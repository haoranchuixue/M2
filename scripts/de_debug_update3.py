"""Binary search for which field causes the 400 error."""
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
chart_id = str(int(time.time() * 1000))

base_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "checkVersion": "1",
    "version": 3,
    "contentId": "0",
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0,
    "componentData": "[]",
    "canvasStyleData": "{}",
}

# Working minimal chart
working_chart = {
    "id": chart_id,
    "sceneId": dashboard_id,
    "tableId": dataset_id,
    "title": "DSP Report",
    "type": "table-normal",
    "render": "antv",
}

# Fields to add one by one
extra_fields = {
    "resultCount": 1000,
    "resultMode": "all",
    "xAxis": "[]",
    "yAxis": "[]",
    "xAxisExt": "[]",
    "yAxisExt": "[]",
    "extStack": "[]",
    "extBubble": "[]",
    "extColor": "[]",
    "customAttr": "{}",
    "customStyle": "{}",
    "customFilter": "[]",
    "drillFields": "[]",
    "senior": "{}",
    "flowMapStartName": "[]",
    "flowMapEndName": "[]",
    "isPlugin": False,
    "dataFrom": "dataset",
    "refreshViewEnable": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
}

# Add fields one at a time to find the culprit
chart = dict(working_chart)
for key, val in extra_fields.items():
    chart[key] = val
    payload = dict(base_payload)
    payload["canvasViewInfo"] = {chart_id: chart}
    
    r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                      headers=headers, json=payload, timeout=15)
    status = "OK" if r.status_code == 200 else "FAIL"
    print(f"  + {key}={repr(val)[:30]}: {r.status_code} ({status})")
    
    if r.status_code != 200:
        # Remove the last added field
        del chart[key]
        print(f"    --> Removing '{key}' and continuing...")

# Final test with all non-problematic fields
payload = dict(base_payload)
payload["canvasViewInfo"] = {chart_id: chart}
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                  headers=headers, json=payload, timeout=15)
print(f"\nFinal: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    print(f"\nWorking chart keys: {list(chart.keys())}")
