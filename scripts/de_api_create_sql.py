"""Create SQL dataset via API - exactly match working dataset format."""
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

sr_ds_id = "1236022373120086016"
dsp_group_id = "1236043392912330752"
old_dataset_id = 1236046190513098752

# Get existing dataset structure
r = requests.post(f'{base}/de2api/datasetTree/details/{old_dataset_id}', headers=headers, json={}, timeout=30)
ds = r.json()['data']

raw_info = ds.get('info')
info_data = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
old_fields = info_data[0]['currentDsFields']

sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

# Create new IDs
ts = str(int(time.time() * 1000))

# Build currentDs as SQL type
new_current_ds = {
    "id": ts,
    "name": None,
    "tableName": None,
    "datasourceId": sr_ds_id,
    "datasetGroupId": None,
    "type": "sql",
    "info": json.dumps({"table": "", "sql": sql_query}),
    "sqlVariableDetails": None,
    "fields": None,
    "lastUpdateTime": 0,
    "status": None,
    "isCross": None
}

# Build fields referencing the new table ID
new_fields = []
for i, f in enumerate(old_fields):
    nf = dict(f)
    nf['id'] = str(int(ts) + i + 1)
    nf['datasetTableId'] = ts
    nf['datasetGroupId'] = None
    new_fields.append(nf)

# Build info structure (as a JSON string)
info_list = [{
    "currentDs": new_current_ds,
    "currentDsField": None,
    "currentDsFields": new_fields,
    "childrenDs": [],
    "unionToParent": {
        "unionType": "left",
        "unionFields": [],
        "parentDs": None,
        "currentDs": None,
        "parentSQLObj": None,
        "currentSQLObj": None
    },
    "allChildCount": 0
}]

# Build union structure
union_list = [{
    "currentDs": new_current_ds,
    "currentDsField": None,
    "currentDsFields": new_fields,
    "childrenDs": [],
    "unionToParent": {
        "unionType": "left",
        "unionFields": [],
        "parentDs": None,
        "currentDs": None,
        "parentSQLObj": None,
        "currentSQLObj": None
    },
    "allChildCount": 0
}]

# Build allFields
all_fields = []
for i, f in enumerate(ds['allFields']):
    nf = dict(f)
    nf['id'] = str(int(ts) + i + 1)
    nf['datasetTableId'] = ts
    nf['datasetGroupId'] = None
    all_fields.append(nf)

# Payload - NOTE: no "id" field (creating a new dataset)
payload = {
    "name": "DSP Report SQL",
    "pid": dsp_group_id,
    "nodeType": "dataset",
    "type": "dataset",
    "info": json.dumps(info_list, ensure_ascii=False),
    "union": json.dumps(union_list, ensure_ascii=False),
    "allFields": all_fields,
    "isCross": False
}

# Debug: print the payload structure
print(f"Payload keys: {list(payload.keys())}")
print(f"Name: {payload['name']}")
print(f"Fields: {len(all_fields)}")
print(f"Info (first 500): {payload['info'][:500]}")

print(f"\n=== Creating SQL dataset ===")
r2 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload, timeout=60)
print(f"Status: {r2.status_code}")

if r2.status_code == 200:
    resp = r2.json()
    print(f"Code: {resp.get('code')}, Msg: {resp.get('msg', '')[:500]}")
    if resp.get('code') == 0:
        new_id = resp.get('data')
        print(f"\n*** SQL Dataset created! ID: {new_id} ***")
elif r2.status_code == 400:
    # Try with Content-Type header set differently
    print("400 error, trying with raw JSON string...")
    # Sometimes Spring fails to parse if there are type mismatches
    # Let's try sending the allFields as part of the info instead
    payload2 = {
        "name": "DSP Report SQL",
        "pid": dsp_group_id,
        "nodeType": "dataset",
        "info": json.dumps(info_list, ensure_ascii=False),
        "union": json.dumps(union_list, ensure_ascii=False),
        "allFields": all_fields,
        "isCross": False
    }
    r3 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload2, timeout=60)
    print(f"Status2: {r3.status_code}")
    if r3.status_code == 200:
        resp3 = r3.json()
        print(f"Code: {resp3.get('code')}, Msg: {resp3.get('msg', '')[:500]}")
    else:
        # Try without type field
        payload3 = dict(payload)
        del payload3['type']
        r4 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload3, timeout=60)
        print(f"Status3 (no type): {r4.status_code}")
        if r4.status_code == 200:
            resp4 = r4.json()
            print(f"Code: {resp4.get('code')}, Msg: {resp4.get('msg', '')[:500]}")
        else:
            # Try with empty allFields (let server discover them)
            payload4 = dict(payload)
            payload4['allFields'] = []
            r5 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload4, timeout=60)
            print(f"Status4 (empty fields): {r5.status_code}")
            if r5.status_code == 200:
                resp5 = r5.json()
                print(f"Code: {resp5.get('code')}, Msg: {resp5.get('msg', '')[:500]}")
else:
    print(f"Error: {r2.text[:500]}")
