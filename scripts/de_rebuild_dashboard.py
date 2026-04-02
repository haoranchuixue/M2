"""
Rebuild ReportCenter DSP Report dashboard with correct dataset.

The chart was referencing a deleted dataset (1236079082777743360).
The actual dataset is 'DSP Report Data' (1236046190513098752).

This script:
1. Fetches fields from the correct dataset
2. Rebuilds the chart view (table-normal) with proper field bindings
3. Rebuilds VQuery filters: Time Range (date picker) + Source (dropdown)
4. Updates and publishes the dashboard
"""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
PANEL_ID = '1236081407923720192'
DS_ID = '1236046190513098752'


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

# ─── Step 1: Fetch dataset fields ───
print('=== Step 1: Fetch dataset fields ===')
r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
ds_data = r.json()['data']
all_fields = ds_data['allFields']
field_map = {f['originName']: f for f in all_fields}
print(f'Dataset has {len(all_fields)} fields:')
for f in all_fields:
    print(f'  {f["originName"]:30s} type={f["type"]:10s} id={f["id"]}')

# ─── Step 2: Get current dashboard version ───
print('\n=== Step 2: Get current dashboard ===')
r2 = requests.post(
    f'{base}/de2api/dataVisualization/findById',
    headers=headers,
    json={'id': PANEL_ID, 'busiFlag': 'dataV', 'resourceTable': 'snapshot'},
    timeout=30,
)
dv = r2.json().get('data') or {}
cur_version = dv.get('version') or 1
old_canvas = dv.get('canvasStyleData', '{}')
if isinstance(old_canvas, str):
    old_canvas = json.loads(old_canvas)
print(f'Current version: {cur_version}')

# ─── Step 3: Build chart view fields ───

def make_field(origin_name, display_name, group_type, summary=''):
    f = field_map.get(origin_name)
    if not f:
        print(f'  WARNING: field {origin_name!r} not in dataset')
        return None
    return {
        'id': f['id'],
        'datasourceId': f.get('datasourceId'),
        'datasetTableId': f.get('datasetTableId'),
        'datasetGroupId': str(DS_ID),
        'chartId': None,
        'originName': f['originName'],
        'name': display_name,
        'dbFieldName': f.get('dbFieldName'),
        'dataeaseName': f.get('dataeaseName'),
        'groupType': group_type,
        'type': f['type'],
        'deType': f.get('deType', 0),
        'deExtractType': f.get('deExtractType', 0),
        'extField': f.get('extField', 0),
        'checked': True,
        'columnIndex': f.get('columnIndex', 0),
        'lastSyncTime': f.get('lastSyncTime'),
        'dateFormat': f.get('dateFormat'),
        'dateFormatType': f.get('dateFormatType'),
        'fieldShortName': f.get('fieldShortName'),
        'chartType': 'table-normal',
        'summary': summary,
        'sort': 'none',
        'formatterCfg': {
            'type': 'auto', 'unitLanguage': 'ch', 'unit': 1,
            'suffix': '', 'decimalCount': 2, 'thousandSeparator': True,
        },
        'filter': [],
        'customSort': None,
        'busiType': None,
        'hide': False,
        'field': None,
        'agg': False,
    }


# Dimensions - start with Date only (like the screenshot aggregation).
# Other dims are available in the dataset and can be toggled in the UI.
dims = [
    ('create_date', 'Date'),
]

# Metrics (actual column names from dataset)
metrics = [
    ('request_count', 'Request', 'sum'),
    ('request_filter_count', 'TotalRequest', 'sum'),
    ('response_count', 'Response', 'sum'),
    ('win_count', 'Wins', 'sum'),
    ('bid_price_total', 'BidPrice', 'sum'),
    ('imp_count', 'Impressions', 'sum'),
    ('clean_imp_count', 'Clean Impressions', 'sum'),
    ('cheat_imp_count', 'Cheat Impressions', 'sum'),
    ('exceed_imp_count', 'Exceed Impressions', 'sum'),
    ('click_count', 'Click', 'sum'),
    ('clean_click_count', 'Clean Clicks', 'sum'),
    ('cheat_click_count', 'Cheat Clicks', 'sum'),
    ('price_total', 'Price Total', 'sum'),
]

x_axis = [item for origin, display in dims if (item := make_field(origin, display, 'd'))]
y_axis = [item for origin, display, agg in metrics if (item := make_field(origin, display, 'q', agg))]
print(f'\nxAxis: {len(x_axis)} fields, yAxis: {len(y_axis)} fields')

date_field = field_map.get('create_date')
source_field = field_map.get('source')

# ─── Step 4: Build chart view ───
chart_id = str(int(time.time() * 1000))

