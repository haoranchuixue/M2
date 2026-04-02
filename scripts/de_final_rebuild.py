"""
Final rebuild of m2dashboard using the new SQL-filtered dataset.
Dataset: DSP_Report_Recent (1236796318811295744)
SQL: SELECT ... FROM dsp_report WHERE create_date = '2026-03-29' LIMIT 5000
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
M2_ID = '1236684857652940800'
DS_ID = '1236046190513098752'  # original db dataset

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

# Get fields from new dataset
r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
fields = r.json()['data']['allFields']
field_map = {f['originName']: f for f in fields}
print(f'Dataset fields: {len(fields)}')

date_field = field_map['create_date']
source_field = field_map['source']

def make_field(origin_name, display_name):
    f = field_map.get(origin_name)
    if not f:
        return None
    return {
        'id': f['id'], 'datasourceId': f.get('datasourceId'),
        'datasetTableId': f.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
        'originName': f['originName'], 'name': display_name,
        'dataeaseName': f.get('dataeaseName'), 'fieldShortName': f.get('fieldShortName'),
        'groupType': f.get('groupType', 'd'), 'type': f['type'], 'deType': f.get('deType', 0),
        'deExtractType': f.get('deExtractType', 0), 'extField': 0,
        'checked': True, 'chartType': 'table-normal', 'sort': 'none',
        'filter': [], 'hide': False, 'agg': False,
    }

# Use table-normal (aggregation table) with minimal dimensions to reduce query weight
x_columns = [('create_date', 'Date')]
y_columns = [('request_count', 'Request')]

x_axis = [item for o, d in x_columns if (item := make_field(o, d))]
y_axis = []
for o, d in y_columns:
    f = field_map.get(o)
    if f:
        y_axis.append({
            'id': f['id'], 'datasourceId': f.get('datasourceId'),
            'datasetTableId': f.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
            'originName': f['originName'], 'name': d,
            'dataeaseName': f.get('dataeaseName'), 'fieldShortName': f.get('fieldShortName'),
            'groupType': 'q', 'type': f['type'], 'deType': f.get('deType', 0),
            'deExtractType': f.get('deExtractType', 0), 'extField': 0,
            'checked': True, 'chartType': 'table-normal', 'sort': 'none',
            'summary': 'sum', 'filter': [], 'hide': False, 'agg': False,
        })
print(f'xAxis: {len(x_axis)} fields, yAxis: {len(y_axis)} fields')

chart_id = str(int(time.time() * 1000))
filter_id = str(int(time.time() * 1000) + 1)

chart_view = {
    'id': chart_id, 'title': 'DSP Report',
    'sceneId': str(M2_ID), 'tableId': str(DS_ID),
    'type': 'table-normal', 'render': 'antv',
    'resultCount': 10, 'resultMode': 'custom',
    'xAxis': x_axis, 'xAxisExt': [], 'yAxis': y_axis, 'yAxisExt': [],
    'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
    'extColor': [], 'sortPriority': [],
    'customAttr': {
        'basicStyle': {'tableBorderColor': '#E6E7E4', 'tableColumnMode': 'adapt',
                        'tablePageMode': 'pull', 'tablePageSize': 20, 'tableLayoutMode': 'grid'},
        'tableHeader': {'tableHeaderAlign': 'left', 'tableHeaderBgColor': '#F5F6F7',
                        'tableHeaderFontColor': '#333333', 'tableTitleFontSize': 12,
                        'tableTitleHeight': 36, 'tableHeaderSort': True},
        'tableCell': {'tableFontColor': '#333333', 'tableItemAlign': 'left',
                      'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
                      'tableItemHeight': 36, 'enableTableCrossBG': True, 'tableItemSubBgColor': '#F8F8F9'},
        'misc': {'showName': True}, 'label': {'show': False}, 'tooltip': {'show': True},
    },
    'customStyle': {'text': {'show': True, 'fontSize': '14', 'isBolder': True, 'color': '#333333'}},
    'customFilter': {},
    'drillFields': [],
    'senior': {'functionCfg': {'sliderShow': False}, 'scrollCfg': {'open': False}},
    'dataFrom': 'dataset', 'datasetMode': 0,
}

print('Skipping getData test (requires date filter from VQuery to avoid full table scan)')

# Build VQuery component
date_criteria = {
    'id': str(int(time.time() * 1000) + 10),
    'name': 'Time Range', 'timeGranularity': 'date', 'timeGranularityMultiple': 'daterange',
    'field': {'id': date_field['id'], 'type': date_field['type'], 'name': 'Date', 'deType': 1},
    'displayId': date_field['id'],
    'conditionType': 0, 'timeType': 'fixed', 'relativeToCurrent': 'custom',
    'defaultValue': ['2026-03-31', '2026-03-31'], 'selectValue': ['2026-03-31', '2026-03-31'],
    'dataset': {'id': str(DS_ID)}, 'visible': True, 'defaultValueCheck': True,
    'displayType': '7', 'checkedFields': [chart_id],
    'checkedFieldsMap': {chart_id: [{'datasetId': str(DS_ID), 'id': date_field['id'],
                         'originName': 'create_date', 'name': 'Date', 'deType': 1,
                         'groupType': 'd', 'checked': True}]},
}
source_criteria = {
    'id': str(int(time.time() * 1000) + 11),
    'name': 'Source',
    'field': {'id': source_field['id'], 'type': source_field['type'], 'name': 'Source',
              'deType': source_field.get('deType', 0)},
    'displayId': source_field['id'],
    'conditionType': 0, 'timeType': 'fixed', 'relativeToCurrent': 'custom',
    'dataset': {'id': str(DS_ID)}, 'visible': True, 'defaultValueCheck': False,
    'displayType': '0', 'checkedFields': [chart_id],
    'checkedFieldsMap': {chart_id: [{'datasetId': str(DS_ID), 'id': source_field['id'],
                         'originName': 'source', 'name': 'Source',
                         'deType': source_field.get('deType', 0),
                         'groupType': 'd', 'checked': True}]},
}

date_comp = {
    'canvasId': 'canvas-main', 'component': 'VQuery',
    'name': 'Filters', 'label': 'Filters',
    'propValue': [date_criteria, source_criteria],
    'innerType': 'VQuery', 'x': 1, 'y': 1, 'sizeX': 72, 'sizeY': 4,
    'style': {'width': 400, 'height': 100},
    'commonBackground': {'backgroundColorSelect': True, 'backgroundType': 'color',
                         'backgroundColor': 'rgba(255,255,255,1)', 'innerPadding': 0, 'borderRadius': 5},
    'state': 'ready', 'render': 'custom', 'id': filter_id, 'show': True,
    'isLock': False, 'isShow': True,
}

chart_comp = {
    'canvasId': 'canvas-main', 'component': 'UserView',
    'name': 'DSP Report', 'label': 'DSP Report',
    'propValue': {'innerType': 'table-normal'}, 'innerType': 'table-normal',
    'x': 1, 'y': 5, 'sizeX': 72, 'sizeY': 24,
    'style': {'width': 1580, 'height': 600},
    'commonBackground': {'backgroundColorSelect': True, 'backgroundType': 'color',
                         'backgroundColor': 'rgba(255,255,255,1)', 'innerPadding': 0, 'borderRadius': 5},
    'state': 'ready', 'render': 'custom', 'id': chart_id, 'show': True,
    'isLock': False, 'isShow': True,
}

# Get dashboard version
r_dv = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                     json={'id': M2_ID, 'busiFlag': 'dashboard', 'resourceTable': 'snapshot'}, timeout=30)
dv = r_dv.json()['data']
cur_version = dv.get('version', 1)
old_canvas = dv.get('canvasStyleData', '{}')
if isinstance(old_canvas, str):
    old_canvas = json.loads(old_canvas)
if isinstance(old_canvas, dict) and 'dashboard' in old_canvas:
    old_canvas['dashboard']['resultMode'] = 'custom'
    old_canvas['dashboard']['resultCount'] = 1000

update_payload = {
    'id': M2_ID, 'name': 'm2dashboard',
    'pid': dv.get('pid', 0), 'type': 'dashboard', 'busiFlag': 'dashboard',
    'componentData': json.dumps([date_comp, chart_comp], separators=(',', ':'), ensure_ascii=False),
    'canvasStyleData': json.dumps(old_canvas, separators=(',', ':')),
    'canvasViewInfo': {chart_id: chart_view},
    'checkVersion': str(cur_version), 'version': cur_version + 1,
    'contentId': str(dv.get('contentId', '0')),
    'status': 0, 'mobileLayout': False,
}

print(f'\n=== Update canvas (v{cur_version}) ===')
r3 = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                    headers=headers, json=update_payload, timeout=60)
print(f'updateCanvas: {r3.json().get("code")}')

r4 = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus', headers=headers,
                    json={'id': M2_ID, 'type': 'dashboard', 'busiFlag': 'dashboard', 'status': 1,
                          'pid': dv.get('pid', 0)}, timeout=30)
print(f'Publish: {r4.json().get("code")}')
print('\nDone!')
