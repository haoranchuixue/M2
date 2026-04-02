"""
Create a SQL-based dataset with a date filter to avoid full table scans.
Then rebuild m2dashboard to use this new dataset.
"""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
M2_ID = '1236684857652940800'
OLD_DS_ID = '1236046190513098752'
DATASOURCE_ID = '1236022373120086016'
FOLDER_ID = '1236043392912330752'


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

# Step 1: Create SQL-based dataset with date filter
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
print(f'SQL: {sql_query}')

table_info = {
    'tableName': 'dsp_report_recent',
    'datasourceId': DATASOURCE_ID,
    'type': 'sql',
    'info': json.dumps({'table': 'dsp_report_recent', 'sql': sql_query}),
    'sqlVariableDetails': None,
}

# Try to create a new dataset using the save API
new_ds_payload = {
    'name': 'DSP Report Recent',
    'pid': FOLDER_ID,
    'nodeType': 'dataset',
    'union': [{
        'currentDs': table_info,
        'currentDsField': None,
        'currentDsFields': [],
        'childDs': None,
        'unionType': None,
        'unionFields': None,
    }],
    'allFields': [],
}

print('\n=== Step 1: Create filtered dataset ===')
r = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=new_ds_payload, timeout=60)
print(f'Status: {r.status_code}')
resp = r.json()
print(f'Code: {resp.get("code")}, Msg: {str(resp.get("msg",""))[:200]}')

if resp.get('code') != 0:
    print('Failed to create dataset. Trying different API...')
    # Maybe we need a different endpoint
    r2 = requests.post(f'{base}/de2api/datasetTable/save', headers=headers, json=new_ds_payload, timeout=60)
    print(f'datasetTable/save: {r2.status_code} {r2.text[:300]}')

new_ds_id = None
if resp.get('code') == 0 and resp.get('data'):
    new_ds_id = str(resp['data'].get('id', resp['data'])) if isinstance(resp['data'], dict) else str(resp['data'])
    print(f'New dataset ID: {new_ds_id}')

    # Get fields from new dataset
    time.sleep(2)
    r3 = requests.post(f'{base}/de2api/datasetTree/details/{new_ds_id}', headers=headers, json={}, timeout=30)
    d3 = r3.json().get('data') or {}
    fields = d3.get('allFields') or []
    print(f'New dataset fields: {len(fields)}')
    for f in fields[:5]:
        print(f'  {f.get("originName")} (type={f.get("type")}, id={f.get("id")})')
else:
    print('Using old dataset ID instead, will try to make it work')
    new_ds_id = OLD_DS_ID

    # Get fields from old dataset
    r3 = requests.post(f'{base}/de2api/datasetTree/details/{OLD_DS_ID}', headers=headers, json={}, timeout=30)
    d3 = r3.json()['data']
    fields = d3['allFields']

field_map = {f['originName']: f for f in fields}
DS_ID = new_ds_id

date_field = field_map.get('create_date')
source_field = field_map.get('source')

print(f'\nUsing dataset: {DS_ID}')
print(f'Fields: {len(fields)}')


def make_field(origin_name, display_name, group_type):
    f = field_map.get(origin_name)
    if not f:
        return None
    return {
        'id': f['id'],
        'datasourceId': f.get('datasourceId'),
        'datasetTableId': f.get('datasetTableId'),
        'datasetGroupId': str(DS_ID),
        'chartId': None,
        'originName': f['originName'],
        'name': display_name,
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
        'chartType': 'table-info',
        'sort': 'none',
        'filter': [],
        'hide': False,
        'agg': False,
    }


all_columns = [
    ('create_date', 'Date'),
    ('country', 'Country'),
    ('connection_type', 'Connect Type'),
    ('adv_id', 'Adv ID'),
    ('adv_type', 'Adv Type'),
    ('p_cvr_version', 'PCvr Version'),
    ('p_ctr_version', 'PCtr Version'),
    ('tag_id', 'Tag ID'),
    ('tag_name', 'Tag Name'),
    ('audience', 'Audience'),
    ('source', 'Source'),
    ('request_count', 'Request'),
    ('request_filter_count', 'TotalRequest'),
    ('response_count', 'Response'),
    ('win_count', 'Wins'),
    ('bid_price_total', 'BidPrice'),
    ('imp_count', 'Impressions'),
    ('clean_imp_count', 'Clean Impressions'),
    ('cheat_imp_count', 'Cheat Impressions'),
    ('exceed_imp_count', 'Exceed Impressions'),
    ('click_count', 'Click'),
    ('clean_click_count', 'Clean Clicks'),
    ('cheat_click_count', 'Cheat Clicks'),
    ('price_total', 'Price Total'),
]

