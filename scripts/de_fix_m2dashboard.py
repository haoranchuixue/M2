"""
Fix m2dashboard (id=1236684857652940800) in DataEase gray environment.

The chart references a deleted dataset. Rebind to 'DSP Report Data' (1236046190513098752)
and add Time Range + Source query components.
"""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
M2_ID = '1236684857652940800'
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

# ─── Step 1: Get current m2dashboard ───
print('=== Step 1: Get m2dashboard ===')
r = requests.post(
    f'{base}/de2api/dataVisualization/findById',
    headers=headers,
    json={'id': M2_ID, 'busiFlag': 'dashboard', 'resourceTable': 'snapshot'},
    timeout=30,
)
dv = r.json().get('data') or {}
cur_version = dv.get('version') or 1
print(f'name: {dv.get("name")}, type: {dv.get("type")}, version: {cur_version}, status: {dv.get("status")}')

comps = dv.get('componentData', '[]')
if isinstance(comps, str):
    comps = json.loads(comps)
cvi = dv.get('canvasViewInfo') or {}
old_canvas = dv.get('canvasStyleData', '{}')
if isinstance(old_canvas, str):
    old_canvas = json.loads(old_canvas)

print(f'components: {len(comps)}')
for c in comps:
    print(f'  {c.get("component")} / {c.get("innerType")} canvasId={c.get("canvasId")} id={c.get("id")}')
print(f'canvasViewInfo keys: {list(cvi.keys())}')
print(f'canvasStyle: selfAdaption={old_canvas.get("selfAdaption")}, auxiliaryMatrix={old_canvas.get("auxiliaryMatrix")}, dashboard={old_canvas.get("dashboard")}')

# ─── Step 2: Get dataset fields ───
print('\n=== Step 2: Get dataset fields ===')
r2 = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
all_fields = r2.json()['data']['allFields']
field_map = {f['originName']: f for f in all_fields}
print(f'Fields: {len(all_fields)}')

date_field = field_map['create_date']
source_field = field_map['source']


def make_field(origin_name, display_name, group_type, summary=''):
    f = field_map.get(origin_name)
    if not f:
        return None
    result = {
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
        'summary': summary,
        'sort': 'none',
        'formatterCfg': {
            'type': 'auto', 'unitLanguage': 'ch', 'unit': 1,
            'suffix': '', 'decimalCount': 2, 'thousandSeparator': True,
        },
        'filter': [],
        'hide': False,
        'agg': False,
    }
    if origin_name == 'create_date':
        result['filter'] = [{
            'fieldId': str(f['id']),
            'term': 'eq',
            'value': '2026-03-29',
        }]
    return result


# ─── Step 3: Build chart (table-info = detail table, no aggregation) ───
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
y_axis = []
print(f'\nxAxis: {len(x_axis)} (table-info, no yAxis)')

chart_id = str(int(time.time() * 1000))
filter_id = str(int(time.time() * 1000) + 1)
source_filter_id = str(int(time.time() * 1000) + 2)

