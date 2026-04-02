"""Build the full ReportCenter dashboard in DataEase using saveCanvas + updateCanvas."""
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

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=60)
    return r.json()

# Dataset ID
ds_id = "1236079082777743360"

# Step 1: Get dataset fields
print("=== Step 1: Get dataset fields ===")
r = api(f'/datasetTree/details/{ds_id}')
all_fields = r['data']['allFields']
print(f"Dataset has {len(all_fields)} fields")
field_map = {f['originName']: f for f in all_fields}

# Step 2: Check existing dashboards
print("\n=== Step 2: List dashboards ===")
tree = api('/dataVisualization/tree', {"busiFlag": "dataV", "leafType": "panel"})
panels = []
def find_all(nodes, depth=0):
    for n in nodes:
        name, nid, ntype = n.get('name',''), n.get('id',''), n.get('nodeType','')
        print(f"{'  '*depth}[{ntype}] {name} (id={nid})")
        if ntype == 'panel':
            panels.append(n)
        for c in (n.get('children') or []):
            find_all([c], depth+1)
find_all(tree.get('data', []))

# Try to find existing panel for DSP or create new one
panel_id = None
for p in panels:
    if 'DSP' in p.get('name', '') or 'Report' in p.get('name', ''):
        panel_id = p['id']
        print(f"\nFound existing panel: {p['name']} -> id={panel_id}")
        break

if not panel_id:
    print("\n=== Creating new dashboard via saveCanvas ===")
    canvas_style = {
        "width": 1600,
        "height": 900,
        "selfAdaption": True,
        "auxiliaryMatrix": True,
        "matrixBase": 4,
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
    
    create_payload = {
        "name": "ReportCenter - DSP Report",
        "pid": "0",
        "type": "dataV",
        "nodeType": "panel",
        "componentData": "[]",
        "canvasStyleData": json.dumps(canvas_style, separators=(',', ':')),
        "busiFlag": "dataV"
    }
    
    result = api('/dataVisualization/saveCanvas', create_payload)
    print(f"Code: {result.get('code')}, Data: {result.get('data')}")
    if result.get('code') == 0:
        panel_id = result['data']
        print(f"Dashboard created! ID: {panel_id}")
    else:
        print(f"Error: {result.get('msg')}")
        # Try another name
        create_payload['name'] = "ReportCenter DSP v3"
        result = api('/dataVisualization/saveCanvas', create_payload)
        print(f"Retry - Code: {result.get('code')}, Data: {result.get('data')}")
        if result.get('code') == 0:
            panel_id = result['data']

if not panel_id:
    print("FATAL: Cannot create/find dashboard!")
    sys.exit(1)

print(f"\nUsing panel_id: {panel_id}")

# Step 3: Get the current dashboard state
print("\n=== Step 3: Get dashboard state ===")
dv_resp = api(f'/dataVisualization/findById/{panel_id}')
dv_data = dv_resp.get('data', {})
print(f"Name: {dv_data.get('name')}, canvasViewInfo keys: {list(dv_data.get('canvasViewInfo', {}).keys()) if dv_data.get('canvasViewInfo') else 'None'}")

# Step 4: Build the chart fields
print("\n=== Step 4: Build chart fields ===")

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

def build_field(origin_name, display_name, group_type, summary=""):
    f = field_map.get(origin_name)
    if not f:
        print(f"  WARNING: '{origin_name}' not found")
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
        "chartType": "table-normal",
        "summary": summary
    }

x_axis = [build_field(o, d, 'd') for o, d in dim_columns]
x_axis = [x for x in x_axis if x]

y_axis = [build_field(o, d, 'q', s) for o, d, s in metric_columns]
y_axis = [y for y in y_axis if y]

print(f"xAxis: {len(x_axis)} dims, yAxis: {len(y_axis)} metrics")

