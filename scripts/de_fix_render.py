"""Fix the component render mode and propValue to match working tea dashboard."""
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
panel_id = "1236050016221663232"

# Get dataset fields
all_fields = api(f'/datasetTree/details/{ds_id}')['data']['allFields']
field_map = {f['originName']: f for f in all_fields}

# Get current state
snap = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dashboard", "resourceTable": "snapshot"})
snap_data = snap.get('data', {})
cur_version = snap_data.get('version') or 1
print(f"Version: {cur_version}")

# Get the existing chart view
cvi = snap_data.get('canvasViewInfo', {}) or {}
old_chart_id = list(cvi.keys())[0] if cvi else None
old_chart = cvi.get(old_chart_id) if old_chart_id else None

if old_chart:
    print(f"Existing chart: {old_chart_id}, type={old_chart.get('type')}, x={len(old_chart.get('xAxis',[]))}, y={len(old_chart.get('yAxis',[]))}")
    chart_id = old_chart_id
    chart_view = old_chart
else:
    print("No existing chart view found - will use saved chart data from earlier")
    # The chart view data should still be in the snapshot
    chart_id = str(int(time.time() * 1000))
    
    def make_field(f, display_name=None, group_type=None, summary=""):
        return {
            "id": f['id'], "datasetTableId": f.get('datasetTableId'),
            "datasetGroupId": str(ds_id), "datasourceId": f.get('datasourceId'),
            "chartType": "table-normal", "originName": f['originName'],
            "name": display_name or f['originName'], "dataeaseName": f.get('dataeaseName'),
            "type": f['type'], "deType": f.get('deType', 0),
            "deExtractType": f.get('deExtractType', 0), "extField": 0,
            "groupType": group_type, "checked": True, "columnIndex": f.get('columnIndex', 0),
            "sort": "none", "summary": summary, "fieldShortName": f.get('fieldShortName'),
            "formatterCfg": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
            "filter": [], "hide": False, "agg": False
        }
    
    dims = [('report_date', 'Date'), ('adv_id', 'Adv ID'), ('adv_name', 'Adv Name'), ('country', 'Country')]
    metrics = [('response','Response','sum'),('win','Wins','sum'),('imp','Impressions','sum'),('click','Click','sum'),
               ('cost','Cost','sum'),('revenue','Revenue','sum'),('event10','Event10','sum'),
               ('roi','ROI','avg'),('win_rate','Win Rate','avg'),('cpm','CPM','avg'),('ctr','CTR','avg')]
    
    x_axis = [make_field(field_map[o], d, 'd') for o, d in dims]
    y_axis = [make_field(field_map[o], d, 'q', s) for o, d, s in metrics]
    date_f = field_map['report_date']
    
    chart_view = {
        "id": chart_id, "title": "DSP Report", "sceneId": str(panel_id),
        "tableId": str(ds_id), "type": "table-normal", "render": "antv",
        "resultCount": 1000, "resultMode": "custom",
        "extStack": [], "extBubble": [], "extLabel": [], "extTooltip": [],
        "customAttr": {"basicStyle": {"alpha": 100, "tableBorderColor": "#E6E7E4",
            "tableScrollBarColor": "rgba(0,0,0,0.15)", "tableColumnMode": "adapt",
            "tablePageMode": "pull", "tablePageSize": 20},
            "tableHeader": {"showIndex": False, "tableHeaderAlign": "left",
                "tableHeaderBgColor": "#F5F6F7", "tableHeaderFontColor": "#333333",
                "tableTitleFontSize": 12, "tableTitleHeight": 36},
            "tableCell": {"tableFontColor": "#333333", "tableItemAlign": "left", "tableItemBgColor": "#ffffff",
                "tableItemFontSize": 12, "tableItemHeight": 36, "enableTableCrossBG": True,
                "tableItemSubBgColor": "#F8F8F9"},
            "misc": {"showName": True, "nameFontSize": 16, "nameFontColor": "#333333"},
            "label": {"show": False}, "tooltip": {"show": True}},
        "customStyle": {"text": {"show": True, "fontSize": "14", "color": "#333333"}, "misc": {"showName": False}},
        "customFilter": {"logic": "and", "items": [{"type": "field", "fieldId": int(date_f['id']),
            "filterType": "logic", "term": "ge", "value": "2026-03-27", "filterTypeTime": "dateValue"}], "filterType": "logic"},
        "drillFields": [], "senior": {"functionCfg": {"sliderShow": False}},
        "stylePriority": "panel", "dataFrom": "dataset",
        "linkageActive": False, "jumpActive": False, "drill": False,
        "xAxis": x_axis, "xAxisExt": [], "yAxis": y_axis, "yAxisExt": []
    }

