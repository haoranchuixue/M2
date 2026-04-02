"""Build the full ReportCenter dashboard in DataEase - fixed updateCanvas payload."""
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

ds_id = "1236079082777743360"
panel_id = "1236081407923720192"

# Step 1: Get dataset fields
print("=== Step 1: Get dataset fields ===")
r = api(f'/datasetTree/details/{ds_id}')
all_fields = r['data']['allFields']
print(f"Dataset has {len(all_fields)} fields")
field_map = {f['originName']: f for f in all_fields}

# Step 2: Get current dashboard state (from snapshot)
print("\n=== Step 2: Get current dashboard state ===")
dv_resp = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dataV", "resourceTable": "snapshot"})
dv_data = dv_resp.get('data', {})
print(f"Name: {dv_data.get('name')}")
print(f"Type: {dv_data.get('type')}")
print(f"Version: {dv_data.get('version')}")
print(f"ContentId: {dv_data.get('contentId')}")
print(f"Status: {dv_data.get('status')}")
cur_version = dv_data.get('version', 1)
content_id = dv_data.get('contentId', '0')

# Step 3: Build chart fields
print("\n=== Step 3: Build chart fields ===")
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

x_axis = [x for x in [build_field(o, d, 'd') for o, d in dim_columns] if x]
y_axis = [y for y in [build_field(o, d, 'q', s) for o, d, s in metric_columns] if y]
print(f"xAxis: {len(x_axis)} dims, yAxis: {len(y_axis)} metrics")

# Date filter - last 7 days
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

# Step 4: Build chart view
chart_id = str(int(time.time() * 1000))
print(f"Chart ID: {chart_id}")

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
    "misc": {"nameFontColor": "#000000", "nameFontSize": 18, "showName": False},
    "label": {"show": True},
    "tooltip": {"show": True}
}

custom_style = {
    "text": {
        "show": True, "fontSize": 14, "color": "#000000",
        "hPosition": "left", "vPosition": "top",
        "isItalic": False, "isBolder": True,
        "fontFamily": "Microsoft YaHei", "letterSpace": 0, "fontShadow": False
    },
    "background": {
        "backgroundType": "color", "color": "#FFFFFF", "alpha": 100, "borderRadius": 5
    }
}

chart_view = {
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
    "senior": {"functionCfg": {"sliderShow": False, "sliderRange": [0, 10], "roam": True}},
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

# Component
component = {
    "id": chart_id,
    "component": "UserView",
    "label": "table-normal",
    "propValue": {"innerType": "table-normal", "tabList": [], "render": "antv"},
    "icon": "",
    "style": {
        "width": 1600, "height": 600, "left": 0, "top": 0,
        "borderRadius": 5, "borderWidth": 0, "borderColor": "",
        "borderStyle": "solid", "opacity": 1,
        "backgroundColor": "", "backgroundImage": ""
    },
    "x": 0, "y": 0, "sizeX": 36, "sizeY": 18,
    "matrixStyle": {},
    "maintainRadio": False,
    "auxiliaryMatrix": True,
    "events": {},
    "linkage": {"open": False, "category": ""},
    "hyperlinks": {"openMode": "blank", "enable": False, "content": ""},
    "commonBackground": {
        "backgroundType": "color", "color": "#ffffff", "alpha": 100,
        "borderRadius": 5, "innerPadding": 12, "outerPadding": 2,
        "borderWidth": 0, "borderColor": "#DCDFE6", "borderStyle": "solid"
    },
    "innerType": "table-normal",
    "mobileSelected": False,
    "mobileStyle": {"style": {"width": 375, "height": 200, "left": 0, "top": 0}},
    "sourceViewId": None,
    "linkageFilters": [],
    "canvasActive": False,
    "maintainRadio": False,
    "aspectRatio": 1,
    "actionSelection": {"linkageActive": "custom"}
}

# Compact JSON for component data
compact_comp = json.dumps([component], separators=(',', ':'), ensure_ascii=False)
compact_style = json.dumps({
    "width": 1600, "height": 900, "selfAdaption": True, "auxiliaryMatrix": True,
    "matrixBase": 4, "openCommonStyle": True,
    "dashboard": {
        "backgroundType": "color", "color": "#f5f6f7", "alpha": 100,
        "borderRadius": 0, "gap": "yes", "gapSize": 5
    },
    "component": {
        "commonBackground": {
            "backgroundType": "color", "color": "#ffffff", "alpha": 100,
            "borderRadius": 5, "innerPadding": 12, "outerPadding": 2,
            "borderWidth": 0, "borderColor": "#DCDFE6", "borderStyle": "solid"
        }
    }
}, separators=(',', ':'))

# Verify pattern
check_pattern = f'"id":"{chart_id}"'
assert check_pattern in compact_comp, f"Pattern {check_pattern} not found!"
print(f"Component ID check OK: {check_pattern}")

# Step 5: updateCanvas
print("\n=== Step 5: Update canvas ===")
update_payload = {
    "id": panel_id,
    "name": "ReportCenter - DSP Report",
    "pid": 0,
    "type": "dataV",
    "busiFlag": "dataV",
    "componentData": compact_comp,
    "canvasStyleData": compact_style,
    "canvasViewInfo": {chart_id: chart_view},
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": str(content_id) if content_id else "0",
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0
}

r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"HTTP Status: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    code = resp.get('code')
    msg = resp.get('msg') or ''
    print(f"Code: {code}, Msg: {str(msg)[:500]}")
    
    if code == 0:
        print("\n*** Dashboard updated successfully! ***")
        
        time.sleep(2)
        verify = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dataV", "resourceTable": "snapshot"})
        vd = verify.get('data', {})
        comps = json.loads(vd.get('componentData', '[]')) if isinstance(vd.get('componentData'), str) else (vd.get('componentData') or [])
        cvi = vd.get('canvasViewInfo', {}) or {}
        print(f"Components: {len(comps)}, Views: {len(cvi)}")
        
        if cvi:
            for vid, vinfo in cvi.items():
                print(f"  View {vid}: type={vinfo.get('type')}, tableId={vinfo.get('tableId')}, x={len(vinfo.get('xAxis', []))}, y={len(vinfo.get('yAxis', []))}")
            
            # Publish
            print("\n=== Publishing ===")
            pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                                headers=headers,
                                json={"id": panel_id, "type": "dataV", "busiFlag": "dataV", "status": 1, "pid": 0},
                                timeout=30)
            print(f"Publish: {pub.status_code}, {pub.json().get('code')}")
else:
    print(f"Error body: {r.text[:500]}")

print(f"\n=== Dashboard URLs ===")
print(f"View:    {base}/#/panel/mobile/{panel_id}")
print(f"Edit:    {base}/#/dvCanvas?dvId={panel_id}&opt=edit")
print(f"Preview: {base}/#/preview/{panel_id}")
