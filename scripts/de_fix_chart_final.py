"""Fix chart: use aggregation + date filter to stay within CPU limit."""
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

# Get dataset fields
r = requests.post(f'{base}/de2api/datasetTree/details/{dataset_id}', headers=headers, json={}, timeout=30)
all_fields = r.json()['data']['allFields']

dim_fields = [f for f in all_fields if f['groupType'] == 'd']
metric_fields = [f for f in all_fields if f['groupType'] == 'q']

print(f"Dimensions: {len(dim_fields)}, Metrics: {len(metric_fields)}")

def make_field(f, summary=None):
    return {
        "id": f['id'],
        "datasourceId": None, "datasetTableId": None,
        "datasetGroupId": str(dataset_id),
        "chartId": None,
        "originName": f['originName'],
        "name": f['name'],
        "dbFieldName": None, "description": None,
        "dataeaseName": f['dataeaseName'],
        "groupType": f['groupType'],
        "type": f['type'],
        "precision": None, "scale": None,
        "deType": f['deType'],
        "deExtractType": f.get('deExtractType', 0),
        "extField": 0, "checked": True,
        "columnIndex": None, "lastSyncTime": None,
        "dateFormat": None, "dateFormatType": None,
        "fieldShortName": f['fieldShortName'],
        "groupList": None, "otherGroup": None,
        "desensitized": None, "orderChecked": None, "params": None,
        "summary": summary or "count",
        "sort": "none",
        "dateStyle": "y_M_d", "datePattern": "date_sub", "dateShowFormat": None,
        "chartType": "bar",
        "compareCalc": {"type": "none", "resultData": "percent", "field": None, "custom": None},
        "logic": None, "filterType": None, "index": None,
        "formatterCfg": {"type": "auto", "unitLanguage": "ch", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
        "chartShowName": None, "filter": [], "customSort": None,
        "busiType": None, "hide": False, "field": None, "agg": False
    }

# xAxis: just create_date as dimension (for GROUP BY)
date_field = next(f for f in dim_fields if f['originName'] == 'create_date')
source_field = next(f for f in dim_fields if f['originName'] == 'source')
x_axis = [make_field(date_field), make_field(source_field)]

# yAxis: all metric fields with SUM aggregation
y_axis = [make_field(f, "sum") for f in metric_fields]

print(f"xAxis: {len(x_axis)} dim fields")
print(f"yAxis: {len(y_axis)} metric fields")

# Build customFilter with date >= 3 days ago
custom_filter = {
    "logic": "and",
    "items": [
        {
            "type": "item",
            "fieldId": int(date_field['id']),
            "filterType": "logic",
            "term": "ge",
            "value": "2026-03-27",
            "filterTypeTime": "dateValue"
        }
    ]
}

# First, test getData with this configuration
print("\n=== Testing getData ===")

# Get current chart view
r_find = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                      json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
cur_data = r_find.json().get('data', {})
cur_views = cur_data.get('canvasViewInfo', {})
chart_id = list(cur_views.keys())[0]
chart_view = cur_views[chart_id]

# Update chart view for testing
chart_view['type'] = 'table-normal'
chart_view['resultMode'] = 'custom'
chart_view['resultCount'] = 1000
chart_view['xAxis'] = x_axis
chart_view['yAxis'] = y_axis
chart_view['customFilter'] = custom_filter

r_test = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=180)
resp = r_test.json()
print(f"Code: {resp.get('code')}")

if resp.get('code') == 0:
    data = resp.get('data', {})
    rows = data.get('tableRow', [])
    print(f"Rows: {len(rows)}")
    if rows:
        print(f"First row: {json.dumps(rows[0], ensure_ascii=False)[:300]}")
    print("*** getData SUCCESS! ***")
    
    # Now update the dashboard with this working configuration
    print("\n=== Updating dashboard ===")
    cur_version = cur_data.get('version', 5)
    
    comps = json.loads(cur_data.get('componentData', '[]'))
    for comp in comps:
        if str(comp.get('id')) == str(chart_id):
            comp['innerType'] = 'table-normal'
            comp['propValue'] = {'innerType': 'table-normal'}
    
    update_payload = {
        "id": dashboard_id,
        "name": "DSP Report",
        "pid": 0,
        "type": "dashboard",
        "busiFlag": "dashboard",
        "componentData": json.dumps(comps, separators=(',', ':'), ensure_ascii=False),
        "canvasStyleData": cur_data.get('canvasStyleData', '{}'),
        "canvasViewInfo": {chart_id: chart_view},
        "checkVersion": str(cur_version),
        "version": cur_version + 1,
        "contentId": cur_data.get('contentId', '0'),
        "status": 0,
        "mobileLayout": False,
        "selfWatermarkStatus": False,
        "extFlag": 0,
    }
    
    r_upd = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                          headers=headers, json=update_payload, timeout=60)
    upd_resp = r_upd.json()
    print(f"Update code: {upd_resp.get('code')}")
    
    if upd_resp.get('code') == 0:
        # Publish
        pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                           headers=headers,
                           json={"id": dashboard_id, "type": "dashboard",
                                 "busiFlag": "dashboard", "status": 1, "pid": 0},
                           timeout=30)
        print(f"Publish: {pub.json().get('code')}")
        print(f"\nDashboard ready at: {base}/#/panel/index?dvId={dashboard_id}")
    else:
        print(f"Update error: {upd_resp.get('msg', '')[:300]}")
else:
    print(f"Error: {resp.get('msg', '')[:300]}")
    
    # Try narrower date range
    print("\n\nRetrying with 1-day filter (2026-03-29)...")
    chart_view['customFilter']['items'][0]['value'] = "2026-03-29"
    chart_view['customFilter']['items'][0]['term'] = "eq"
    
    r_test2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=180)
    resp2 = r_test2.json()
    print(f"Code: {resp2.get('code')}")
    if resp2.get('code') == 0:
        rows2 = resp2.get('data', {}).get('tableRow', [])
        print(f"Rows: {len(rows2)}")
        if rows2:
            print(f"First: {json.dumps(rows2[0], ensure_ascii=False)[:300]}")
        print("*** 1-day SUCCESS! ***")
    else:
        print(f"Error: {resp2.get('msg', '')[:300]}")
