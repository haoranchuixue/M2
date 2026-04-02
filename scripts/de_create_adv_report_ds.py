"""Create dataset from ads_dsp_adv_index_report (pre-aggregated, smaller table)."""
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
table_name = "ads_dsp_adv_index_report"

# Get field definitions from the table
r_fields = requests.post(f'{base}/de2api/datasource/getTableField',
                         headers=headers,
                         json={"datasourceId": sr_ds_id, "tableName": table_name},
                         timeout=30)
raw_fields = r_fields.json()['data']
print(f"Table {table_name} has {len(raw_fields)} fields")

# Build the dataset using the same structure as the existing dsp_report dataset
ts = str(int(time.time() * 1000))

# Map fields
dim_types = {'DATE', 'VARCHAR', 'INT'}
metric_types = {'BIGINT', 'DECIMAL', 'DOUBLE', 'FLOAT', 'INT'}

fields = []
for i, rf in enumerate(raw_fields):
    origin = rf['originName']
    name = rf.get('name', '') or origin
    ftype = rf['type']
    
    # Determine groupType
    if origin in ('report_date', 'report_hour', 'affiliate_id', 'affiliate_name',
                  'ad_format', 'bundle_id', 'country', 'publisher_id',
                  'adv_type', 'adv_id', 'adv_name', 'first_ssp',
                  'response_type', 'traffic_type', 'domain'):
        group_type = 'd'
    else:
        group_type = 'q'
    
    de_type = rf.get('deType', 0)
    de_extract = rf.get('deExtractType', 0)
    
    field = {
        "id": str(int(ts) + i + 1),
        "datasourceId": sr_ds_id,
        "datasetTableId": ts,
        "datasetGroupId": None,
        "chartId": None,
        "originName": origin,
        "name": name if name else origin,
        "dbFieldName": None,
        "description": None,
        "dataeaseName": rf.get('dataeaseName', f'f_{i}'),
        "groupType": group_type,
        "type": ftype,
        "precision": None, "scale": None,
        "deType": de_type,
        "deExtractType": de_extract,
        "extField": 0,
        "checked": True,
        "columnIndex": i,
        "lastSyncTime": None,
        "dateFormat": None, "dateFormatType": None,
        "fieldShortName": rf.get('fieldShortName', f'f_{i}'),
        "groupList": None, "otherGroup": None,
        "desensitized": None, "orderChecked": None, "params": None
    }
    fields.append(field)

current_ds = {
    "id": ts,
    "name": None,
    "tableName": table_name,
    "datasourceId": sr_ds_id,
    "datasetGroupId": None,
    "type": "db",
    "info": json.dumps({"table": table_name, "sql": ""}),
    "sqlVariableDetails": None,
    "fields": None,
    "lastUpdateTime": 0,
    "status": None,
    "isCross": None
}

union_item = {
    "currentDs": current_ds,
    "currentDsField": None,
    "currentDsFields": fields,
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

payload = {
    "name": "DSP Adv Index Report",
    "pid": dsp_group_id,
    "nodeType": "dataset",
    "info": json.dumps([union_item], ensure_ascii=False),
    "union": [union_item],
    "allFields": fields,
    "isCross": False
}

print(f"\n=== Creating dataset from {table_name} ===")
r = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=payload, timeout=60)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    resp = r.json()
    print(f"Full response: {json.dumps(resp, ensure_ascii=False)[:2000]}")
    code = resp.get('code')
    msg = resp.get('msg') or ''
    print(f"Code: {code}, Msg: {str(msg)[:500]}")
    
    if code == 0:
        new_ds_id = resp.get('data')
        if isinstance(new_ds_id, dict):
            new_ds_id = new_ds_id.get('id')
        print(f"\n*** Dataset created! ID: {new_ds_id} ***")
        
        time.sleep(3)
        r2 = requests.post(f'{base}/de2api/datasetTree/details/{new_ds_id}', headers=headers, json={}, timeout=30)
        if r2.json().get('code') == 0:
            ds = r2.json()['data']
            ds_fields = ds.get('allFields', [])
            print(f"Dataset fields: {len(ds_fields)}")
            for f in ds_fields:
                print(f"  {f['originName']:30s} {f.get('type', 'N/A'):10s} group={f.get('groupType', '?')}")
else:
    print(f"Error: {r.text[:500]}")
