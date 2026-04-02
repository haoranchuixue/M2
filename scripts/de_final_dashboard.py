"""Final dashboard build - update the 'ReportCenter DSP Report' (type=dashboard) with chart."""
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
panel_id = "1236085805173313536"

# Get dataset fields
all_fields = api(f'/datasetTree/details/{ds_id}')['data']['allFields']
field_map = {f['originName']: f for f in all_fields}
date_field = field_map['report_date']
print(f"Dataset: {len(all_fields)} fields")

# Get dashboard state
snap = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dashboard", "resourceTable": "snapshot"})
snap_data = snap.get('data') or {}
cur_version = snap_data.get('version') or 1
print(f"Dashboard version: {cur_version}")

# Build fields
def make_field(f, display_name=None, group_type=None, summary=""):
    return {
        "id": f['id'],
        "datasetTableId": f.get('datasetTableId'),
        "datasetGroupId": str(ds_id),
        "datasourceId": f.get('datasourceId'),
        "chartType": "table-normal",
        "originName": f['originName'],
        "name": display_name or f.get('name') or f['originName'],
        "dataeaseName": f.get('dataeaseName'),
        "type": f['type'],
        "deType": f.get('deType', 0),
        "deExtractType": f.get('deExtractType', 0),
        "extField": f.get('extField', 0),
        "groupType": group_type or f.get('groupType', 'd'),
        "checked": True,
        "columnIndex": f.get('columnIndex', 0),
        "lastSyncTime": f.get('lastSyncTime'),
        "dateFormat": f.get('dateFormat'),
        "dateFormatType": f.get('dateFormatType'),
        "description": f.get('description'),
        "chartId": None,
        "sort": "none",
        "summary": summary,
        "fieldShortName": f.get('fieldShortName'),
        "index": None,
        "formatterCfg": {"type": "auto", "unitLanguage": "ch", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
        "chartShowName": None,
        "filter": [],
        "customSort": None,
        "busiType": None,
        "hide": False,
        "field": None,
        "agg": False
    }

dims = [
    ('report_date', 'Date'),
    ('adv_id', 'Adv ID'),
    ('adv_name', 'Adv Name'),
    ('country', 'Country'),
]
metrics = [
    ('response', 'Response', 'sum'),
    ('win', 'Wins', 'sum'),
    ('imp', 'Impressions', 'sum'),
    ('click', 'Click', 'sum'),
    ('cost', 'Cost', 'sum'),
    ('revenue', 'Revenue', 'sum'),
    ('event10', 'Event10', 'sum'),
    ('roi', 'ROI', 'avg'),
    ('win_rate', 'Win Rate', 'avg'),
    ('cpm', 'CPM', 'avg'),
    ('ctr', 'CTR', 'avg'),
]

x_axis = [make_field(field_map[o], d, 'd') for o, d in dims]
y_axis = [make_field(field_map[o], d, 'q', s) for o, d, s in metrics]
print(f"xAxis: {len(x_axis)}, yAxis: {len(y_axis)}")

custom_filter = {
    "logic": "and",
    "items": [{
        "type": "field",
        "fieldId": int(date_field['id']),
        "filterType": "logic",
        "term": "ge",
        "value": "2026-03-27",
        "filterTypeTime": "dateValue"
    }],
    "filterType": "logic"
}

chart_id = str(int(time.time() * 1000))

chart_view = {
    "id": chart_id,
    "title": "DSP Report",
    "sceneId": str(panel_id),
    "tableId": str(ds_id),
    "type": "table-normal",
    "render": "antv",
    "resultCount": 1000,
    "resultMode": "custom",
    "extStack": [], "extBubble": [], "extLabel": [], "extTooltip": [],
    "customAttr": {
        "basicStyle": {
            "alpha": 100, "tableBorderColor": "#E6E7E4",
            "tableScrollBarColor": "rgba(0,0,0,0.15)", "tableColumnMode": "adapt",
            "tableColumnWidth": 100, "tablePageMode": "pull", "tablePageSize": 20,
            "gaugeStyle": "default", "colorScheme": "default",
            "colors": ["#1E90FF","#90EE90","#00CED1","#E2BD84","#7A90E0","#3BA272","#2BE7FF","#0A8ADA","#FFD700"],
            "mapVendor": "amap", "gradient": True, "lineWidth": 2, "lineSymbol": "circle",
            "lineSymbolSize": 4, "lineSmooth": True, "barDefault": True, "barWidth": 40,
            "barGap": 0.4, "lineType": "solid", "scatterSymbol": "circle", "scatterSymbolSize": 8,
            "radarShape": "polygon", "mapStyle": "normal", "areaBorderColor": "#303133",
            "suspension": True, "areaBaseColor": "#FFFFFF", "mapSymbolOpacity": 0.7,
            "mapSymbolStrokeWidth": 2, "mapSymbol": "circle", "mapSymbolSize": 20,
            "radius": 100, "innerRadius": 60, "showZoom": True, "zoomButtonColor": "#aaa",
            "zoomBackground": "#fff", "tableLayoutMode": "grid"
        },
        "tableHeader": {"indexLabel": "序号", "showIndex": False, "tableHeaderAlign": "left",
                        "tableHeaderBgColor": "#F5F6F7", "tableHeaderFontColor": "#333333",
                        "tableTitleFontSize": 12, "tableTitleHeight": 36, "tableHeaderSort": True},
        "tableCell": {"tableFontColor": "#333333", "tableItemAlign": "left", "tableItemBgColor": "#ffffff",
                      "tableItemFontSize": 12, "tableItemHeight": 36, "enableTableCrossBG": True,
                      "tableItemSubBgColor": "#F8F8F9"},
        "misc": {"showName": True, "nameFontSize": 16, "nameFontColor": "#333333"},
        "label": {"show": False},
        "tooltip": {"show": True}
    },
    "customAttrMobile": None,
    "customStyle": {
        "text": {"show": True, "fontSize": "14", "hPosition": "left", "vPosition": "top", "isItalic": False,
                 "isBolder": True, "remarkShow": False, "remark": "", "fontFamily": "Microsoft YaHei",
                 "letterSpace": "0", "fontShadow": False, "color": "#333333"},
        "legend": {"show": True, "hPosition": "center", "vPosition": "bottom", "orient": "horizontal",
                   "icon": "circle", "color": "#333333", "fontSize": 12},
        "misc": {"showName": False}
    },
    "customStyleMobile": None,
    "customFilter": custom_filter,
    "drillFields": [],
    "senior": {
        "functionCfg": {"sliderShow": False, "sliderRange": [0, 10], "sliderBg": "#FFFFFF",
                        "sliderFillBg": "#BCD6F1", "sliderTextColor": "#999999",
                        "emptyDataStrategy": "breakLine", "emptyDataFieldCtrl": []},
        "assistLineCfg": {"enable": False, "assistLine": []},
        "threshold": {"enable": False, "gaugeThreshold": "", "labelThreshold": [],
                      "tableThreshold": [], "textLabelThreshold": []},
        "scrollCfg": {"open": False, "row": 1, "interval": 2000, "step": 50}
    },
    "stylePriority": "panel", "chartType": "private", "isPlugin": None,
    "dataFrom": "dataset", "viewFields": [],
    "refreshViewEnable": False, "refreshUnit": "minute", "refreshTime": 5,
    "linkageActive": False, "jumpActive": False,
    "flowMapStartName": [], "flowMapEndName": [], "calParams": [], "extColor": [], "sortPriority": [],
    "drill": False, "drillFilters": None,
    "totalPage": 0, "totalItems": 0, "datasetMode": 0,
    "chartExtRequest": None, "isExcelExport": False,
    "xAxis": x_axis, "xAxisExt": [], "yAxis": y_axis, "yAxisExt": []
}

component = {
    "animations": [],
    "canvasId": "canvas-main",
    "events": {},
    "groupStyle": {},
    "isLock": False,
    "isShow": True,
    "collapseName": ["position", "background", "style"],
    "linkage": {"duration": 0},
    "component": "UserView",
    "name": "DSP Report",
    "label": "DSP Report",
    "propValue": {"innerType": "table-normal"},
    "icon": "bar",
    "innerType": "table-normal",
    "editing": False,
    "x": 1, "y": 1, "sizeX": 72, "sizeY": 28,
    "style": {"rotate": 0, "opacity": 1, "width": 1880, "height": 700, "left": 10, "top": 10},
    "matrixStyle": {},
    "commonBackground": {
        "backgroundColorSelect": True, "backgroundImageEnable": False, "backgroundType": "color",
        "innerImage": "", "outerImage": "", "innerPadding": 0, "borderRadius": 5,
        "backgroundColor": "rgba(255, 255, 255, 1)"
    },
    "state": "ready",
    "render": "custom",
    "id": chart_id,
    "_dragId": 0,
    "show": True,
    "mobileSelected": False,
    "mobileStyle": {"style": {"width": 375, "height": 200, "left": 0, "top": 0}},
    "sourceViewId": None,
    "linkageFilters": [],
    "canvasActive": False,
    "maintainRadio": False,
    "aspectRatio": 1,
    "actionSelection": {"linkageActive": "custom"}
}

compact_comp = json.dumps([component], separators=(',', ':'), ensure_ascii=False)
compact_style = json.dumps({
    "width": 1920, "height": 1080, "selfAdaption": True, "auxiliaryMatrix": True,
    "openCommonStyle": True,
    "panel": {"themeColor": "light", "color": "#f5f6f7", "imageUrl": "", "borderRadius": 0},
    "dashboard": {}
}, separators=(',', ':'))

check = f'"id":"{chart_id}"'
assert check in compact_comp

print(f"\nChart ID: {chart_id}")

update_payload = {
    "id": panel_id,
    "name": "ReportCenter DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": compact_comp,
    "canvasStyleData": compact_style,
    "canvasViewInfo": {chart_id: chart_view},
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": str(snap_data.get('contentId', '0')),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0
}

print(f"=== Updating canvas ===")
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"HTTP: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    code = resp.get('code')
    print(f"Code: {code}")
    
    if code == 0:
        # Publish
        pub = api('/dataVisualization/updatePublishStatus',
                   {"id": panel_id, "type": "dashboard", "busiFlag": "dashboard", "status": 1, "pid": 0})
        print(f"Publish: {pub.get('code')}")
        
        # Verify
        time.sleep(2)
        v = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dashboard", "resourceTable": "core"})
        vd = v.get('data', {})
        vcvi = vd.get('canvasViewInfo', {}) or {}
        vc = json.loads(vd.get('componentData', '[]')) if isinstance(vd.get('componentData'), str) else (vd.get('componentData') or [])
        print(f"Core: {len(vc)} components, {len(vcvi)} views")
        
        print("\n*** SUCCESS ***")
    else:
        print(f"Error: {resp.get('msg', '')[:300]}")
else:
    print(f"Error: {r.text[:500]}")

# Now take a screenshot
print("\n=== Taking screenshot ===")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Navigate to dashboard list and click the dashboard
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(5)
    
    # Find and click the ReportCenter DSP Report
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and 'ReportCenter' in text:
            print(f"Found: {text}")
            el.click()
            break
    
    time.sleep(5)
    page.screenshot(path='d:/Projects/m2/scripts/ss_dashboard_click.png')
    
    # Wait for data to load
    print("Waiting for data to load...")
    time.sleep(25)
    page.screenshot(path='d:/Projects/m2/scripts/ss_dashboard_loaded.png')
    print("Screenshots saved")
    
    browser.close()

print(f"\nDashboard: {base}/#/panel/index")