# Date filter
date_f = field_map.get('report_date')
custom_filter = {
    "logic": "and",
    "items": [{
        "type": "field",
        "fieldId": int(date_f['id']),
        "filterType": "logic",
        "term": "ge",
        "value": "2026-03-24",
        "filterTypeTime": "dateValue"
    }],
    "filterType": "logic"
} if date_f else None

# Step 5: Use updateCanvas to set chart & component
print("\n=== Step 5: Build chart view and update canvas ===")

chart_id = str(int(time.time() * 1000))

custom_attr = {
    "basicStyle": {
        "tableBorderColor": "#E6E7E4",
        "tableScrollBarColor": "rgba(0,0,0,0.15)",
        "alpha": 100,
        "tablePageMode": "pull",
        "tablePageSize": 20,
        "showSummary": False
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
}

custom_style = {
    "text": {
        "show": True,
        "fontSize": 14,
        "color": "#000000",
        "hPosition": "left",
        "vPosition": "top",
        "isItalic": False,
        "isBolder": True,
        "fontFamily": "Microsoft YaHei",
        "letterSpace": 0,
        "fontShadow": False
    },
    "background": {
        "backgroundType": "color",
        "color": "#FFFFFF",
        "alpha": 100,
        "borderRadius": 5
    }
}

# Build the canvasViewInfo entry
canvas_view_info = {
    chart_id: {
        "id": chart_id,
        "sceneId": str(panel_id),
        "tableId": str(ds_id),
        "title": "DSP Report",
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
        "customAttr": json.dumps(custom_attr, ensure_ascii=False),
        "customStyle": json.dumps(custom_style, ensure_ascii=False),
        "drill": False,
        "jumpActive": False,
        "linkageActive": False,
        "isPlugin": False,
        "chartExtRequest": {
            "user": 1,
            "filter": [],
            "drill": [],
            "queryFrom": "panel",
            "resultCount": 1000,
            "resultMode": "custom"
        }
    }
}

# Component referencing the chart
component = {
    "id": chart_id,
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
        "borderRadius": 5
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
        "innerPadding": 12,
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

canvas_style = {
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
    "pid": str(dv_data.get('pid', '0')),
    "nodeType": "panel",
    "type": "dataV",
    "canvasStyleData": json.dumps(canvas_style, separators=(',', ':')),
    "componentData": json.dumps([component], separators=(',', ':')),
    "canvasViewInfo": canvas_view_info,
    "watermarkInfo": json.dumps({"settingContent": {"enable": False, "enablePanelCustom": True, "content": "DataEase", "watermark_color": "#999999", "watermark_x_space": 100, "watermark_y_space": 100, "watermark_fontsize": 18}})
}

r_update = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"Update canvas: status={r_update.status_code}")
resp_update = r_update.json()
print(f"Code: {resp_update.get('code')}, Msg: {str(resp_update.get('msg', ''))[:300]}")

if resp_update.get('code') == 0:
    print("\n*** Dashboard updated successfully! ***")
    
    # Verify
    time.sleep(2)
    verify = api(f'/dataVisualization/findById/{panel_id}')
    vd = verify.get('data', {})
    comps = json.loads(vd.get('componentData', '[]')) if isinstance(vd.get('componentData'), str) else vd.get('componentData', [])
    cvi = vd.get('canvasViewInfo', {})
    print(f"Components: {len(comps)}, Views: {len(cvi)}")
    if cvi:
        for vid, vinfo in cvi.items():
            print(f"  View {vid}: type={vinfo.get('type')}, table={vinfo.get('tableId')}, xAxis={len(vinfo.get('xAxis', []))}, yAxis={len(vinfo.get('yAxis', []))}")

print(f"\n=== Dashboard URLs ===")
print(f"View: {base}/#/panel/mobile/{panel_id}")
print(f"Edit: {base}/#/dvCanvas?dvId={panel_id}&opt=edit")
print(f"Preview: {base}/#/preview/{panel_id}")
