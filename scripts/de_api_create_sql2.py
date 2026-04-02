"""Create SQL dataset - fix: union should be list (not JSON string), pid should be number."""
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
dsp_group_id = 1236043392912330752
old_dataset_id = 1236046190513098752

r = requests.post(f'{base}/de2api/datasetTree/details/{old_dataset_id}', headers=headers, json={}, timeout=30)
ds = r.json()['data']

raw_info = ds.get('info')
info_data = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
old_fields = info_data[0]['currentDsFields']

sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

ts = str(int(time.time() * 1000))

new_current_ds = {
    "id": ts,
    "name": None,
    "tableName": None,
    "datasourceId": sr_ds_id,
    "datasetGroupId": None,
    "type": "sql",
    "info": json.dumps({"table":"","sql":sql_query}, separators=(',',':')),
    "sqlVariableDetails": None,
    "fields": None,
    "lastUpdateTime": 0,
    "status": None,
    "isCross": None
}

new_fields = []
for i, f in enumerate(old_fields):
    nf = dict(f)
    nf['id'] = str(int(ts) + i + 1)
    nf['datasetTableId'] = ts
    nf['datasetGroupId'] = None
    new_fields.append(nf)

union_item = {
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
}

all_fields = []
for i, f in enumerate(ds['allFields']):
    nf = dict(f)
    nf['id'] = str(int(ts) + i + 1)
    nf['datasetTableId'] = ts
    nf['datasetGroupId'] = None
    all_fields.append(nf)

# KEY FIX: union is native list, pid is number, info is compact JSON string
payload = {
    "name": "DSP Report SQL",
    "pid": dsp_group_id,
    "nodeType": "dataset",
    "info": json.dumps([union_item], separators=(',', ':'), ensure_ascii=False),
    "union": [union_item],
    "allFields": all_fields,
    "isCross": False
}

print(f"=== Creating SQL dataset (fixed format) ===")
print(f"pid type: {type(payload['pid'])}, value: {payload['pid']}")
print(f"union type: {type(payload['union'])}")
print(f"info type: {type(payload['info'])}")
print(f"Fields: {len(all_fields)}")

r2 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload, timeout=60)
print(f"Status: {r2.status_code}")

if r2.status_code == 200:
    resp = r2.json()
    code = resp.get('code')
    msg = resp.get('msg', '')
    print(f"Code: {code}, Msg: {msg[:500]}")
    if code == 0:
        new_id = resp.get('data')
        print(f"\n*** SQL Dataset created! ID: {new_id} ***")
        
        time.sleep(3)
        r3 = requests.post(f'{base}/de2api/datasetTree/details/{new_id}', headers=headers, json={}, timeout=30)
        if r3.json().get('code') == 0:
            ds3 = r3.json()['data']
            fields = ds3.get('allFields', [])
            print(f"Fields: {len(fields)}")
            for f in fields[:3]:
                print(f"  {f['originName']}: {f['type']}")
else:
    print(f"Error: {r2.text[:500]}")
    
    # Try with mode field
    print("\n\nRetrying with mode=0...")
    payload['mode'] = 0
    r3 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload, timeout=60)
    print(f"Status: {r3.status_code}")
    if r3.status_code == 200:
        resp3 = r3.json()
        print(f"Code: {resp3.get('code')}, Msg: {resp3.get('msg', '')[:500]}")
    else:
        print(f"Error: {r3.text[:300]}")
        
        # Try with type field
        print("\n\nRetrying with type field...")
        payload['type'] = None
        r4 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload, timeout=60)
        print(f"Status: {r4.status_code}")
        if r4.status_code == 200:
            resp4 = r4.json()
            print(f"Code: {resp4.get('code')}, Msg: {resp4.get('msg', '')[:500]}")
