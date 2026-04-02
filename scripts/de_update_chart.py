"""Update the chart with fewer default dimensions to avoid CPU limit."""
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

# Get dataset fields
r = api(f'/datasetTree/details/{ds_id}')
all_fields = r['data']['allFields']
field_map = {f['originName']: f for f in all_fields}
print(f"Dataset: {len(all_fields)} fields")

# Get current dashboard state
dv_resp = api(f'/dataVisualization/findById/{panel_id}')
if dv_resp.get('code') != 0 or not dv_resp.get('data'):
    dv_resp = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dataV", "resourceTable": "snapshot"})
dv_data = dv_resp.get('data') or {}
cur_version = dv_data.get('version') or 1
cvi = dv_data.get('canvasViewInfo', {}) or {}
old_chart_id = list(cvi.keys())[0] if cvi else None
print(f"Version: {cur_version}, existing chart: {old_chart_id}")

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

# Key insight: use fewer default dimensions to keep query fast
# Date is mandatory. Add a few key dims that users commonly need.
# Other dims can be added via DataEase dimension settings.
default_dims = [
    ('report_date', 'Date', 'd'),
    ('adv_id', 'Adv ID', 'd'),
    ('adv_name', 'Adv Name', 'd'),
    ('country', 'Country', 'd'),
]

# Core metrics only
default_metrics = [
    ('response', 'Response', 'q', 'sum'),
    ('win', 'Wins', 'q', 'sum'),
    ('imp', 'Impressions', 'q', 'sum'),
    ('click', 'Click', 'q', 'sum'),
    ('cost', 'Cost', 'q', 'sum'),
    ('revenue', 'Revenue', 'q', 'sum'),
    ('event10', 'Event10', 'q', 'sum'),
    ('roi', 'ROI', 'q', 'avg'),
    ('win_rate', 'Win Rate', 'q', 'avg'),
    ('cpm', 'CPM', 'q', 'avg'),
    ('ctr', 'CTR', 'q', 'avg'),
]

x_axis = []
for origin, display, gtype in default_dims:
    f = field_map.get(origin)
    if f:
        x_axis.append(make_field(f, display, gtype))

y_axis = []
for origin, display, gtype, summary in default_metrics:
    f = field_map.get(origin)
    if f:
        y_axis.append(make_field(f, display, gtype, summary))

print(f"xAxis: {len(x_axis)} dims, yAxis: {len(y_axis)} metrics")

# Date filter: last 3 days
date_f = field_map.get('report_date')
today = "2026-03-30"
three_days_ago = "2026-03-27"
custom_filter = {
    "logic": "and",
    "items": [{
        "type": "field",
        "fieldId": int(date_f['id']),
        "filterType": "logic",
        "term": "ge",
        "value": three_days_ago,
        "filterTypeTime": "dateValue"
    }],
    "filterType": "logic"
} if date_f else {"logic": None, "items": None}

chart_id = old_chart_id or str(int(time.time() * 1000))
print(f"Using chart_id: {chart_id}")

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
            "zoomBackground": "#fff", "tableLayoutMode": "grid", "calcTopN": False,
            "topN": 5, "topNLabel": "其他"
        },
        "tableHeader": {"indexLabel": "序号", "showIndex": False, "tableHeaderAlign": "left",
                        "tableHeaderBgColor": "#F5F6F7", "tableHeaderFontColor": "#333333",
                        "tableTitleFontSize": 12, "tableTitleHeight": 36, "tableHeaderSort": True},
        "tableCell": {"tableFontColor": "#333333", "tableItemAlign": "left", "tableItemBgColor": "#ffffff",
                      "tableItemFontSize": 12, "tableItemHeight": 36, "enableTableCrossBG": True,
                      "tableItemSubBgColor": "#F8F8F9"},
        "misc": {"showName": True, "nameFontSize": 18, "nameFontColor": "#000000"},
        "label": {"show": False},
        "tooltip": {"show": True}
    },
    "customAttrMobile": None,
    "customStyle": {
        "text": {"show": True, "fontSize": "14", "hPosition": "left", "vPosition": "top", "isItalic": False,
                 "isBolder": True, "remarkShow": False, "remark": "", "fontFamily": "Microsoft YaHei",
                 "letterSpace": "0", "fontShadow": False, "color": "#000000"},
        "legend": {"show": True, "hPosition": "center", "vPosition": "bottom", "orient": "horizontal",
                   "icon": "circle", "color": "#000000", "fontSize": 12},
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
    "style": {"rotate": 0, "opacity": 1, "width": 1580, "height": 700, "left": 10, "top": 10},
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
    "width": 1600, "height": 900, "selfAdaption": True, "auxiliaryMatrix": True,
    "openCommonStyle": True,
    "panel": {"themeColor": "light", "color": "#f5f6f7", "imageUrl": "", "borderRadius": 0},
    "dashboard": {}
}, separators=(',', ':'))

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
    "contentId": str(dv_data.get('contentId', '0')),
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
        
        # Test data query
        print(f"\n=== Testing data query ===")
        query = {
            "type": "table-normal",
            "tableId": str(ds_id),
            "xAxis": x_axis,
            "xAxisExt": [],
            "yAxis": y_axis,
            "yAxisExt": [],
            "extStack": [], "extBubble": [], "extLabel": [], "extTooltip": [],
            "customFilter": custom_filter,
            "drill": False,
            "drillFields": [],
            "drillFilters": [],
            "senior": chart_view['senior'],
            "resultCount": 100,
            "resultMode": "custom",
            "chartExtRequest": {"user": 1, "filter": [], "drill": [], "queryFrom": "panel", "resultCount": 100, "resultMode": "custom"}
        }
        
        start = time.time()
        r_data = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=query, timeout=300)
        elapsed = time.time() - start
        resp_data = r_data.json()
        code = resp_data.get('code', -1)
        print(f"Code: {code}, Time: {elapsed:.1f}s")
        
        if code == 0:
            data = resp_data.get('data', {})
            table_data = data.get('data', {})
            rows = table_data.get('tableRow', [])
            fields = table_data.get('fields', [])
            print(f"Fields: {len(fields)}, Rows: {len(rows)}")
            
            if rows:
                print("Sample (first 3):")
                for row in rows[:3]:
                    print(f"  {json.dumps(row, ensure_ascii=False)[:300]}")
        else:
            print(f"Error: {str(resp_data.get('msg',''))[:300]}")
else:
    print(f"Error: {r.text[:500]}")

print(f"\nPreview: {base}/#/preview/{panel_id}")
print(f"Edit:    {base}/#/dvCanvas?dvId={panel_id}&opt=edit")
