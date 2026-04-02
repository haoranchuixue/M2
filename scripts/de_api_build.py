"""Create DSP Report dataset and dashboard via DataEase API."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time
import hashlib

base = 'http://47.236.78.123:8100'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base}/', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        inputs = page.query_selector_all('input')
        inputs[0].fill('admin')
        inputs[1].fill('DataEase@123456')
        page.query_selector('button').click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt

token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

sr_ds_id = '1236022373120086016'
dsp_group_id = '1236043392912330752'

def make_de_name(origin_name):
    h = hashlib.md5(origin_name.encode('utf-8')).hexdigest()[:16]
    return f"f_{h}"

# Define fields needed for DSP Report
ts = int(time.time() * 1000)
table_id = str(ts)

# Dimension fields
dim_fields = [
    ("source", "Source", "INT", 2),
    ("create_date", "Date", "DATE", 1),
    ("affiliate_id", "Aff ID", "VARCHAR", 0),
    ("country", "Country", "VARCHAR", 0),
    ("connection_type", "Connect Type", "VARCHAR", 0),
    ("adv_id", "Adv ID", "INT", 2),
    ("adv_type", "Adv Type", "VARCHAR", 0),
    ("p_cvr_version", "PCvr Version", "VARCHAR", 0),
    ("p_ctr_version", "PCtr Version", "VARCHAR", 0),
    ("tag_id", "Tag ID", "VARCHAR", 0),
    ("tag_name", "Tag Name", "VARCHAR", 0),
    ("audience", "Audience", "VARCHAR", 0),
]

# Metric fields (to be summed)
metric_fields = [
    ("request_count", "Request", "BIGINT", 2),
    ("request_filter_count", "Request Filter", "BIGINT", 2),
    ("response_count", "Response", "BIGINT", 2),
    ("win_count", "Wins", "BIGINT", 2),
    ("bid_price_total", "Bid Price Total", "DECIMAL", 2),
    ("imp_count", "Impressions", "BIGINT", 2),
    ("clean_imp_count", "Clean Impressions", "BIGINT", 2),
    ("cheat_imp_count", "Cheat Impressions", "BIGINT", 2),
    ("exceed_imp_count", "Exceed Impressions", "BIGINT", 2),
    ("click_count", "Click", "BIGINT", 2),
    ("clean_click_count", "Clean Clicks", "BIGINT", 2),
    ("cheat_click_count", "Cheat Clicks", "BIGINT", 2),
    ("price_total", "Price Total", "DECIMAL", 2),
]

def make_field(origin_name, display_name, field_type, de_type, group_type, idx):
    de_name = make_de_name(origin_name)
    return {
        "id": str(ts + idx),
        "datasourceId": sr_ds_id,
        "datasetTableId": table_id,
        "datasetGroupId": None,
        "chartId": None,
        "originName": origin_name,
        "name": display_name,
        "dbFieldName": None,
        "description": None,
        "dataeaseName": de_name,
        "groupType": group_type,
        "type": field_type,
        "precision": None,
        "scale": None,
        "deType": de_type,
        "deExtractType": de_type,
        "extField": 0,
        "checked": True,
        "columnIndex": None,
        "lastSyncTime": None,
        "dateFormat": None,
        "dateFormatType": None,
        "fieldShortName": de_name,
        "desensitized": None
    }

# Build all fields
all_fields = []
idx = 1
for origin, display, ftype, dtype in dim_fields:
    all_fields.append(make_field(origin, display, ftype, dtype, "d", idx))
    idx += 1
for origin, display, ftype, dtype in metric_fields:
    all_fields.append(make_field(origin, display, ftype, dtype, "q", idx))
    idx += 1

# Build the dataset save payload
current_ds = {
    "id": table_id,
    "name": None,
    "tableName": "dsp_report",
    "datasourceId": sr_ds_id,
    "datasetGroupId": None,
    "type": "db",
    "info": json.dumps({"table": "dsp_report", "sql": ""}),
    "sqlVariableDetails": None,
    "fields": None,
    "lastUpdateTime": 0,
    "status": None,
    "isCross": None
}

union_entry = {
    "currentDs": current_ds,
    "currentDsField": None,
    "currentDsFields": all_fields,
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

dataset_payload = {
    "name": "DSP Report Data",
    "pid": dsp_group_id,
    "nodeType": "dataset",
    "type": None,
    "mode": 0,
    "info": json.dumps([union_entry]),
    "union": [union_entry],
    "allFields": all_fields,
    "isCross": False
}

# Save the dataset
print("=== Saving dataset ===")
result = api('/datasetTree/save', dataset_payload)
print(f"Code: {result.get('code')}")
msg = result.get('msg') or ''
print(f"Msg: {msg[:500]}")
if result.get('data'):
    data = result['data']
    if isinstance(data, dict):
        print(f"Dataset ID: {data.get('id')}")
        # Save full response
        with open('d:/Projects/m2/scripts/dataset_save_result.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Full result saved to dataset_save_result.json")
    else:
        print(f"Data: {str(data)[:500]}")
