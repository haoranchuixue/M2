"""Test with minimal columns to find the minimum viable query."""
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

dashboard_id = 1236050016221663232
dataset_id = 1236046190513098752

r = requests.post(f'{base}/de2api/datasetTree/details/{dataset_id}', headers=headers, json={}, timeout=30)
all_fields = r.json()['data']['allFields']

def make_field(f, summary=None):
    return {
        "id": f['id'], "datasourceId": None, "datasetTableId": None,
        "datasetGroupId": str(dataset_id), "chartId": None,
        "originName": f['originName'], "name": f['name'],
        "dbFieldName": None, "description": None,
        "dataeaseName": f['dataeaseName'], "groupType": f['groupType'],
        "type": f['type'], "precision": None, "scale": None,
        "deType": f['deType'], "deExtractType": f.get('deExtractType', 0),
        "extField": 0, "checked": True, "columnIndex": None,
        "lastSyncTime": None, "dateFormat": None, "dateFormatType": None,
        "fieldShortName": f['fieldShortName'],
        "groupList": None, "otherGroup": None, "desensitized": None,
        "orderChecked": None, "params": None,
        "summary": summary or "count", "sort": "none",
        "dateStyle": "y_M_d", "datePattern": "date_sub", "dateShowFormat": None,
        "chartType": "bar",
        "compareCalc": {"type": "none", "resultData": "percent", "field": None, "custom": None},
        "logic": None, "filterType": None, "index": None,
        "formatterCfg": {"type": "auto", "unitLanguage": "ch", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
        "chartShowName": None, "filter": [], "customSort": None,
        "busiType": None, "hide": False, "field": None, "agg": False
    }

# Get base chart view
r_find = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                      json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
cur_views = r_find.json().get('data', {}).get('canvasViewInfo', {})
chart_id = list(cur_views.keys())[0]
base_chart = cur_views[chart_id]

date_field = next(f for f in all_fields if f['originName'] == 'create_date')
source_field = next(f for f in all_fields if f['originName'] == 'source')
request_field = next(f for f in all_fields if f['originName'] == 'request_count')

# Test 1: table-info with only 2 columns, 1 day, LIMIT 10
print("Test 1: table-info, 2 columns, 1 day, limit 10")
test = json.loads(json.dumps(base_chart))
test['type'] = 'table-info'
test['resultMode'] = 'custom'
test['resultCount'] = 10
test['xAxis'] = [make_field(date_field), make_field(source_field)]
test['yAxis'] = []
test['customFilter'] = {
    "logic": "and",
    "items": [{
        "type": "item", "fieldId": int(date_field['id']),
        "filterType": "logic", "term": "eq",
        "value": "2026-03-29", "filterTypeTime": "dateValue"
    }]
}

r1 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test, timeout=180)
resp1 = r1.json()
print(f"  Code: {resp1.get('code')}")
if resp1.get('code') == 0:
    rows = resp1.get('data', {}).get('tableRow', [])
    print(f"  Rows: {len(rows)}")
    if rows:
        print(f"  First: {json.dumps(rows[0], ensure_ascii=False)[:200]}")
    print("  *** SUCCESS ***")
else:
    print(f"  Error: {resp1.get('msg', '')[:200]}")

# Test 2: table-normal, GROUP BY date, SUM 1 metric only, 1 day
print("\nTest 2: table-normal, 1 dim, 1 metric, 1 day")
test2 = json.loads(json.dumps(base_chart))
test2['type'] = 'table-normal'
test2['resultMode'] = 'custom'
test2['resultCount'] = 100
test2['xAxis'] = [make_field(date_field)]
test2['yAxis'] = [make_field(request_field, "sum")]
test2['customFilter'] = {
    "logic": "and",
    "items": [{
        "type": "item", "fieldId": int(date_field['id']),
        "filterType": "logic", "term": "eq",
        "value": "2026-03-29", "filterTypeTime": "dateValue"
    }]
}

r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test2, timeout=180)
resp2 = r2.json()
print(f"  Code: {resp2.get('code')}")
if resp2.get('code') == 0:
    rows2 = resp2.get('data', {}).get('tableRow', [])
    print(f"  Rows: {len(rows2)}")
    if rows2:
        print(f"  First: {json.dumps(rows2[0], ensure_ascii=False)[:200]}")
    print("  *** SUCCESS ***")
else:
    print(f"  Error: {resp2.get('msg', '')[:200]}")

# Test 3: Try a different table - maybe ads_dsp_cost_metric_daily_dr is smaller
# First check if there's a dataset for it
print("\nTest 3: Check other tables via datasource API")
r3 = requests.post(f'{base}/de2api/datasource/getTablesByDsId', headers=headers,
                   json={"datasourceId": "1236022373120086016"}, timeout=30)
if r3.status_code == 200:
    tables = r3.json().get('data', [])
    print(f"  Tables: {[t.get('name', t) if isinstance(t, dict) else t for t in tables[:10]]}")
else:
    print(f"  Status: {r3.status_code}")
