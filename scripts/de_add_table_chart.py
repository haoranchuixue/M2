"""Add table chart to DSP Report dashboard."""
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
ds_data = r.json()['data']
all_fields = ds_data['allFields']

# Build chart field configs
dim_fields = [f for f in all_fields if f['groupType'] == 'd']
metric_fields = [f for f in all_fields if f['groupType'] == 'q']

def make_axis_field(f, summary=None):
    field = {
        "id": f['id'],
        "datasetGroupId": str(dataset_id),
        "originName": f['originName'],
        "name": f['name'],
        "dataeaseName": f['dataeaseName'],
        "groupType": f['groupType'],
        "type": f['type'],
        "deType": f['deType'],
        "deExtractType": f.get('deExtractType', 0),
        "extField": 0,
        "checked": True,
        "fieldShortName": f['fieldShortName'],
        "sort": "none",
    }
    if f['deType'] == 1:
        field["dateStyle"] = "y_M_d"
        field["datePattern"] = "date_sub"
    if summary:
        field["summary"] = summary
    return field

# Build X axis: create_date as default dimension
x_axis = [make_axis_field(f) for f in dim_fields if f['originName'] == 'create_date']

# Build Y axis: all metrics with SUM aggregation
y_axis = [make_axis_field(f, "sum") for f in metric_fields]

chart_id = str(int(time.time() * 1000))

chart_view = {
    "id": chart_id,
    "sceneId": dashboard_id,
    "tableId": dataset_id,
    "title": "DSP Report",
    "type": "table-normal",
    "render": "antv",
    "resultCount": 1000,
    "resultMode": "all",
    "refreshViewEnable": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
    "isPlugin": False,
    "dataFrom": "dataset",
    "xAxis": json.dumps(x_axis),
    "xAxisExt": "[]",
    "yAxis": json.dumps(y_axis),
    "yAxisExt": "[]",
    "extStack": "[]",
    "extBubble": "[]",
    "extColor": "[]",
    "customAttr": json.dumps({
        "basicStyle": {"tableBorderColor": "#E6E7E4", "tableScrollBarColor": "rgba(0,0,0,0.15)", "alpha": 100},
        "tableHeader": {"tableHeaderBgColor": "#F5F6F7", "tableHeaderFontColor": "#333333", "tableTitleFontSize": 12},
        "tableCell": {"tableFontColor": "#333333", "tableItemBgColor": "#ffffff", "tableFontSize": 12},
        "misc": {"nameFontColor": "#333333"}
    }),
    "customStyle": json.dumps({
        "text": {"show": True, "fontSize": 16, "color": "#333333", "hPosition": "left", "isItalic": False, "isBolder": True},
        "background": {"color": "#ffffff", "alpha": 100, "borderRadius": 5}
    }),
    "customFilter": "[]",
    "drillFields": "[]",
    "senior": "{}",
    "flowMapStartName": "[]",
    "flowMapEndName": "[]"
}

component = {
    "id": f"component_{chart_id}",
    "component": "UserView",
    "name": "view",
    "label": "DSP Report",
    "propValue": {"innerType": "table-normal"},
    "icon": "",
    "style": {"width": 1880, "height": 700, "top": 50, "left": 20},
    "x": 1, "y": 1, "sizeX": 36, "sizeY": 14,
    "canvasId": "canvas_main",
    "innerType": "table-normal"
}

update_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": json.dumps([component]),
    "canvasStyleData": json.dumps({
        "width": 1920, "height": 1080, "selfAdaption": True,
        "auxiliaryMatrix": True, "openCommonStyle": True,
        "panel": {"themeColor": "light", "color": "#f5f6f7", "imageUrl": "", "borderRadius": 0},
        "dashboard": {}
    }),
    "canvasViewInfo": {chart_id: chart_view},
    "checkVersion": "1",
    "version": 3,
    "contentId": "0",
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0,
}

print("=== Updating dashboard with chart ===")
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', 
                  headers=headers, json=update_payload, timeout=60)
print(f"Status: {r.status_code}")
resp = r.json()
print(f"Code: {resp.get('code')}")
msg = resp.get('msg') or ''
print(f"Msg: {msg[:500]}")

if resp.get('code') == 0:
    print("\n*** Dashboard updated successfully! ***")
    
    # Now publish it
    print("\n=== Publishing dashboard ===")
    pub_payload = {
        "id": dashboard_id,
        "type": "dashboard",
        "busiFlag": "dashboard",
        "status": 1,
        "pid": 0,
    }
    r2 = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                       headers=headers, json=pub_payload, timeout=30)
    print(f"Publish status: {r2.status_code}")
    print(f"Publish response: {r2.text[:500]}")
    
    print(f"\n*** Dashboard URL: {base}/#/panel/index?dvId={dashboard_id} ***")
else:
    # Save the error
    with open('d:/Projects/m2/scripts/update_error.json', 'w', encoding='utf-8') as f:
        json.dump(resp, f, indent=2, ensure_ascii=False)
    print("Error saved to update_error.json")
