"""Update DSP Report dashboard with table chart via API."""
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

def api_post(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r

dashboard_id = '1236050016221663232'
dataset_id = '1236046190513098752'

# Get dataset fields
ds_detail = api_post('/datasetTree/details/' + dataset_id, {}).json()
all_fields = ds_detail['data']['allFields']

# Build dimensions and metrics for chart view
dim_fields = [f for f in all_fields if f['groupType'] == 'd']
metric_fields = [f for f in all_fields if f['groupType'] == 'q']

# X axis: create_date only by default
x_axis = []
for f in dim_fields:
    if f['originName'] == 'create_date':
        x_axis.append({
            "id": f['id'],
            "datasetGroupId": dataset_id,
            "originName": f['originName'],
            "name": f['name'],
            "dataeaseName": f['dataeaseName'],
            "groupType": "d",
            "type": f['type'],
            "deType": f['deType'],
            "deExtractType": f.get('deExtractType', 0),
            "extField": 0,
            "checked": True,
            "fieldShortName": f['fieldShortName'],
            "sort": "none",
            "dateStyle": "y_M_d",
            "datePattern": "date_sub"
        })

y_axis = []
for f in metric_fields:
    y_axis.append({
        "id": f['id'],
        "datasetGroupId": dataset_id,
        "originName": f['originName'],
        "name": f['name'],
        "dataeaseName": f['dataeaseName'],
        "groupType": "q",
        "type": f['type'],
        "deType": f['deType'],
        "deExtractType": f.get('deExtractType', 0),
        "extField": 0,
        "checked": True,
        "fieldShortName": f['fieldShortName'],
        "sort": "none",
        "summary": "sum",
        "formatterCfg": {"type": "auto", "thousandSeparator": True}
    })

chart_id = str(int(time.time() * 1000))

# Chart view DTO
chart_view = {
    "id": chart_id,
    "sceneId": int(dashboard_id),
    "tableId": int(dataset_id),
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

# Component data
component = {
    "id": f"component_{chart_id}",
    "component": "UserView",
    "name": "view",
    "label": "DSP Report",
    "propValue": {"innerType": "table-normal"},
    "icon": "",
    "style": {
        "width": 1880,
        "height": 700,
        "top": 50,
        "left": 20
    },
    "x": 1,
    "y": 1,
    "sizeX": 36,
    "sizeY": 14,
    "canvasId": "canvas_main",
    "innerType": "table-normal"
}

# Update payload
update_payload = {
    "id": int(dashboard_id),
    "name": "DSP Report",
    "type": "dashboard",
    "pid": 0,
    "componentData": json.dumps([component]),
    "canvasStyleData": json.dumps({
        "width": 1920,
        "height": 1080,
        "selfAdaption": True,
        "auxiliaryMatrix": True,
        "openCommonStyle": True,
        "panel": {"themeColor": "light", "color": "#f5f6f7", "imageUrl": "", "borderRadius": 0},
        "dashboard": {}
    }),
    "canvasViewInfo": {chart_id: chart_view},
    "busiFlag": "dashboard",
    "checkVersion": "1",
    "contentId": "0",
    "resourceTable": "snapshot"
}

print("=== Updating dashboard ===")
r = api_post('/dataVisualization/updateCanvas', update_payload)
print(f"HTTP Status: {r.status_code}")
print(f"Response: {r.text[:2000]}")

if r.status_code != 200:
    # Try with different structure
    print("\n=== Trying alternative payload ===")
    # Maybe canvasViewInfo needs string values
    update_payload2 = dict(update_payload)
    update_payload2['canvasViewInfo'] = json.dumps({chart_id: chart_view})
    r2 = api_post('/dataVisualization/updateCanvas', update_payload2)
    print(f"HTTP Status: {r2.status_code}")
    print(f"Response: {r2.text[:2000]}")