chart_view = {
    'id': chart_id,
    'title': 'DSP Report',
    'sceneId': str(M2_ID),
    'tableId': str(DS_ID),
    'type': 'table-info',
    'render': 'antv',
    'resultCount': 10,
    'resultMode': 'custom',
    'xAxis': x_axis, 'xAxisExt': [],
    'yAxis': y_axis, 'yAxisExt': [],
    'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
    'extColor': [], 'sortPriority': [],
    'customAttr': {
        'basicStyle': {
            'alpha': 100, 'tableBorderColor': '#E6E7E4',
            'tableScrollBarColor': 'rgba(0,0,0,0.15)', 'tableColumnMode': 'adapt',
            'tableColumnWidth': 100, 'tablePageMode': 'pull', 'tablePageSize': 20,
            'colorScheme': 'default', 'gradient': True, 'tableLayoutMode': 'grid',
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
    'stylePriority': 'panel',
    'dataFrom': 'dataset',
    'refreshViewEnable': False,
    'refreshUnit': 'minute',
    'refreshTime': 5,
    'datasetMode': 0,
}

# Use same canvasId format as existing components
existing_canvas_id = comps[0].get('canvasId', 'canvas-main') if comps else 'canvas-main'
print(f'Using canvasId: {existing_canvas_id}')

# ─── Step 4: Build query components ───
date_comp = {
    'animations': [], 'canvasId': existing_canvas_id,
    'events': {}, 'groupStyle': {},
    'isLock': False, 'isShow': True, 'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'VQuery',
    'name': 'Time Range', 'label': 'Time Range',
    'propValue': [],
    'icon': 'icon_search', 'innerType': 'VQuery',
    'editing': False,
    'x': 1, 'y': 1, 'sizeX': 72, 'sizeY': 4,
    'style': {'width': 400, 'height': 100},
    'matrixStyle': {},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'backgroundColor': 'rgba(255, 255, 255, 1)',
        'innerImage': '', 'outerImage': '', 'innerPadding': 0, 'borderRadius': 5,
    },
    'state': 'ready', 'render': 'custom',
    'id': filter_id,
    'show': True,
    'mobileSelected': False,
    'actionSelection': {'linkageActive': 'custom'},
}

# Add Time Range criteria + Source dropdown as propValue items
date_criteria = {
    'id': str(int(time.time() * 1000) + 10),
    'name': 'Time Range',
    'showError': True,
    'timeGranularity': 'date',
    'timeGranularityMultiple': 'daterange',
    'field': {'id': date_field['id'], 'type': date_field['type'], 'name': 'Date', 'deType': 1},
    'displayId': date_field['id'],
    'sortId': '', 'sort': 'asc',
    'defaultMapValue': [], 'mapValue': [],
    'conditionType': 0,
    'conditionValueOperatorF': 'eq', 'conditionValueF': '',
    'conditionValueOperatorS': 'like', 'conditionValueS': '',
    'defaultConditionValueOperatorF': 'eq', 'defaultConditionValueF': '',
    'defaultConditionValueOperatorS': 'like', 'defaultConditionValueS': '',
    'timeType': 'fixed',
    'relativeToCurrent': 'custom',
    'required': False,
    'timeNum': 0, 'relativeToCurrentType': 'date',
    'around': 'f',
    'auto': False,
    'defaultValue': ['2026-03-29', '2026-03-29'],
    'selectValue': ['2026-03-29', '2026-03-29'],
    'optionValueSource': 0, 'valueSource': [],
    'dataset': {'id': str(DS_ID), 'name': '', 'fields': []},
    'visible': True,
    'defaultValueCheck': True,
    'multiple': False,
    'displayType': '7',
    'checkedFields': [str(DS_ID)],
    'parameters': [], 'parametersCheck': False, 'parametersList': [],
    'checkedFieldsMap': {
        str(DS_ID): [{
            'datasetId': str(DS_ID), 'id': date_field['id'],
            'originName': 'create_date', 'name': 'Date',
            'deType': 1, 'groupType': 'd', 'checked': True,
        }],
    },
}

source_criteria = {
    'id': str(int(time.time() * 1000) + 11),
    'name': 'Source',
    'showError': True,
    'timeGranularity': 'date',
    'timeGranularityMultiple': 'datetimerange',
    'field': {'id': source_field['id'], 'type': source_field['type'], 'name': 'Source', 'deType': source_field.get('deType', 0)},
    'displayId': source_field['id'],
    'sortId': '', 'sort': 'asc',
    'defaultMapValue': [], 'mapValue': [],
    'conditionType': 0,
    'conditionValueOperatorF': 'eq', 'conditionValueF': '',
    'conditionValueOperatorS': 'like', 'conditionValueS': '',
    'defaultConditionValueOperatorF': 'eq', 'defaultConditionValueF': '',
    'defaultConditionValueOperatorS': 'like', 'defaultConditionValueS': '',
    'timeType': 'fixed', 'relativeToCurrent': 'custom',
    'required': False,
    'timeNum': 0, 'relativeToCurrentType': 'date', 'around': 'f',
    'auto': False,
    'defaultValue': None, 'selectValue': None,
    'optionValueSource': 0, 'valueSource': [],
    'dataset': {'id': str(DS_ID), 'name': '', 'fields': []},
    'visible': True,
    'defaultValueCheck': False,
    'multiple': False,
    'displayType': '0',
    'checkedFields': [str(DS_ID)],
    'parameters': [], 'parametersCheck': False, 'parametersList': [],
    'checkedFieldsMap': {
        str(DS_ID): [{
            'datasetId': str(DS_ID), 'id': source_field['id'],
            'originName': 'source', 'name': 'Source',
            'deType': source_field.get('deType', 0), 'groupType': 'd', 'checked': True,
        }],
    },
}

date_comp['propValue'] = [date_criteria, source_criteria]

chart_comp = {
    'animations': [], 'canvasId': existing_canvas_id,
    'events': {}, 'groupStyle': {},
    'isLock': False, 'isShow': True, 'collapseName': [],
    'linkage': {'duration': 0},
    'component': 'UserView',
    'name': 'DSP Report', 'label': 'DSP Report',
    'propValue': {'innerType': 'table-info'},
    'icon': 'bar', 'innerType': 'table-info',
    'editing': False,
    'x': 1, 'y': 5, 'sizeX': 72, 'sizeY': 24,
    'style': {'width': 1580, 'height': 600},
    'matrixStyle': {},
    'commonBackground': {
        'backgroundColorSelect': True, 'backgroundImageEnable': False,
        'backgroundType': 'color', 'backgroundColor': 'rgba(255, 255, 255, 1)',
        'innerImage': '', 'outerImage': '', 'innerPadding': 0, 'borderRadius': 5,
    },
    'state': 'ready', 'render': 'custom',
    'id': chart_id,
    'show': True,
    'mobileSelected': False,
    'actionSelection': {'linkageActive': 'custom'},
}

new_comps = [date_comp, chart_comp]

# ─── Step 5: Update canvas ───
compact_comp = json.dumps(new_comps, separators=(',', ':'), ensure_ascii=False)

# Update canvas style to use custom result mode with limit
if isinstance(old_canvas, dict) and 'dashboard' in old_canvas:
    old_canvas['dashboard']['resultMode'] = 'custom'
    old_canvas['dashboard']['resultCount'] = 1000
compact_style = json.dumps(old_canvas, separators=(',', ':'))

update_payload = {
    'id': M2_ID,
    'name': dv.get('name') or 'm2dashboard',
    'pid': dv.get('pid') or 0,
    'type': dv.get('type') or 'dashboard',
    'busiFlag': 'dashboard',
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

print(f'\n=== Step 5: Update canvas (v{cur_version} -> v{cur_version+1}) ===')
r3 = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                    headers=headers, json=update_payload, timeout=60)
print(f'updateCanvas: {r3.status_code}')
resp3 = r3.json()
print(f'Code: {resp3.get("code")}, Msg: {str(resp3.get("msg",""))[:200]}')

if resp3.get('code') != 0:
    print('FAILED')
    sys.exit(1)

# Publish
print('\n=== Step 6: Publish ===')
r4 = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                    headers=headers,
                    json={'id': M2_ID, 'type': 'dashboard', 'busiFlag': 'dashboard', 'status': 1,
                          'pid': dv.get('pid') or 0},
                    timeout=30)
print(f'Publish: {r4.json().get("code")}')

print(f'\nDone! Open in browser:')
print(f'  Edit: {base}/#/panel/index')
print(f'  Or navigate to m2dashboard in the sidebar.')
