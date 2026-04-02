"""Fix chart: reduce result count and use pagination to avoid CPU limit."""
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

# Get current dashboard
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
cur_data = r.json().get('data', {})
cur_version = cur_data.get('version', 4)
cur_views = cur_data.get('canvasViewInfo', {})
cur_comp = cur_data.get('componentData', '[]')
cur_style = cur_data.get('canvasStyleData', '{}')

print(f"Version: {cur_version}, Views: {len(cur_views)}")

# Fix chart view: use table-info instead of table-normal for detail view
# table-info is detail table (明细表) which doesn't aggregate
# Also reduce resultCount and use proper pagination
for vid, vdata in cur_views.items():
    print(f"\nFixing chart {vid}...")
    
    # Change to table-info (detail table, no aggregation needed)
    vdata['type'] = 'table-info'
    vdata['resultMode'] = 'custom'
    vdata['resultCount'] = 100
    
    # Remove summary from all fields in xAxis (no aggregation for detail table)
    for field in vdata.get('xAxis', []):
        if 'summary' in field:
            del field['summary']
    
    # Update component innerType too
    comps = json.loads(cur_comp)
    for comp in comps:
        if str(comp.get('id')) == str(vid):
            comp['innerType'] = 'table-info'
            comp['propValue'] = {'innerType': 'table-info'}
    cur_comp = json.dumps(comps, separators=(',', ':'), ensure_ascii=False)

update_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": cur_comp,
    "canvasStyleData": cur_style,
    "canvasViewInfo": cur_views,
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": cur_data.get('contentId', '0'),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0,
}

print(f"\n=== Updating chart to table-info with resultCount=100 ===")
r2 = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                   headers=headers, json=update_payload, timeout=60)
print(f"HTTP Status: {r2.status_code}, Code: {r2.json().get('code')}")

if r2.json().get('code') == 0:
    # Publish
    pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                       headers=headers,
                       json={"id": dashboard_id, "type": "dashboard",
                             "busiFlag": "dashboard", "status": 1, "pid": 0},
                       timeout=30)
    print(f"Publish: {pub.json().get('code')}")
    
    # Test getData
    verify = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                          json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
    v_views = verify.json().get('data', {}).get('canvasViewInfo', {})
    
    for vid, vdata in v_views.items():
        print(f"\nTesting getData for chart {vid}...")
        r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=vdata, timeout=120)
        resp = r3.json()
        print(f"  Code: {resp.get('code')}")
        if resp.get('code') == 0:
            data_info = resp.get('data', {})
            if isinstance(data_info, dict):
                print(f"  Data keys: {list(data_info.keys())}")
                fields = data_info.get('fields', [])
                table_data = data_info.get('tableRow', data_info.get('data', []))
                print(f"  Fields: {len(fields)}")
                if isinstance(table_data, list):
                    print(f"  Rows: {len(table_data)}")
                    if table_data:
                        print(f"  First row: {json.dumps(table_data[0], ensure_ascii=False)[:300]}")
        else:
            print(f"  Error: {resp.get('msg', '')[:300]}")
    
    print(f"\nDashboard: {base}/#/panel/index?dvId={dashboard_id}")