# Build component matching tea dashboard structure EXACTLY
component = {
    "_dragId": 0,
    "actionSelection": {"linkageActive": "custom"},
    "animations": [],
    "aspectRatio": 1,
    "canvasActive": False,
    "canvasId": "canvas-main",
    "collapseName": ["position", "background", "style"],
    "commonBackground": {
        "backgroundColorSelect": True, "backgroundImageEnable": False, "backgroundType": "color",
        "innerImage": "", "outerImage": "", "innerPadding": 0, "borderRadius": 5,
        "backgroundColor": "rgba(255, 255, 255, 1)"
    },
    "component": "UserView",
    "editing": False,
    "events": {},
    "groupStyle": {},
    "icon": "",
    "id": chart_id,
    "innerType": "table-normal",
    "isLock": False,
    "isShow": True,
    "label": "明细表",
    "linkage": {"duration": 0},
    "linkageFilters": [],
    "maintainRadio": False,
    "matrixStyle": {},
    "name": "DSP Report",
    "propValue": {"textValue": ""},
    "render": "antv",
    "show": True,
    "sizeX": 72,
    "sizeY": 28,
    "state": "ready",
    "style": {"rotate": 0, "opacity": 1, "width": 1880, "height": 700, "left": 10, "top": 10},
    "x": 1,
    "y": 1
}

compact_comp = json.dumps([component], separators=(',', ':'), ensure_ascii=False)
compact_style = json.dumps({
    "width": 1920, "height": 1080, "selfAdaption": True, "auxiliaryMatrix": True,
    "openCommonStyle": True,
    "panel": {"themeColor": "light", "color": "#f5f6f7", "imageUrl": "", "borderRadius": 0},
    "dashboard": {"gap": "yes", "gapSize": 5, "resultMode": "all", "resultCount": 1000, "themeColor": "light"}
}, separators=(',', ':'))

assert f'"id":"{chart_id}"' in compact_comp
print(f"Chart ID: {chart_id}, render: antv, propValue: textValue")

update_payload = {
    "id": panel_id,
    "name": "DSP Report",
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

print(f"\n=== Updating ===")
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"HTTP: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    if resp.get('code') == 0:
        pub = api('/dataVisualization/updatePublishStatus',
                   {"id": panel_id, "type": "dashboard", "busiFlag": "dashboard", "status": 1, "pid": 0})
        print(f"Publish: {pub.get('code')}")
        
        # Take screenshot
        print("\n=== Screenshot ===")
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            pg = br.new_page(viewport={"width": 1920, "height": 1080})
            pg.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
            pg.wait_for_load_state('networkidle', timeout=30000)
            pg.wait_for_selector('input', timeout=10000)
            ins = pg.query_selector_all('input')
            ins[0].fill('admin')
            ins[1].fill('DataEase@123456')
            pg.query_selector('button').click()
            time.sleep(5)
            pg.wait_for_load_state('networkidle', timeout=30000)
            
            pg.goto(f'{base}/#/panel/index', timeout=60000)
            time.sleep(5)
            
            # Expand folder and click DSP Report
            elements = pg.query_selector_all('span')
            for el in elements:
                text = el.text_content()
                if text and text.strip() == 'DSP Report':
                    el.click()
                    break
            
            print("Waiting 45s for data...")
            time.sleep(45)
            pg.screenshot(path='d:/Projects/m2/scripts/ss_fixed.png')
            print("Screenshot saved: ss_fixed.png")
            br.close()
    else:
        print(f"Error: {resp.get('msg', '')[:300]}")
else:
    print(f"Error: {r.text[:500]}")