x_axis = [item for o, d in all_columns if (item := make_field(o, d, 'd'))]
print(f'xAxis: {len(x_axis)}')

chart_id = str(int(time.time() * 1000))
filter_id = str(int(time.time() * 1000) + 1)

chart_view = {
    'id': chart_id,
    'title': 'DSP Report',
    'sceneId': str(M2_ID),
    'tableId': str(DS_ID),
    'type': 'table-info',
    'render': 'antv',
    'resultCount': 1000,
    'resultMode': 'custom',
    'xAxis': x_axis, 'xAxisExt': [], 'yAxis': [], 'yAxisExt': [],
    'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
    'extColor': [], 'sortPriority': [],
    'customAttr': {
        'basicStyle': {
            'alpha': 100, 'tableBorderColor': '#E6E7E4',
            'tableScrollBarColor': 'rgba(0,0,0,0.15)', 'tableColumnMode': 'adapt',
            'tableColumnWidth': 100, 'tablePageMode': 'pull', 'tablePageSize': 20,
            'tableLayoutMode': 'grid',
        },
        'tableHeader': {
            'showIndex': False, 'tableHeaderAlign': 'left',
            'tableHeaderBgColor': '#F5F6F7', 'tableHeaderFontColor': '#333333',
            'tableTitleFontSize': 12, 'tableTitleHeight': 36, 'tableHeaderSort': True,
        },
        'tableCell': {
            'tableFontColor': '#333333', 'tableItemAlign': 'left',
            'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
            'tableItemHeight': 36, 'enableTableCrossBG': True,
            'tableItemSubBgColor': '#F8F8F9',
        },
        'misc': {'showName': True},
        'label': {'show': False},
        'tooltip': {'show': True},
    },
    'customStyle': {
        'text': {'show': True, 'fontSize': '14', 'hPosition': 'left', 'vPosition': 'top',
                 'isBolder': True, 'color': '#333333'},
    },
    'customFilter': {},
    'drillFields': [],
    'senior': {
        'functionCfg': {'sliderShow': False, 'emptyDataStrategy': 'breakLine'},
        'scrollCfg': {'open': False},
    },
    'dataFrom': 'dataset',
    'datasetMode': 0,
}

# VQuery component
if date_field and source_field:
    date_criteria = {
        'id': str(int(time.time() * 1000) + 10),
        'name': 'Time Range',
        'showError': True,
        'timeGranularity': 'date',
        'timeGranularityMultiple': 'daterange',
        'field': {'id': date_field['id'], 'type': date_field['type'], 'name': 'Date', 'deType': 1},
        'displayId': date_field['id'],
        'conditionType': 0, 'conditionValueOperatorF': 'eq',
        'timeType': 'fixed', 'relativeToCurrent': 'custom',
        'required': False,
        'defaultValue': ['2026-03-29', '2026-03-29'],
        'selectValue': ['2026-03-29', '2026-03-29'],
        'optionValueSource': 0, 'dataset': {'id': str(DS_ID)},
        'visible': True, 'defaultValueCheck': True, 'multiple': False,
        'displayType': '7',
        'checkedFields': [str(DS_ID)],
        'checkedFieldsMap': {
            str(DS_ID): [{'datasetId': str(DS_ID), 'id': date_field['id'],
                          'originName': 'create_date', 'name': 'Date', 'deType': 1,
                          'groupType': 'd', 'checked': True}],
        },
    }

    source_criteria = {
        'id': str(int(time.time() * 1000) + 11),
        'name': 'Source',
        'showError': True,
        'field': {'id': source_field['id'], 'type': source_field['type'], 'name': 'Source',
                  'deType': source_field.get('deType', 0)},
        'displayId': source_field['id'],
        'conditionType': 0, 'conditionValueOperatorF': 'eq',
        'timeType': 'fixed', 'relativeToCurrent': 'custom',
        'required': False,
        'optionValueSource': 0, 'dataset': {'id': str(DS_ID)},
        'visible': True, 'defaultValueCheck': False, 'multiple': False,
        'displayType': '0',
        'checkedFields': [str(DS_ID)],
        'checkedFieldsMap': {
            str(DS_ID): [{'datasetId': str(DS_ID), 'id': source_field['id'],
                          'originName': 'source', 'name': 'Source',
                          'deType': source_field.get('deType', 0),
                          'groupType': 'd', 'checked': True}],
        },
    }

