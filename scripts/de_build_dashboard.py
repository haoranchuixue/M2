"""Build DSP Report dashboard with correct chart structure based on reference."""
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

dashboard_id = 1236050016221663232
dataset_id = 1236046190513098752

# Get dataset fields
r = requests.post(f'{base}/de2api/datasetTree/details/{dataset_id}', headers=headers, json={}, timeout=30)
all_fields = r.json()['data']['allFields']
print(f"Dataset has {len(all_fields)} fields")

dim_fields = [f for f in all_fields if f['groupType'] == 'd']
metric_fields = [f for f in all_fields if f['groupType'] == 'q']
print(f"  Dimensions: {len(dim_fields)}, Metrics: {len(metric_fields)}")

def make_field(f, summary=None):
    """Build a field entry matching the reference structure."""
    field = {
        "id": f['id'],
        "datasourceId": None,
        "datasetTableId": None,
        "datasetGroupId": str(dataset_id),
        "chartId": None,
        "originName": f['originName'],
        "name": f['name'],
        "dbFieldName": None,
        "description": None,
        "dataeaseName": f['dataeaseName'],
        "groupType": f['groupType'],
        "type": f['type'],
        "precision": None,
        "scale": None,
        "deType": f['deType'],
        "deExtractType": f.get('deExtractType', 0),
        "extField": 0,
        "checked": True,
        "columnIndex": None,
        "lastSyncTime": None,
        "dateFormat": None,
        "dateFormatType": None,
        "fieldShortName": f['fieldShortName'],
        "groupList": None,
        "otherGroup": None,
        "desensitized": None,
        "orderChecked": None,
        "params": None,
        "summary": summary or "count",
        "sort": "none",
        "dateStyle": "y_M_d",
        "datePattern": "date_sub",
        "dateShowFormat": None,
        "chartType": "bar",
        "compareCalc": {
            "type": "none",
            "resultData": "percent",
            "field": None,
            "custom": None
        },
        "logic": None,
        "filterType": None,
        "index": None,
        "formatterCfg": {
            "type": "auto",
            "unitLanguage": "ch",
            "unit": 1,
            "suffix": "",
            "decimalCount": 2,
            "thousandSeparator": True
        },
        "chartShowName": None,
        "filter": [],
        "customSort": None,
        "busiType": None,
        "hide": False,
        "field": None,
        "agg": False
    }
    return field

# Put all fields as dimension columns in the table
x_axis = []
for f in all_fields:
    x_axis.append(make_field(f))

chart_id = str(int(time.time() * 1000))