chart_view = {
    'id': chart_id,
    'title': 'DSP Report',
    'sceneId': str(PANEL_ID),
    'tableId': str(DS_ID),
    'type': 'table-normal',
    'render': 'antv',
    'resultCount': 100,
    'resultMode': 'custom',
    'xAxis': x_axis,
    'xAxisExt': [],
    'yAxis': y_axis,
    'yAxisExt': [],
    'extStack': [],
    'extBubble': [],
    'extLabel': [],
    'extTooltip': [],
    'extColor': [],
    'sortPriority': [],
    'customAttr': {
        'basicStyle': {
            'alpha': 100, 'tableBorderColor': '#E6E7E4',
            'tableScrollBarColor': 'rgba(0,0,0,0.15)', 'tableColumnMode': 'adapt',
            'tableColumnWidth': 100, 'tablePageMode': 'pull', 'tablePageSize': 20,
            'colorScheme': 'default',
            'colors': ['#1E90FF', '#90EE90', '#00CED1', '#E2BD84', '#7A90E0',
                        '#3BA272', '#2BE7FF', '#0A8ADA', '#FFD700'],
            'gradient': True, 'lineWidth': 2, 'tableLayoutMode': 'grid',
        },
        'tableHeader': {
            'showIndex': False, 'indexLabel': '序号', 'tableHeaderAlign': 'left',
            'tableHeaderBgColor': '#F5F6F7', 'tableHeaderFontColor': '#333333',
            'tableTitleFontSize': 12, 'tableTitleHeight': 36, 'tableHeaderSort': True,
        },
        'tableCell': {
            'tableFontColor': '#333333', 'tableItemAlign': 'left',
            'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
            'tableItemHeight': 36, 'enableTableCrossBG': True,
            'tableItemSubBgColor': '#F8F8F9',
        },
        'misc': {'showName': True, 'nameFontSize': 16, 'nameFontColor': '#333333'},
        'label': {'show': False},
        'tooltip': {'show': True},
    },
    'customStyle': {
        'text': {
            'show': True, 'fontSize': '14', 'hPosition': 'left', 'vPosition': 'top',
            'isItalic': False, 'isBolder': True, 'remarkShow': False, 'remark': '',
            'fontFamily': 'Microsoft YaHei', 'letterSpace': '0', 'fontShadow': False,
            'color': '#333333',
        },
        'legend': {
            'show': True, 'hPosition': 'center', 'vPosition': 'bottom',
            'orient': 'horizontal', 'icon': 'circle', 'color': '#333333', 'fontSize': 12,
        },
    },
    'customFilter': {
        'logic': 'and',
        'items': [
            {
                'type': 'field',
                'fieldId': int(date_field['id']),
                'filterType': 'logic',
                'term': 'eq',
                'value': '2026-03-29',
                'filterTypeTime': 'dateValue',
            },
            {
                'type': 'field',
                'fieldId': int(source_field['id']),
                'filterType': 'logic',
                'term': 'gt',
                'value': '2',
            },
        ],
        'filterType': 'logic',
    },
    'drillFields': [],
    'senior': {
        'functionCfg': {'sliderShow': False, 'emptyDataStrategy': 'breakLine'},
        'assistLineCfg': {'enable': False},
        'threshold': {'enable': False},
        'scrollCfg': {'open': False, 'row': 1, 'interval': 2000, 'step': 50},
    },
    'stylePriority': 'panel',
    'chartType': 'private',
    'dataFrom': 'dataset',
    'refreshViewEnable': False,
    'refreshUnit': 'minute',
    'refreshTime': 5,
    'linkageActive': False,
    'jumpActive': False,
    'drill': False,
    'datasetMode': 0,
    'isExcelExport': False,
}

# ─── Step 5: Build query filter components ───
filter_id = str(int(time.time() * 1000) + 1)
source_filter_id = str(int(time.time() * 1000) + 2)

