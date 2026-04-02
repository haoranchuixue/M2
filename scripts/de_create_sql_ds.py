"""Create SQL-type dataset with date filter in DataEase, properly structured."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time

base = 'http://47.236.78.123:8100'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
        page.wait_for_load_state('networkidle', timeout=30000)
        page.wait_for_selector('input', timeout=10000)
        inputs = page.query_selector_all('input')
        inputs[0].fill('admin')
        inputs[1].fill('DataEase@123456')
        page.query_selector('button').click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt

token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

sr_ds_id = 1236022373120086016
dsp_group_id = 1236043392912330752
old_dataset_id = 1236046190513098752

# Step 1: Get existing dataset structure as reference
print("=== Getting existing dataset structure ===")
r = requests.post(f'{base}/de2api/datasetTree/details/{old_dataset_id}', headers=headers, json={}, timeout=30)
old_ds = r.json()['data']
print(f"Old dataset name: {old_ds['name']}")
print(f"Old dataset type: {old_ds.get('type')}")

raw_info = old_ds.get('info', '[]')
old_info = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
raw_union = old_ds.get('union', '[]')
old_union = json.loads(raw_union) if isinstance(raw_union, str) else raw_union
old_fields = old_ds.get('allFields', [])

print(f"Old info structure: {json.dumps(old_info, indent=2, ensure_ascii=False)[:500]}")
print(f"Old union structure: {json.dumps(old_union, indent=2, ensure_ascii=False)[:500]}")
print(f"Old fields count: {len(old_fields)}")

# Step 2: Build SQL dataset using the exact same structure as the old one, but with type=sql
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"

ts_id = str(int(time.time() * 1000))

# Clone the old info/union structure exactly, just change type and sql
old_current_ds = old_info[0]['currentDs']
old_current_fields = old_info[0]['currentDsFields']

# Create new currentDs based on old one
new_current_ds = dict(old_current_ds)
new_current_ds['id'] = ts_id
new_current_ds['type'] = 'sql'
new_current_ds['info'] = json.dumps({"table": "", "sql": sql_query})

# Update field IDs to reference the new table ID
new_fields = []
for i, f in enumerate(old_current_fields):
    nf = dict(f)
    nf['id'] = str(int(ts_id) + i + 1)
    nf['datasetTableId'] = ts_id
    new_fields.append(nf)

info_data = [{
    "currentDs": new_current_ds,
    "currentDsField": None,
    "currentDsFields": new_fields,
    "childDs": None,
    "unionType": None,
    "unionFields": None
}]

union_data = [{
    "currentDs": new_current_ds,
    "currentDsField": None,
    "currentDsFields": new_fields,
    "childDs": None,
    "unionType": None,
    "unionFields": None
}]

# allFields also need updated IDs
all_new_fields = []
for i, f in enumerate(old_fields):
    nf = dict(f)
    nf['id'] = str(int(ts_id) + i + 1)
    nf['datasetTableId'] = ts_id
    all_new_fields.append(nf)

dataset_payload = {
    "name": "DSP Report (Filtered)",
    "pid": dsp_group_id,
    "nodeType": "dataset",
    "type": "dataset",
    "info": json.dumps(info_data, ensure_ascii=False),
    "union": json.dumps(union_data, ensure_ascii=False),
    "allFields": all_new_fields,
    "isCross": False
}

print(f"\n=== Creating SQL-filtered dataset ===")
print(f"Fields: {len(all_new_fields)}")
print(f"SQL: {sql_query}")
print(f"currentDs type: {new_current_ds['type']}")
print(f"currentDs info: {new_current_ds['info']}")

r2 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=dataset_payload, timeout=60)
print(f"Status: {r2.status_code}")
resp = r2.json()
code = resp.get('code')
msg = resp.get('msg', '')
print(f"Code: {code}, Msg: {msg[:500]}")

if code == 0:
    new_ds_id = resp.get('data')
    print(f"\n*** SQL Dataset created! ID: {new_ds_id} ***")
    
    time.sleep(3)
    r3 = requests.post(f'{base}/de2api/datasetTree/details/{new_ds_id}', headers=headers, json={}, timeout=30)
    if r3.json().get('code') == 0:
        ds_data = r3.json()['data']
        fields = ds_data.get('allFields', [])
        print(f"Dataset fields ({len(fields)}):")
        for f in fields:
            print(f"  {f['originName']:30s} {f.get('type', 'N/A'):10s} group={f.get('groupType', 'N/A')}")
    else:
        print(f"Error getting details: {r3.json().get('msg', '')[:200]}")
else:
    print(f"\nFull error response:")
    print(json.dumps(resp, indent=2, ensure_ascii=False)[:1000])