chart_view = {
    "id": chart_id,
    "title": "DSP Report",
    "sceneId": str(dashboard_id),
    "tableId": str(dataset_id),
    "type": "table-normal",
    "render": "antv",
    "resultCount": 1000,
    "resultMode": "all",
    "extStack": [],
    "extBubble": [],
    "extLabel": [],
    "extTooltip": [],
    "customAttr": {
        "basicStyle": {
            "alpha": 100,
            "tableBorderColor": "#E6E7E4",
            "tableScrollBarColor": "rgba(0,0,0,0.15)",
            "tableColumnMode": "adapt",
            "tableColumnWidth": 100,
            "tablePageMode": "page",
            "tablePageSize": 20,
            "gaugeStyle": "default",
            "colorScheme": "default",
            "colors": ["#1E90FF","#90EE90","#00CED1","#E2BD84","#7A90E0","#3BA272","#2BE7FF","#0A8ADA","#FFD700"],
            "mapVendor": "amap",
            "gradient": True,
            "lineWidth": 2,
            "lineSymbol": "circle",
            "lineSymbolSize": 4,
            "lineSmooth": True,
            "barDefault": True,
            "barWidth": 40,
            "barGap": 0.4,
            "lineType": "solid",
            "scatterSymbol": "circle",
            "scatterSymbolSize": 8,
            "radarShape": "polygon",
            "mapStyle": "normal",
            "areaBorderColor": "#303133",
            "suspension": True,
            "areaBaseColor": "#FFFFFF",
            "mapSymbolOpacity": 0.7,
            "mapSymbolStrokeWidth": 2,
            "mapSymbol": "circle",
            "mapSymbolSize": 20,
            "radius": 100,
            "innerRadius": 60,
            "showZoom": True,
            "zoomButtonColor": "#aaa",
            "zoomBackground": "#fff",
            "tableLayoutMode": "grid",
            "calcTopN": False,
            "topN": 5,
            "topNLabel": "其他"
        },
        "misc": {
            "pieInnerRadius": 0, "pieOuterRadius": 80, "radarShape": "polygon", "radarSize": 80,
            "gaugeMinType": "fix", "gaugeMinField": {"id": "", "summary": ""}, "gaugeMin": 0,
            "gaugeMaxType": "fix", "gaugeMaxField": {"id": "", "summary": ""}, "gaugeMax": 100,
            "gaugeStartAngle": 225, "gaugeEndAngle": -45,
            "nameFontSize": 18, "valueFontSize": 18, "nameValueSpace": 10,
            "valueFontColor": "#5470c6", "valueFontFamily": "Microsoft YaHei",
            "valueFontIsBolder": False, "valueFontIsItalic": False, "valueLetterSpace": 0, "valueFontShadow": False,
            "showName": True, "nameFontColor": "#000000", "nameFontFamily": "Microsoft YaHei",
            "nameFontIsBolder": False, "nameFontIsItalic": False, "nameLetterSpace": "0", "nameFontShadow": False,
            "treemapWidth": 80, "treemapHeight": 80,
            "liquidMax": 100, "liquidMaxType": "fix", "liquidMaxField": {"id": "", "summary": ""},
            "liquidSize": 80, "liquidShape": "circle",
            "hPosition": "center", "vPosition": "center",
            "mapPitch": 0, "mapLineType": "arc", "mapLineWidth": 1, "mapLineAnimateDuration": 3,
            "mapLineGradient": False, "mapLineSourceColor": "#146C94", "mapLineTargetColor": "#576CBC",
            "wordSizeRange": [8, 32], "wordSpacing": 6
        },
        "label": {
            "show": False, "position": "top", "color": "#000000", "fontSize": 10, "formatter": "",
            "labelLine": {"show": True},
            "labelFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
            "reserveDecimalCount": 2, "labelShadow": False, "labelBgColor": "", "labelShadowColor": "",
            "quotaLabelFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
            "showDimension": True, "showQuota": False, "showProportion": True, "seriesLabelFormatter": []
        },
        "tooltip": {
            "show": True, "trigger": "item", "confine": True, "fontSize": 12, "color": "#000000",
            "tooltipFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True},
            "backgroundColor": "#FFFFFF", "seriesTooltipFormatter": []
        },
        "tableTotal": {
            "row": {
                "showGrandTotals": True, "showSubTotals": True, "reverseLayout": False, "reverseSubLayout": False,
                "label": "总计", "subLabel": "小计", "subTotalsDimensions": [],
                "calcTotals": {"aggregation": "SUM", "cfg": []},
                "calcSubTotals": {"aggregation": "SUM", "cfg": []},
                "totalSort": "none", "totalSortField": ""
            },
            "col": {
                "showGrandTotals": True, "showSubTotals": True, "reverseLayout": False, "reverseSubLayout": False,
                "label": "总计", "subLabel": "小计", "subTotalsDimensions": [],
                "calcTotals": {"aggregation": "SUM", "cfg": []},
                "calcSubTotals": {"aggregation": "SUM", "cfg": []},
                "totalSort": "none", "totalSortField": ""
            }
        },
        "tableHeader": {
            "indexLabel": "序号", "showIndex": False,
            "tableHeaderAlign": "center", "tableHeaderBgColor": "#F5F6F7",
            "tableHeaderFontColor": "#333333", "tableTitleFontSize": 12,
            "tableTitleHeight": 36, "tableHeaderSort": True,
            "showColTooltip": False, "showRowTooltip": False
        },
        "tableCell": {
            "tableFontColor": "#333333", "tableItemAlign": "left",
            "tableItemBgColor": "#ffffff", "tableItemFontSize": 12,
            "tableItemHeight": 36, "enableTableCrossBG": True,
            "tableItemSubBgColor": "#F8F8F9", "showTooltip": False
        },
        "map": {"id": "", "level": "world"},
        "indicator": {
            "show": True, "fontSize": 20, "color": "#5470C6ff",
            "hPosition": "center", "vPosition": "center",
            "isItalic": False, "isBolder": True, "fontFamily": "Microsoft YaHei",
            "letterSpace": 0, "fontShadow": False,
            "suffixEnable": True, "suffix": "", "suffixFontSize": 14,
            "suffixColor": "#5470C6ff", "suffixIsItalic": False, "suffixIsBolder": True,
            "suffixFontFamily": "Microsoft YaHei", "suffixLetterSpace": 0, "suffixFontShadow": False
        },
        "indicatorName": {
            "show": True, "fontSize": 18, "color": "#ffffffff",
            "isItalic": False, "isBolder": True, "fontFamily": "Microsoft YaHei",
            "letterSpace": 0, "fontShadow": False, "nameValueSpacing": 0
        }
    },
    "customAttrMobile": None,
    "customStyle": {
        "text": {
            "show": True, "fontSize": "18", "hPosition": "left", "vPosition": "top",
            "isItalic": False, "isBolder": False, "remarkShow": False, "remark": "",
            "fontFamily": "Microsoft YaHei", "letterSpace": "0", "fontShadow": False,
            "color": "#111111", "remarkBackgroundColor": "#ffffff"
        },
        "legend": {
            "show": True, "hPosition": "center", "vPosition": "bottom",
            "orient": "horizontal", "icon": "circle", "color": "#000000", "fontSize": 12
        },
        "xAxis": {
            "show": True, "position": "bottom", "name": "", "color": "#000000", "fontSize": 12,
            "axisLabel": {"show": True, "color": "#000000", "fontSize": 12, "rotate": 0, "formatter": "{value}"},
            "axisLine": {"show": True, "lineStyle": {"color": "#cccccc", "width": 1, "style": "solid"}},
            "splitLine": {"show": False, "lineStyle": {"color": "#CCCCCC", "width": 1, "style": "solid"}},
            "axisValue": {"auto": True, "min": 10, "max": 100, "split": 10, "splitCount": 10},
            "axisLabelFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True}
        },
        "yAxis": {
            "show": True, "position": "left", "name": "", "color": "#000000", "fontSize": 12,
            "axisLabel": {"show": True, "color": "#000000", "fontSize": 12, "rotate": 0, "formatter": "{value}"},
            "axisLine": {"show": False, "lineStyle": {"color": "#cccccc", "width": 1, "style": "solid"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#CCCCCC", "width": 1, "style": "solid"}},
            "axisValue": {"auto": True, "min": 10, "max": 100, "split": 10, "splitCount": 10},
            "axisLabelFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True}
        },
        "yAxisExt": {
            "show": True, "position": "right", "name": "", "color": "#000000", "fontSize": 12,
            "axisLabel": {"show": True, "color": "#000000", "fontSize": 12, "rotate": 0, "formatter": "{value}"},
            "axisLine": {"show": False, "lineStyle": {"color": "#cccccc", "width": 1, "style": "solid"}},
            "splitLine": {"show": True, "lineStyle": {"color": "#CCCCCC", "width": 1, "style": "solid"}},
            "axisValue": {"auto": True, "min": None, "max": None, "split": None, "splitCount": None},
            "axisLabelFormatter": {"type": "auto", "unit": 1, "suffix": "", "decimalCount": 2, "thousandSeparator": True}
        },
        "misc": {
            "showName": False, "color": "#000000", "fontSize": 12, "axisColor": "#999", "splitNumber": 5,
            "axisLine": {"show": True, "lineStyle": {"color": "#CCCCCC", "width": 1, "type": "solid"}},
            "axisTick": {"show": False, "length": 5, "lineStyle": {"color": "#000000", "width": 1, "type": "solid"}},
            "axisLabel": {"show": False, "rotate": 0, "margin": 8, "color": "#000000", "fontSize": "12", "formatter": "{value}"},
            "splitLine": {"show": True, "lineStyle": {"color": "#CCCCCC", "width": 1, "type": "solid"}},
            "splitArea": {"show": True}
        }
    },
    "customStyleMobile": None,
    "customFilter": {"logic": None, "items": None},
    "drillFields": [],
    "senior": {
        "functionCfg": {
            "sliderShow": False, "sliderRange": [0, 10],
            "sliderBg": "#FFFFFF", "sliderFillBg": "#BCD6F1", "sliderTextColor": "#999999",
            "emptyDataStrategy": "breakLine", "emptyDataFieldCtrl": []
        },
        "assistLineCfg": {"enable": False, "assistLine": []},
        "threshold": {
            "enable": False, "gaugeThreshold": "",
            "labelThreshold": [], "tableThreshold": [], "textLabelThreshold": []
        },
        "scrollCfg": {"open": False, "row": 1, "interval": 2000, "step": 50},
        "areaMapping": {}
    },
    "createBy": None,
    "createTime": None,
    "updateTime": None,
    "snapshot": None,
    "stylePriority": "panel",
    "chartType": "private",
    "isPlugin": None,
    "dataFrom": "dataset",
    "viewFields": [],
    "refreshViewEnable": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
    "linkageActive": False,
    "jumpActive": False,
    "aggregate": None,
    "flowMapStartName": [],
    "flowMapEndName": [],
    "calParams": [],
    "extColor": [],
    "sortPriority": [],
    "data": None,
    "privileges": None,
    "isLeaf": None,
    "pid": None,
    "sql": None,
    "drill": False,
    "drillFilters": None,
    "position": None,
    "totalPage": 0,
    "totalItems": 0,
    "datasetMode": 0,
    "datasourceType": None,
    "chartExtRequest": None,
    "isExcelExport": False,
    "exportDatasetOriginData": False,
    "cache": False,
    "sourceTableId": None,
    "downloadType": None,
    "xAxis": x_axis,
    "xAxisExt": [],
    "yAxis": [],
    "yAxisExt": []
}

# Build component matching reference structure
component = {
    "animations": [],
    "canvasId": "canvas-main",
    "events": {},
    "groupStyle": {},
    "isLock": False,
    "isShow": True,
    "collapseName": ["position", "background", "style", "picture"],
    "linkage": {
        "duration": 0,
        "data": [{"id": "", "label": "", "event": "", "style": [{"key": "", "value": ""}]}]
    },
    "component": "UserView",
    "name": "表格",
    "label": "DSP Report",
    "propValue": {"innerType": "table-normal"},
    "icon": "bar",
    "innerType": "table-normal",
    "editing": False,
    "x": 1,
    "y": 1,
    "sizeX": 72,
    "sizeY": 28,
    "style": {
        "rotate": 0,
        "opacity": 1,
        "width": 1880,
        "height": 700,
        "left": 10,
        "top": 10
    },
    "matrixStyle": {},
    "commonBackground": {
        "backgroundColorSelect": True,
        "backgroundImageEnable": False,
        "backgroundType": "color",
        "innerImage": "",
        "outerImage": "",
        "innerPadding": 0,
        "borderRadius": 5,
        "backgroundColor": "rgba(255, 255, 255, 1)",
        "innerImageColor": ""
    },
    "state": "ready",
    "render": "custom",
    "id": chart_id,
    "_dragId": 0,
    "show": True,
    "linkageFilters": [],
    "canvasActive": False,
    "maintainRadio": False,
    "aspectRatio": 1,
    "actionSelection": {"linkageActive": "custom"}
}

# Get current dashboard data to preserve version
r_find = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                      json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
cur_data = r_find.json().get('data', {})
cur_version = cur_data.get('version', 3)
print(f"Current version: {cur_version}")

update_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": json.dumps([component]),
    "canvasStyleData": json.dumps({
        "width": 1920,
        "height": 1080,
        "selfAdaption": True,
        "auxiliaryMatrix": True,
        "openCommonStyle": True,
        "panel": {
            "themeColor": "light",
            "color": "#f5f6f7",
            "imageUrl": "",
            "borderRadius": 0
        },
        "dashboard": {}
    }),
    "canvasViewInfo": {chart_id: chart_view},
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": cur_data.get('contentId', '0'),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0,
}

print(f"\n=== Updating dashboard with corrected chart structure ===")
print(f"Chart ID: {chart_id}")
print(f"Fields in xAxis: {len(x_axis)}")

r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                  headers=headers, json=update_payload, timeout=60)
print(f"HTTP Status: {r.status_code}")