# Date Range filter (VQuery with dict propValue - legacy format that works on this instance)
date_filter_comp = {
    'animations': [],
    'canvasId': 'canvas-main',
    'events': {},
    'groupStyle': {},
    'isLock': False,
    'isShow': True,
    'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'VQuery',
    'name': 'Time Range',
    'label': 'Time Range',
    'propValue': {
        'innerType': 'VQueryDatePicker',
        'parametersType': 'dateRange',
        'conditionType': 0,
        'conditionValueOperator': 'between',
        'defaultConditionValueOperatorF': 'between',
        'conditionValueOperatorF': 'between',
        'defaultRelativeToCurrent': 'custom',
        'relativeToCurrent': 'custom',
        'relativeToCurrentType': 'year',
        'required': False,
        'defaultValue': ['2026-03-29', '2026-03-29'],
        'selectValue': ['2026-03-29', '2026-03-29'],
        'checkedFields': [{
            'datasetId': str(DS_ID),
            'id': date_field['id'],
            'originName': date_field['originName'],
            'name': 'Date',
            'deType': date_field.get('deType', 1),
            'groupType': 'd',
            'checked': True,
        }],
        'checkedFieldsMap': {
            str(DS_ID): [{
                'datasetId': str(DS_ID),
                'id': date_field['id'],
                'originName': date_field['originName'],
                'name': 'Date',
                'deType': date_field.get('deType', 1),
                'groupType': 'd',
                'checked': True,
            }],
        },
        'displayType': 'new',
        'timeGranularity': 'date',
        'timeGranularityMultiple': 'daterange',
        'showTitle': True,
        'title': 'Time Range',
        'titleColor': '#333333',
        'titleFontSize': 14,
        'parameters': [],
        'visible': True,
        'id': filter_id,
    },
    'icon': '',
    'innerType': 'VQueryDatePicker',
    'editing': False,
    'x': 1, 'y': 1, 'sizeX': 18, 'sizeY': 2,
    'style': {'rotate': 0, 'opacity': 1, 'width': 400, 'height': 50, 'left': 10, 'top': 10},
    'matrixStyle': {},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'innerImage': '', 'outerImage': '',
        'innerPadding': 0, 'borderRadius': 5,
        'backgroundColor': 'rgba(255, 255, 255, 1)',
    },
    'state': 'ready',
    'render': 'custom',
    'id': filter_id,
    '_dragId': 0,
    'show': True,
    'mobileSelected': False,
    'mobileStyle': {'style': {'width': 375, 'height': 50, 'left': 0, 'top': 0}},
    'sourceViewId': None,
    'linkageFilters': [],
    'canvasActive': False,
    'maintainRadio': False,
    'aspectRatio': 1,
    'actionSelection': {'linkageActive': 'custom'},
}

# Source dropdown filter
source_condition = {
    'id': str(int(time.time() * 1000) + 7),
    'name': 'Source',
    'showError': True,
    'timeGranularity': 'date',
    'timeGranularityMultiple': 'datetimerange',
    'field': {
        'id': source_field['id'],
        'type': source_field['type'],
        'name': 'Source',
        'deType': source_field.get('deType', 0),
    },
    'displayId': source_field['id'],
    'sortId': '',
    'sort': 'asc',
    'defaultMapValue': [],
    'mapValue': [],
    'conditionType': 0,
    'conditionValueOperatorF': 'eq',
    'conditionValueF': '',
    'conditionValueOperatorS': 'like',
    'conditionValueS': '',
    'defaultConditionValueOperatorF': 'eq',
    'defaultConditionValueF': '',
    'defaultConditionValueOperatorS': 'like',
    'defaultConditionValueS': '',
    'timeType': 'fixed',
    'relativeToCurrent': 'custom',
    'required': False,
    'timeNum': 0,
    'relativeToCurrentType': 'date',
    'around': 'f',
    'parametersStart': None,
    'parametersEnd': None,
    'arbitraryTime': None,
    'timeNumRange': 0,
    'relativeToCurrentTypeRange': 'date',
    'aroundRange': 'f',
    'arbitraryTimeRange': None,
    'auto': False,
    'defaultValue': None,
    'selectValue': None,
    'optionValueSource': 0,
    'valueSource': [],
    'dataset': {'id': str(DS_ID), 'name': '', 'fields': []},
    'visible': True,
    'defaultValueCheck': False,
    'multiple': False,
    'displayType': '0',
    'checkedFields': [str(DS_ID)],
    'parameters': [],
    'parametersCheck': False,
    'parametersList': [],
    'checkedFieldsMap': {
        str(DS_ID): [{
            'datasetId': str(DS_ID),
            'id': source_field['id'],
            'originName': source_field['originName'],
            'name': 'Source',
            'deType': source_field.get('deType', 0),
            'groupType': 'd',
            'checked': True,
        }],
    },
}

