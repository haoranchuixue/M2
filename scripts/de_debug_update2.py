"""Debug: Try adding chart view step by step."""
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
}

# Test 1: componentData only (no canvasViewInfo)
print("=== Test 1: componentData with empty canvasViewInfo ===")
p1 = dict(base_payload)
p1["componentData"] = json.dumps([{"id": "comp1", "component": "UserView", "innerType": "table-normal"}])
p1["canvasStyleData"] = "{}"
p1["canvasViewInfo"] = {}
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=p1, timeout=30)
print(f"Status: {r.status_code}, Response: {r.text[:300]}")

# Test 2: canvasViewInfo with minimal chart (just id and type)
print("\n=== Test 2: canvasViewInfo with minimal chart ===")
p2 = dict(base_payload)
p2["componentData"] = "[]"
p2["canvasStyleData"] = "{}"
p2["canvasViewInfo"] = {
    chart_id: {
        "id": chart_id,
        "sceneId": dashboard_id,
        "tableId": dataset_id,
        "title": "DSP Report",
        "type": "table-normal",
        "render": "antv",
    }
}
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=p2, timeout=30)
print(f"Status: {r.status_code}, Response: {r.text[:500]}")

# Test 3: canvasViewInfo with chart but all axis fields as strings
print("\n=== Test 3: canvasViewInfo with full chart ===")
p3 = dict(base_payload)
p3["componentData"] = "[]"
p3["canvasStyleData"] = "{}"
chart = {
    "id": int(chart_id),
    "sceneId": dashboard_id,
    "tableId": dataset_id,
    "title": "DSP Report",
    "type": "table-normal",
    "render": "antv",
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
p3["canvasViewInfo"] = {chart_id: chart}
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=p3, timeout=30)
print(f"Status: {r.status_code}, Response: {r.text[:500]}")

if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}, Msg: {(resp.get('msg') or '')[:200]}")