if r.status_code == 200:
    resp = r.json()
    code = resp.get('code')
    msg = resp.get('msg') or ''
    print(f"Code: {code}, Msg: {msg[:300]}")
    
    if code == 0:
        print("\n*** Dashboard updated successfully! ***")
        
        # Verify
        verify = requests.post(f'{base}/de2api/dataVisualization/findById',
                              headers=headers,
                              json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"},
                              timeout=30)
        v_data = verify.json().get('data', {})
        v_views = v_data.get('canvasViewInfo', {})
        v_comps = json.loads(v_data.get('componentData', '[]'))
        print(f"  Components: {len(v_comps)}")
        print(f"  Views: {len(v_views)}")
        
        if v_views:
            for vid, vdata in v_views.items():
                print(f"  View '{vid}': type={vdata.get('type')}, title={vdata.get('title')}")
                print(f"    xAxis fields: {len(vdata.get('xAxis', []))}")
                print(f"    yAxis fields: {len(vdata.get('yAxis', []))}")
            
            # Publish
            print("\n=== Publishing dashboard ===")
            pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                               headers=headers,
                               json={"id": dashboard_id, "type": "dashboard",
                                     "busiFlag": "dashboard", "status": 1, "pid": 0},
                               timeout=30)
            print(f"Publish: {pub.status_code}, {pub.text[:200]}")
            
            print(f"\n{'='*60}")
            print(f"Dashboard ready at: {base}/#/panel/index?dvId={dashboard_id}")
            print(f"{'='*60}")
        else:
            print("\n  WARNING: Views still empty after update!")
    else:
        print(f"Error: {msg}")
else:
    print(f"Error: {r.text[:500]}")
