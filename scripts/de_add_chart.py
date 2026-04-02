"""Add table chart to DSP Report dashboard via DataEase API."""
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

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

dashboard_id = '1236050016221663232'
dataset_id = '1236046190513098752'

# Get the dataset fields to reference in the chart
print("=== Getting dataset details ===")
ds_detail = api('/datasetTree/details/' + dataset_id, {})
ds_data = ds_detail.get('data', {})
all_fields = ds_data.get('allFields', [])
print(f"Total fields: {len(all_fields)}")
for f in all_fields:
    print(f"  {f['originName']} ({f['name']}): groupType={f['groupType']}, deType={f['deType']}, id={f['id']}")

# Build chart view configuration
# The table chart in DataEase uses chart type "table-info" or "table-normal" or "summary-table"
# For a summary table with aggregation, use "table-normal"

ts = int(time.time() * 1000)
chart_id = str(ts)

# Map fields to chart dimensions and metrics
dim_fields = [f for f in all_fields if f['groupType'] == 'd']
metric_fields = [f for f in all_fields if f['groupType'] == 'q']

# For the chart, dimensions are "xAxis" fields and metrics are "yAxis" fields
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
    summary_type = "sum"
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
        "summary": summary_type,
        "formatterCfg": {"type": "auto", "thousandSeparator": True}
    })

# Build chart view
chart_view = {
    "id": chart_id,
    "sceneId": dashboard_id,
    "tableId": dataset_id,
    "title": "DSP Report Table",
    "type": "table-normal",
    "render": "antv",
    "resultCount": 1000,
    "resultMode": "all",
    "xAxis": json.dumps(x_axis),
    "xAxisExt": "[]",
    "yAxis": json.dumps(y_axis),
    "yAxisExt": "[]",
    "extStack": "[]",
    "extBubble": "[]",
    "customAttr": json.dumps({
        "basicStyle": {"tableBorderColor": "#E6E7E4", "tableScrollBarColor": "rgba(0,0,0,0.15)"},
        "tableHeader": {"tableHeaderBgColor": "#F5F6F7", "tableHeaderFontColor": "#333333"},
        "tableCell": {"tableFontColor": "#333333", "tableItemBgColor": "#ffffff"},
        "misc": {"nameFontColor": "#333333"}
    }),
    "customStyle": json.dumps({
        "text": {"show": True, "fontSize": 18, "color": "#333333", "hPosition": "left", "isItalic": False, "isBolder": True},
        "background": {"color": "#ffffff", "alpha": 100, "borderRadius": 5}
    }),
    "customFilter": "[]",
    "drillFields": "[]",
    "senior": "{}",
    "extColor": "[]",
    "flowMapStartName": "[]",
    "flowMapEndName": "[]",
    "isPlugin": False,
    "dataFrom": "dataset",
    "refreshViewEnable": False,
    "refreshUnit": "minute",
    "refreshTime": 5
}

# Build component data for the dashboard
component = {
    "id": f"component_{chart_id}",
    "component": "UserView",
    "name": "view",
    "label": "DSP Report Table",
    "propValue": {"innerType": "table-normal", "tabStyle": {}},
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
    "matrixStyle": {},
    "commonBackground": {"backgroundColor": "#ffffff", "backgroundColorSelect": True, "enable": True},
    "canvasId": "canvas_main",
    "canvasActive": False,
    "linkageActive": False,
    "hyperlinks": {"enable": False},
    "maintainRadio": None,
    "editBarRecordList": [],
    "innerType": "table-normal",
    "deWidget": None,
    "chartView": chart_view
}

# Update the dashboard canvas with the chart component
print("\n=== Updating dashboard with chart ===")
update_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "type": "dashboard",
    "pid": "0",
    "componentData": json.dumps([component]),
    "canvasStyleData": json.dumps({
        "width": 1920,
        "height": 1080,
        "selfAdaption": True,
        "auxiliaryMatrix": True,
        "openCommonStyle": True,
        "panel": {"themeColor": "light", "color": "#ffffff", "imageUrl": "", "borderRadius": 0},
        "dashboard": {}
    }),
    "canvasViewInfo": {chart_id: chart_view},
    "busiFlag": "dashboard"
}

r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=30)
print(f"HTTP Status: {r.status_code}")
print(f"Raw response: {r.text[:2000]}")
result = r.json() if r.status_code == 200 else {}
print(f"Code: {result.get('code')}")
msg = result.get('msg') or ''
print(f"Msg: {msg[:500]}")
if result.get('data'):
    print(f"Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else result['data']}")
    with open('d:/Projects/m2/scripts/update_result.json', 'w', encoding='utf-8') as f:
        json.dump(result['data'], f, indent=2, ensure_ascii=False)
    print("Result saved to update_result.json")

print(f"\n*** Dashboard URL: {base}/#/preview/{dashboard_id} ***")
print(f"*** Edit URL: {base}/#/dashboard/{dashboard_id} ***")