source_filter_comp = {
    'animations': [],
    'canvasId': 'canvas-main',
    'events': {},
    'groupStyle': {},
    'isLock': False,
    'isShow': True,
    'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'VQuery',
    'name': 'Source',
    'label': 'Source',
    'propValue': [source_condition],
    'icon': '',
    'innerType': 'VQuery',
    'editing': False,
    'x': 20, 'y': 1, 'sizeX': 18, 'sizeY': 2,
    'style': {'rotate': 0, 'opacity': 1, 'width': 400, 'height': 50, 'left': 420, 'top': 10},
    'matrixStyle': {},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'innerImage': '', 'outerImage': '',
        'innerPadding': 0, 'borderRadius': 5,
        'backgroundColor': 'rgba(255, 255, 255, 1)',
    },
    'state': 'ready',
    'render': 'custom',
    'id': source_filter_id,
    '_dragId': 0,
    'show': True,
    'mobileSelected': False,
    'mobileStyle': {'style': {'width': 375, 'height': 50, 'left': 0, 'top': 0}},
    'sourceViewId': None,
    'linkageFilters': [],
    'canvasActive': False,
    'maintainRadio': False,
    'aspectRatio': 1,
    'actionSelection': {'linkageActive': 'custom'},
}

# Chart table component
chart_comp = {
    'animations': [],
    'canvasId': 'canvas-main',
    'events': {},
    'groupStyle': {},
    'isLock': False,
    'isShow': True,
    'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'UserView',
    'name': 'DSP Report',
    'label': 'DSP Report',
    'propValue': {'innerType': 'table-normal'},
    'icon': 'bar',
    'innerType': 'table-normal',
    'editing': False,
    'x': 1, 'y': 4, 'sizeX': 72, 'sizeY': 26,
    'style': {'rotate': 0, 'opacity': 1, 'width': 1580, 'height': 650, 'left': 10, 'top': 60},
    'matrixStyle': {},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'innerImage': '', 'outerImage': '',
        'innerPadding': 0, 'borderRadius': 5,
        'backgroundColor': 'rgba(255, 255, 255, 1)',
    },
    'state': 'ready',
    'render': 'custom',
    'id': chart_id,
    '_dragId': 0,
    'show': True,
    'mobileSelected': False,
    'mobileStyle': {'style': {'width': 375, 'height': 200, 'left': 0, 'top': 0}},
    'sourceViewId': None,
    'linkageFilters': [],
    'canvasActive': False,
    'maintainRadio': False,
    'aspectRatio': 1,
    'actionSelection': {'linkageActive': 'custom'},
}

components = [date_filter_comp, source_filter_comp, chart_comp]
compact_comp = json.dumps(components, separators=(',', ':'), ensure_ascii=False)
compact_style = json.dumps(old_canvas, separators=(',', ':'))

assert f'"id":"{chart_id}"' in compact_comp

# ─── Step 6: Update canvas ───
print(f'\n=== Step 6: Update canvas (v{cur_version} -> v{cur_version + 1}) ===')
update_payload = {
    'id': PANEL_ID,
    'name': 'ReportCenter - DSP Report',
    'pid': 0,
    'type': 'dashboard',
    'busiFlag': 'dataV',
    'componentData': compact_comp,
    'canvasStyleData': compact_style,
    'canvasViewInfo': {chart_id: chart_view},
    'checkVersion': str(cur_version),
    'version': cur_version + 1,
    'contentId': str(dv.get('contentId', '0')),
    'status': 0,
    'mobileLayout': False,
    'selfWatermarkStatus': False,
    'extFlag': 0,
}

r3 = requests.post(
    f'{base}/de2api/dataVisualization/updateCanvas',
    headers=headers, json=update_payload, timeout=60,
)
print(f'updateCanvas: {r3.status_code}')
resp3 = r3.json()
print(f'Code: {resp3.get("code")}, Msg: {str(resp3.get("msg",""))[:200]}')

if resp3.get('code') != 0:
    print('FAILED to update canvas')
    sys.exit(1)

# Publish
print('\n=== Step 7: Publish ===')
r4 = requests.post(
    f'{base}/de2api/dataVisualization/updatePublishStatus',
    headers=headers,
    json={'id': PANEL_ID, 'type': 'dataV', 'busiFlag': 'dataV', 'status': 1, 'pid': 0},
    timeout=30,
)
print(f'Publish: code={r4.json().get("code")}')

# ─── Step 8: Verify chart data ───
print('\n=== Step 8: Verify chart data ===')
time.sleep(2)
token2 = get_fresh_token()
headers2 = {'x-de-token': token2, 'Content-Type': 'application/json'}
r5 = requests.post(f'{base}/de2api/chartData/getData', headers=headers2, json=chart_view, timeout=300)
resp5 = r5.json()
print(f'getData code: {resp5.get("code")}')
if resp5.get('code') == 0:
    rows = resp5.get('data', {}).get('tableRow', [])
    print(f'SUCCESS! {len(rows)} rows returned')
    if rows:
        print(f'First row sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
else:
    print(f'Error: {str(resp5.get("msg",""))[:300]}')

print(f'\nPreview: {base}/#/preview/{PANEL_ID}')
print(f'Edit:    {base}/#/dvCanvas?dvId={PANEL_ID}&opt=edit')
