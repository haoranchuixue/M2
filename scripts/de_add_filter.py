"""Add date range filter component to the dashboard."""
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

ds_id = "1236079082777743360"
panel_id = "1236081407923720192"

# Get dataset fields
r = requests.post(f'{base}/de2api/datasetTree/details/{ds_id}', headers=headers, json={}, timeout=30)
all_fields = r.json()['data']['allFields']
field_map = {f['originName']: f for f in all_fields}
date_field = field_map['report_date']

# Get current dashboard
r2 = requests.post(f'{base}/de2api/dataVisualization/findById/{panel_id}', headers=headers, json={}, timeout=30)
dv = r2.json().get('data') or {}
cur_version = dv.get('version') or 1
cvi = dv.get('canvasViewInfo', {}) or {}
old_components = json.loads(dv.get('componentData', '[]')) if isinstance(dv.get('componentData'), str) else (dv.get('componentData') or [])
old_canvas = dv.get('canvasStyleData', '{}')
if isinstance(old_canvas, str):
    old_canvas = json.loads(old_canvas)

chart_id = list(cvi.keys())[0] if cvi else None
chart_view = cvi.get(chart_id) if chart_id else None
print(f"Version: {cur_version}, chart: {chart_id}")
print(f"Existing components: {len(old_components)}")

# Create date range filter component
filter_id = str(int(time.time() * 1000))

date_filter_component = {
    "animations": [],
    "canvasId": "canvas-main",
    "events": {},
    "groupStyle": {},
    "isLock": False,
    "isShow": True,
    "collapseName": ["position", "background", "style"],
    "linkage": {"duration": 0},
    "component": "VQuery",
    "name": "日期筛选",
    "label": "日期筛选",
    "propValue": {
        "innerType": "VQueryDatePicker",
        "parametersType": "dateRange",
        "defaultConditionValueOperatorF": "between",
        "conditionValueOperatorF": "between",
        "defaultConditionValueF": "",
        "conditionType": 0,
        "conditionValueOperator": "between",
        "defaultRelativeToCurrent": "custom",
        "relativeToCurrent": "custom",
        "relativeToCurrentType": "year",
        "required": False,
        "defaultMapValue": [],
        "defaultValue": ["2026-03-27", "2026-03-30"],
        "selectValue": ["2026-03-27", "2026-03-30"],
        "checkedFields": [{
            "datasetId": str(ds_id),
            "id": date_field['id'],
            "originName": date_field['originName'],
            "name": "Date",
            "deType": date_field.get('deType', 1),
            "groupType": "d",
            "checked": True
        }],
        "checkedFieldsMap": {
            str(ds_id): [{
                "datasetId": str(ds_id),
                "id": date_field['id'],
                "originName": date_field['originName'],
                "name": "Date",
                "deType": date_field.get('deType', 1),
                "groupType": "d",
                "checked": True
            }]
        },
        "displayType": "new",
        "timeGranularity": "date",
        "timeGranularityMultiple": "daterange",
        "showTitle": True,
        "title": "Report Date",
        "titleColor": "#000000",
        "titleFontSize": 14,
        "parameters": [],
        "visible": True,
        "id": filter_id
    },
    "icon": "",
    "innerType": "VQueryDatePicker",
    "editing": False,
    "x": 1, "y": 1, "sizeX": 18, "sizeY": 2,
    "style": {"rotate": 0, "opacity": 1, "width": 400, "height": 50, "left": 10, "top": 10},
    "matrixStyle": {},
    "commonBackground": {
        "backgroundColorSelect": True, "backgroundImageEnable": False, "backgroundType": "color",
        "innerImage": "", "outerImage": "", "innerPadding": 0, "borderRadius": 5,
        "backgroundColor": "rgba(255, 255, 255, 1)"
    },
    "state": "ready",
    "render": "custom",
    "id": filter_id,
    "_dragId": 0,
    "show": True,
    "mobileSelected": False,
    "mobileStyle": {"style": {"width": 375, "height": 50, "left": 0, "top": 0}},
    "sourceViewId": None,
    "linkageFilters": [],
    "canvasActive": False,
    "maintainRadio": False,
    "aspectRatio": 1,
    "actionSelection": {"linkageActive": "custom"}
}

# Move the chart component down to make room for filter
chart_component = None
for comp in old_components:
    if comp.get('id') == chart_id:
        chart_component = comp
        break

if chart_component:
    chart_component['y'] = 3
    chart_component['sizeY'] = 26

new_components = [date_filter_component]
if chart_component:
    new_components.append(chart_component)
else:
    print("WARNING: Chart component not found in old components, keeping as-is")
    for comp in old_components:
        comp['y'] = 3
        new_components.append(comp)

print(f"New components: {len(new_components)}")

compact_comp = json.dumps(new_components, separators=(',', ':'), ensure_ascii=False)

# Make sure chart id pattern exists
if chart_id:
    check = f'"id":"{chart_id}"'
    assert check in compact_comp, f"Chart ID pattern not found!"

compact_style = json.dumps(old_canvas, separators=(',', ':'))

# Update canvas 
update_payload = {
    "id": panel_id,
    "name": "ReportCenter - DSP Report",
    "pid": 0,
    "type": "dataV",
    "busiFlag": "dataV",
    "componentData": compact_comp,
    "canvasStyleData": compact_style,
    "canvasViewInfo": cvi,
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": str(dv.get('contentId', '0')),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0
}

print(f"\n=== Updating canvas ===")
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"HTTP: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}, Msg: {str(resp.get('msg',''))[:300]}")
    
    if resp.get('code') == 0:
        # Publish
        pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                            headers=headers,
                            json={"id": panel_id, "type": "dataV", "busiFlag": "dataV", "status": 1, "pid": 0},
                            timeout=30)
        print(f"Publish: code={pub.json().get('code')}")
        print("SUCCESS!")
else:
    print(f"Error: {r.text[:500]}")

print(f"\nPreview: {base}/#/preview/{panel_id}")
print(f"Edit:    {base}/#/dvCanvas?dvId={panel_id}&opt=edit")