date_comp = {
    'animations': [], 'canvasId': 'canvas-main',
    'events': {}, 'groupStyle': {},
    'isLock': False, 'isShow': True, 'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'VQuery',
    'name': 'Time Range', 'label': 'Time Range',
    'propValue': [date_criteria, source_criteria],
    'icon': 'icon_search', 'innerType': 'VQuery',
    'x': 1, 'y': 1, 'sizeX': 72, 'sizeY': 4,
    'style': {'width': 400, 'height': 100},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'backgroundColor': 'rgba(255, 255, 255, 1)',
        'innerPadding': 0, 'borderRadius': 5,
    },
    'state': 'ready', 'render': 'custom',
    'id': filter_id, 'show': True,
    'actionSelection': {'linkageActive': 'custom'},
}

chart_comp = {
    'animations': [], 'canvasId': 'canvas-main',
    'events': {}, 'groupStyle': {},
    'isLock': False, 'isShow': True, 'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'UserView',
    'name': 'DSP Report', 'label': 'DSP Report',
    'propValue': {'innerType': 'table-info'},
    'icon': 'bar', 'innerType': 'table-info',
    'x': 1, 'y': 5, 'sizeX': 72, 'sizeY': 24,
    'style': {'width': 1580, 'height': 600},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'backgroundColor': 'rgba(255, 255, 255, 1)',
        'innerPadding': 0, 'borderRadius': 5,
    },
    'state': 'ready', 'render': 'custom',
    'id': chart_id, 'show': True,
    'actionSelection': {'linkageActive': 'custom'},
}

new_comps = [date_comp, chart_comp]

# Get current dashboard for version
r_dv = requests.post(
    f'{base}/de2api/dataVisualization/findById', headers=headers,
    json={'id': M2_ID, 'busiFlag': 'dashboard', 'resourceTable': 'snapshot'}, timeout=30)
dv = r_dv.json().get('data') or {}
cur_version = dv.get('version') or 1
old_canvas = dv.get('canvasStyleData', '{}')
if isinstance(old_canvas, str):
    old_canvas = json.loads(old_canvas)
if isinstance(old_canvas, dict) and 'dashboard' in old_canvas:
    old_canvas['dashboard']['resultMode'] = 'custom'
    old_canvas['dashboard']['resultCount'] = 1000

update_payload = {
    'id': M2_ID,
    'name': dv.get('name') or 'm2dashboard',
    'pid': dv.get('pid') or 0,
    'type': dv.get('type') or 'dashboard',
    'busiFlag': 'dashboard',
    'componentData': json.dumps(new_comps, separators=(',', ':'), ensure_ascii=False),
    'canvasStyleData': json.dumps(old_canvas, separators=(',', ':')),
    'canvasViewInfo': {chart_id: chart_view},
    'checkVersion': str(cur_version),
    'version': cur_version + 1,
    'contentId': str(dv.get('contentId', '0')),
    'status': 0, 'mobileLayout': False,
}

print(f'\n=== Update canvas ===')
r5 = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                    headers=headers, json=update_payload, timeout=60)
resp5 = r5.json()
print(f'updateCanvas: {resp5.get("code")}')

print('\n=== Publish ===')
r6 = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus', headers=headers,
                    json={'id': M2_ID, 'type': 'dashboard', 'busiFlag': 'dashboard', 'status': 1,
                          'pid': dv.get('pid') or 0}, timeout=30)
print(f'Publish: {r6.json().get("code")}')

# Test chart data
print('\n=== Test chart data ===')
r7 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=300)
resp7 = r7.json()
print(f'getData: code={resp7.get("code")}')
if resp7.get('code') == 0:
    rows = resp7.get('data', {}).get('tableRow', [])
    print(f'Rows: {len(rows)}')
    if rows:
        print(f'Sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
else:
    print(f'Error: {str(resp7.get("msg",""))[:200]}')
