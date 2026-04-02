"""Build the full ReportCenter dashboard in DataEase using ads_dsp_adv_index_report dataset."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time
import copy

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

# Dataset ID for ads_dsp_adv_index_report
ds_id = "1236079082777743360"

# Step 1: Get dataset fields
print("=== Step 1: Get dataset fields ===")
r = requests.post(f'{base}/de2api/datasetTree/details/{ds_id}', headers=headers, json={}, timeout=30)
ds_data = r.json()['data']
all_fields = ds_data.get('allFields', [])
print(f"Dataset has {len(all_fields)} fields")

# Build field lookup
field_map = {}
for f in all_fields:
    field_map[f['originName']] = f

# Step 2: Check existing dashboards
print("\n=== Step 2: Check existing dashboards ===")
r_dv = requests.post(f'{base}/de2api/dataVisualization/tree', headers=headers, json={"busiFlag": "dataV", "leafType": "panel"}, timeout=30)
dv_tree = r_dv.json().get('data', [])

def find_panels(nodes, depth=0):
    results = []
    for n in nodes:
        name = n.get('name', '')
        ntype = n.get('nodeType', '')
        nid = n.get('id', '')
        if ntype == 'panel':
            results.append({'id': nid, 'name': name, 'pid': n.get('pid')})
            print(f"{'  '*depth}[panel] {name} (id={nid})")
        else:
            print(f"{'  '*depth}[folder] {name} (id={nid})")
        children = n.get('children', [])
        if children:
            results.extend(find_panels(children, depth + 1))
    return results

panels = find_panels(dv_tree)

# Find existing DSP report dashboard or the root folder
existing_dsp = [p for p in panels if 'dsp' in p['name'].lower() or 'report' in p['name'].lower()]
print(f"\nExisting DSP panels: {existing_dsp}")

# Step 3: Define the fields we want in the table
# Based on ReportCenter and available fields in ads_dsp_adv_index_report

# Dimension columns (xAxis) - shown in ReportCenter
dim_columns = [
    ('report_date', 'Date'),
    ('report_hour', 'Hour'),
    ('affiliate_id', 'Aff ID'),
    ('affiliate_name', 'Aff Name'),
    ('ad_format', 'Ad Format'),
    ('bundle_id', 'Bundle ID'),
    ('country', 'Country'),
    ('publisher_id', 'Publisher ID'),
    ('adv_type', 'Adv Type'),
    ('adv_id', 'Adv ID'),
    ('adv_name', 'Adv Name'),
    ('first_ssp', 'First SSP'),
    ('response_type', 'Response Type'),
    ('traffic_type', 'Traffic Type'),
    ('domain', 'Domain'),
]

# Metric columns (yAxis) - shown in ReportCenter  
metric_columns = [
    ('response', 'Response', 'sum'),
    ('win', 'Wins', 'sum'),
    ('imp', 'Impressions', 'sum'),
    ('click', 'Click', 'sum'),
    ('cost', 'Cost', 'sum'),
    ('revenue', 'Revenue', 'sum'),
    ('revenue_d0', 'Revenue D0', 'sum'),
    ('revenue_d1', 'Revenue D1', 'sum'),
    ('revenue_d2', 'Revenue D2', 'sum'),
    ('revenue_d3', 'Revenue D3', 'sum'),
    ('event10', 'Event10', 'sum'),
    ('event10_d0', 'Event10 D0', 'sum'),
    ('event10_d1', 'Event10 D1', 'sum'),
    ('event10_d2', 'Event10 D2', 'sum'),
    ('event10_d3', 'Event10 D3', 'sum'),
    ('roi', 'ROI', 'avg'),
    ('imp_rate', 'Imp Rate', 'avg'),
    ('win_rate', 'Win Rate', 'avg'),
    ('cpc', 'CPC', 'avg'),
    ('cpm', 'CPM', 'avg'),
    ('ctr', 'CTR', 'avg'),
]

def build_field_item(origin_name, display_name, group_type, chart_type="table-normal", summary=""):
    f = field_map.get(origin_name)
    if not f:
        print(f"  WARNING: Field '{origin_name}' not found in dataset!")
        return None
    return {
        "id": f['id'],
        "chartId": None,
        "datasourceId": f.get('datasourceId'),
        "datasetTableId": f.get('datasetTableId'),
        "datasetGroupId": str(ds_id),
        "originName": f['originName'],
        "name": display_name,
        "dataeaseName": f.get('dataeaseName'),
        "groupType": group_type,
        "type": f['type'],
        "deType": f.get('deType', 0),
        "deExtractType": f.get('deExtractType', 0),
        "extField": f.get('extField', 0),
        "checked": True,
        "columnIndex": f.get('columnIndex', 0),
        "dateFormat": f.get('dateFormat'),
        "dateFormatType": f.get('dateFormatType'),
        "sort": "none",
        "filter": [],
        "fieldShortName": f.get('fieldShortName'),
        "chartType": chart_type,
        "summary": summary
    }

x_axis = []
for origin, display in dim_columns:
    item = build_field_item(origin, display, 'd')
    if item:
        x_axis.append(item)

y_axis = []
for origin, display, summary in metric_columns:
    item = build_field_item(origin, display, 'q', summary=summary)
    if item:
        y_axis.append(item)

print(f"\nxAxis fields: {len(x_axis)}")
print(f"yAxis fields: {len(y_axis)}")

# Step 4: Build date filter (last 7 days)
date_field = field_map.get('report_date')
custom_filter = None
if date_field:
    custom_filter = {
        "logic": "and",
        "items": [{
            "type": "field",
            "fieldId": int(date_field['id']),
            "filterType": "logic",
            "term": "ge",
            "value": "2026-03-24",
            "filterTypeTime": "dateValue"
        }],
        "filterType": "logic"
    }

# Step 5: Create a new dashboard
print("\n=== Step 3: Creating new dashboard ===")

# First find the root folder for dashboards
# Use pid=0 for root
new_panel_payload = {
    "name": "ReportCenter - DSP Report",
    "nodeType": "panel",
    "pid": 0
}
r_create = requests.post(f'{base}/de2api/dataVisualization/save', headers=headers, json=new_panel_payload, timeout=30)
print(f"Create dashboard status: {r_create.status_code}")
resp_create = r_create.json()
print(f"Response: {json.dumps(resp_create, ensure_ascii=False)[:500]}")

if resp_create.get('code') == 0:
    panel_id = resp_create.get('data')
    if isinstance(panel_id, dict):
        panel_id = panel_id.get('id')
    print(f"Dashboard created! ID: {panel_id}")
elif resp_create.get('code') == 40001 and '重复' in str(resp_create.get('msg', '')):
    # Already exists, find it
    print("Dashboard name already exists, finding existing one...")
    panel_id = None
    for p in panels:
        if p['name'] == 'ReportCenter - DSP Report':
            panel_id = p['id']
            break
    if not panel_id:
        # Try with a new name
        new_panel_payload['name'] = f"ReportCenter - DSP Report v2"
        r_create = requests.post(f'{base}/de2api/dataVisualization/save', headers=headers, json=new_panel_payload, timeout=30)
        resp_create = r_create.json()
        panel_id = resp_create.get('data')
        if isinstance(panel_id, dict):
            panel_id = panel_id.get('id')
    print(f"Using panel ID: {panel_id}")
else:
    print(f"ERROR creating dashboard: {resp_create}")
    sys.exit(1)

# Step 6: Get the dashboard data to understand the structure
print(f"\n=== Step 4: Get dashboard structure ===")
time.sleep(2)
r_get = requests.post(f'{base}/de2api/dataVisualization/findById/{panel_id}', headers=headers, json={}, timeout=30)
dv_data = r_get.json().get('data', {})
print(f"Dashboard name: {dv_data.get('name')}")

# Get existing canvas data
canvas_str = dv_data.get('canvasStyleData', '{}')
component_str = dv_data.get('componentData', '[]')

canvas_style = json.loads(canvas_str) if isinstance(canvas_str, str) else canvas_str
components = json.loads(component_str) if isinstance(component_str, str) else component_str
print(f"Existing components: {len(components)}")

# Step 7: Create a chart view for the table
print(f"\n=== Step 5: Create chart view ===")
chart_view_id = str(int(time.time() * 1000))

# Build the chart view
chart_view = {
    "id": chart_view_id,
    "sceneId": str(panel_id),
    "tableId": str(ds_id),
    "title": "DSP Report Table",
    "type": "table-normal",
    "render": "antv",
    "resultCount": 1000,
    "resultMode": "custom",
    "xAxis": x_axis,
    "xAxisExt": [],
    "yAxis": y_axis,
    "yAxisExt": [],
    "extStack": [],
    "extBubble": [],
    "extLabel": [],
    "extTooltip": [],
    "customFilter": custom_filter,
    "drillFields": [],
    "senior": {
        "functionCfg": {
            "sliderShow": False,
            "sliderRange": [0, 10],
            "roam": True
        }
    },
    "customAttr": json.dumps({
        "basicStyle": {
            "tableBorderColor": "#E6E7E4",
            "tableScrollBarColor": "rgba(0,0,0,0.15)",
            "alpha": 100,
            "tablePageMode": "pull",
            "tablePageSize": 20
        },
        "tableHeader": {
            "tableHeaderBgColor": "#F5F6F7",
            "tableHeaderFontColor": "#000000",
            "tableTitleFontSize": 12,
            "tableTitleHeight": 36,
            "tableHeaderAlign": "left",
            "showIndex": False,
            "indexLabel": "序号"
        },
        "tableCell": {
            "tableItemBgColor": "#FFFFFF",
            "tableFontColor": "#000000",
            "tableItemFontSize": 12,
            "tableItemHeight": 36,
            "tableItemAlign": "left",
            "enableTableCrossBG": True,
            "tableItemSubBgColor": "#F5F6F7"
        },
        "misc": {
            "nameFontColor": "#000000",
            "nameFontSize": 18,
            "showName": False
        },
        "label": {"show": True},
        "tooltip": {"show": True}
    }, ensure_ascii=False),
    "customStyle": json.dumps({
        "text": {
            "show": True,
            "fontSize": 16,
            "color": "#ffffff",
            "hPosition": "left",
            "vPosition": "top",
            "isItalic": False,
            "isBolder": True,
            "fontFamily": "Microsoft YaHei",
            "letterSpace": 0,
            "fontShadow": False
        },
        "background": {
            "backgroundType": "innerImage",
            "color": "#131E42",
            "alpha": 100,
            "borderRadius": 5
        }
    }, ensure_ascii=False),
    "drill": False,
    "jumpActive": False,
    "linkageActive": False
}

# Save the chart view
r_save_view = requests.post(f'{base}/de2api/chart/save', headers=headers, json=chart_view, timeout=30)
print(f"Save chart view status: {r_save_view.status_code}")
resp_view = r_save_view.json()
print(f"Code: {resp_view.get('code')}, Data: {str(resp_view.get('data', ''))[:200]}")

saved_chart_id = chart_view_id
if resp_view.get('code') == 0 and resp_view.get('data'):
    if isinstance(resp_view['data'], dict):
        saved_chart_id = str(resp_view['data'].get('id', chart_view_id))
    else:
        saved_chart_id = str(resp_view['data'])
    print(f"Chart view saved with ID: {saved_chart_id}")

# Step 8: Update the dashboard canvas with the chart component
print(f"\n=== Step 6: Update dashboard canvas ===")

# Build the component data for the table chart
component = {
    "id": saved_chart_id,
    "component": "UserView",
    "label": "table-normal",
    "propValue": {
        "innerType": "table-normal",
        "tabList": [],
        "render": "antv"
    },
    "icon": "",
    "style": {
        "width": 1600,
        "height": 600,
        "left": 0,
        "top": 0,
        "borderRadius": 5,
        "borderWidth": 0,
        "borderColor": "",
        "borderStyle": "solid",
        "opacity": 1,
        "backgroundColor": "",
        "backgroundImage": ""
    },
    "x": 0,
    "y": 0,
    "sizeX": 36,
    "sizeY": 18,
    "matrixStyle": {},
    "maintainRadio": False,
    "auxiliaryMatrix": True,
    "events": {},
    "linkage": {"open": False, "category": ""},
    "hyperlinks": {"openMode": "blank", "enable": False, "content": ""},
    "commonBackground": {
        "backgroundType": "color",
        "color": "#ffffff",
        "alpha": 100,
        "borderRadius": 5,
        "innerPadding": 0,
        "outerPadding": 2,
        "borderWidth": 0,
        "borderColor": "#DCDFE6",
        "borderStyle": "solid"
    },
    "innerType": "table-normal",
    "mobileSelected": False,
    "mobileStyle": {
        "style": {"width": 375, "height": 200, "left": 0, "top": 0}
    },
    "sourceViewId": None
}

new_components = [component]

canvas_style_updated = {
    "width": 1600,
    "height": 900,
    "refreshViewEnable": False,
    "refreshViewLoading": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
    "scale": 100,
    "scaleWidth": 100,
    "scaleHeight": 100,
    "selfAdaption": True,
    "auxiliaryMatrix": True,
    "matrixBase": 4,
    "dashboardActive": "pc",
    "mobileSetting": {
        "backgroundType": "color",
        "color": "#f5f6f7",
        "imageUrl": ""
    },
    "openCommonStyle": True,
    "dashboard": {
        "backgroundType": "color",
        "color": "#f5f6f7",
        "alpha": 100,
        "borderRadius": 0,
        "gap": "yes",
        "gapSize": 5
    },
    "component": {
        "commonBackground": {
            "backgroundType": "color",
            "color": "#ffffff",
            "alpha": 100,
            "borderRadius": 5,
            "innerPadding": 12,
            "outerPadding": 2,
            "borderWidth": 0,
            "borderColor": "#DCDFE6",
            "borderStyle": "solid"
        }
    }
}

update_payload = {
    "id": str(panel_id),
    "name": dv_data.get('name', 'ReportCenter - DSP Report'),
    "pid": dv_data.get('pid', '0'),
    "nodeType": "panel",
    "canvasStyleData": json.dumps(canvas_style_updated, separators=(',', ':')),
    "componentData": json.dumps(new_components, separators=(',', ':')),
    "watermarkInfo": json.dumps({"settingContent": {"enable": False, "enablePanelCustom": True, "content": "DataEase", "watermark_color": "#999999", "watermark_x_space": 100, "watermark_y_space": 100, "watermark_fontsize": 18}})
}

r_update = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=30)
print(f"Update canvas status: {r_update.status_code}")
resp_update = r_update.json()
print(f"Code: {resp_update.get('code')}, Msg: {str(resp_update.get('msg', ''))[:500]}")

# Step 9: Test querying the chart data
print(f"\n=== Step 7: Test chart data query ===")
chart_payload = {
    "type": "table-normal",
    "tableId": str(ds_id),
    "xAxis": x_axis,
    "xAxisExt": [],
    "yAxis": y_axis,
    "yAxisExt": [],
    "extStack": [],
    "extBubble": [],
    "extLabel": [],
    "extTooltip": [],
    "customFilter": custom_filter,
    "drill": False,
    "drillFields": [],
    "drillFilters": [],
    "senior": {"functionCfg": {"sliderShow": False, "sliderRange": [0, 10], "roam": True}},
    "resultCount": 100,
    "resultMode": "custom",
    "chartExtRequest": {"user": 1, "filter": [], "drill": [], "queryFrom": "panel", "resultCount": 100, "resultMode": "custom"}
}

start = time.time()
r_data = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_payload, timeout=300)
elapsed = time.time() - start
print(f"Query status: {r_data.status_code} ({elapsed:.1f}s)")
resp_data = r_data.json()
code_data = resp_data.get('code', -1)
print(f"Code: {code_data}")

if code_data == 0:
    data = resp_data.get('data', {})
    table_data = data.get('data', {})
    rows = table_data.get('tableRow', [])
    fields_resp = table_data.get('fields', [])
    print(f"Fields: {len(fields_resp)}")
    print(f"Rows: {len(rows)}")
    if rows:
        print("Sample rows:")
        for row in rows[:3]:
            print(f"  {json.dumps(row, ensure_ascii=False)[:300]}")
else:
    msg_data = resp_data.get('msg', '')
    print(f"Error: {str(msg_data)[:500]}")

print(f"\n=== Dashboard URL: {base}/#/panel/mobile/{panel_id} ===")
print(f"=== Edit URL: {base}/#/dvCanvas?dvId={panel_id}&opt=edit ===")
