"""
Full rebuild of m2dashboard after dataset SQL update.
Re-fetch field IDs from the updated dataset and rebuild chart.
"""
import sys, json
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

# 1. Get fresh field IDs from the updated dataset
print('=== Step 1: Get fresh dataset fields ===')
r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
ds = r.json()['data']
all_fields = ds.get('allFields', [])
field_map = {f['originName']: f for f in all_fields}
print(f'Fields: {len(all_fields)}')
for f in all_fields[:5]:
    print(f'  {f["originName"]:25s} id={f["id"]}  type={f.get("type")}')
print(f'  ... and {len(all_fields)-5} more')

# Check union SQL
union = ds.get('union', [])
if union:
    cds = union[0].get('currentDs', {})
    info = cds.get('info', '')
    info_obj = json.loads(info) if info else {}
    sql_b64 = info_obj.get('sql', '')
    if sql_b64:
        import base64
        sql = base64.b64decode(sql_b64).decode()
        print(f'\nDataset SQL: {sql}')
    else:
        print(f'\nDataset SQL: (empty)')

date_field = field_map.get('create_date')
source_field = field_map.get('source')
print(f'\nDate field id: {date_field["id"]}')
print(f'Source field id: {source_field["id"]}')

# 2. Build chart with fresh field IDs
def make_field(origin_name, display_name):
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
        'groupType': 'd',
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

columns = [
    ('create_date', 'Date'), ('country', 'Country'),
    ('connection_type', 'Connect Type'), ('adv_id', 'Adv ID'),
    ('adv_type', 'Adv Type'), ('p_cvr_version', 'PCvr Version'),
    ('p_ctr_version', 'PCtr Version'), ('tag_id', 'Tag ID'),
    ('tag_name', 'Tag Name'), ('audience', 'Audience'),
    ('source', 'Source'),
    ('request_count', 'Request'), ('request_filter_count', 'TotalRequest'),
    ('response_count', 'Response'), ('win_count', 'Wins'),
    ('bid_price_total', 'BidPrice'), ('imp_count', 'Impressions'),
    ('clean_imp_count', 'Clean Impressions'),
    ('cheat_imp_count', 'Cheat Impressions'),
    ('exceed_imp_count', 'Exceed Impressions'),
    ('click_count', 'Click'), ('clean_click_count', 'Clean Clicks'),
    ('cheat_click_count', 'Cheat Clicks'), ('price_total', 'Price Total'),
]

x_axis = [item for o, d in columns if (item := make_field(o, d))]
print(f'\nxAxis: {len(x_axis)} fields')

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
        'basicStyle': {'tableBorderColor': '#E6E7E4', 'tableColumnMode': 'adapt',
                        'tablePageMode': 'pull', 'tablePageSize': 20, 'tableLayoutMode': 'grid'},
        'tableHeader': {'tableHeaderAlign': 'left', 'tableHeaderBgColor': '#F5F6F7',
                        'tableHeaderFontColor': '#333333', 'tableTitleFontSize': 12,
                        'tableTitleHeight': 36, 'tableHeaderSort': True},
        'tableCell': {'tableFontColor': '#333333', 'tableItemAlign': 'left',
                      'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
                      'tableItemHeight': 36, 'enableTableCrossBG': True,
                      'tableItemSubBgColor': '#F8F8F9'},
        'misc': {'showName': True}, 'label': {'show': False}, 'tooltip': {'show': True},
    },
    'customStyle': {'text': {'show': True, 'fontSize': '14', 'isBolder': True, 'color': '#333333'}},
    'customFilter': {},
    'drillFields': [],
    'senior': {'functionCfg': {'sliderShow': False, 'emptyDataStrategy': 'breakLine'},
               'scrollCfg': {'open': False}},
    'dataFrom': 'dataset',
    'datasetMode': 0,
}

# 3. Test getData immediately
print('\n=== Test getData ===')
t0 = time.time()
r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=300)
t1 = time.time()
resp = r2.json()
print(f'Time: {t1-t0:.1f}s  Code: {resp.get("code")}')
if resp.get('code') == 0:
    rows = resp.get('data', {}).get('tableRow', [])
    fields_out = resp.get('data', {}).get('fields', [])
    print(f'Rows: {len(rows)} Fields: {len(fields_out)}')
    if rows:
        print(f'Sample row: {json.dumps(rows[0], ensure_ascii=False)[:400]}')
    if fields_out:
        print(f'Fields: {[f.get("name") for f in fields_out[:5]]}...')
else:
    print(f'Error: {str(resp.get("msg",""))[:400]}')

# 4. Build dashboard components
date_criteria = {
    'id': str(int(time.time() * 1000) + 10),
    'name': 'Time Range',
    'timeGranularity': 'date', 'timeGranularityMultiple': 'daterange',
    'field': {'id': date_field['id'], 'type': date_field['type'], 'name': 'Date', 'deType': 1},
    'displayId': date_field['id'],
    'conditionType': 0, 'timeType': 'fixed', 'relativeToCurrent': 'custom',
    'required': False,
    'defaultValue': ['2026-03-29', '2026-03-29'],
    'selectValue': ['2026-03-29', '2026-03-29'],
    'dataset': {'id': str(DS_ID)},
    'visible': True, 'defaultValueCheck': True, 'multiple': False,
    'displayType': '7',
    'checkedFields': [str(DS_ID)],
    'checkedFieldsMap': {str(DS_ID): [{'datasetId': str(DS_ID), 'id': date_field['id'],
                                        'originName': 'create_date', 'name': 'Date',
                                        'deType': 1, 'groupType': 'd', 'checked': True}]},
}
source_criteria = {
    'id': str(int(time.time() * 1000) + 11),
    'name': 'Source',
    'field': {'id': source_field['id'], 'type': source_field['type'], 'name': 'Source',
              'deType': source_field.get('deType', 0)},
    'displayId': source_field['id'],
    'conditionType': 0, 'timeType': 'fixed', 'relativeToCurrent': 'custom',
    'required': False,
    'dataset': {'id': str(DS_ID)},
    'visible': True, 'defaultValueCheck': False, 'multiple': False,
    'displayType': '0',
    'checkedFields': [str(DS_ID)],
    'checkedFieldsMap': {str(DS_ID): [{'datasetId': str(DS_ID), 'id': source_field['id'],
                                        'originName': 'source', 'name': 'Source',
                                        'deType': source_field.get('deType', 0),
                                        'groupType': 'd', 'checked': True}]},
}

date_comp = {
    'canvasId': 'canvas-main', 'component': 'VQuery',
    'name': 'Filters', 'label': 'Filters',
    'propValue': [date_criteria, source_criteria],
    'icon': 'icon_search', 'innerType': 'VQuery',
    'x': 1, 'y': 1, 'sizeX': 72, 'sizeY': 4,
    'style': {'width': 400, 'height': 100},
    'commonBackground': {'backgroundColorSelect': True, 'backgroundType': 'color',
                         'backgroundColor': 'rgba(255,255,255,1)', 'innerPadding': 0, 'borderRadius': 5},
    'state': 'ready', 'render': 'custom', 'id': filter_id, 'show': True,
    'isLock': False, 'isShow': True,
    'actionSelection': {'linkageActive': 'custom'},
}

chart_comp = {
    'canvasId': 'canvas-main', 'component': 'UserView',
    'name': 'DSP Report', 'label': 'DSP Report',
    'propValue': {'innerType': 'table-info'},
    'icon': 'bar', 'innerType': 'table-info',
    'x': 1, 'y': 5, 'sizeX': 72, 'sizeY': 24,
    'style': {'width': 1580, 'height': 600},
    'commonBackground': {'backgroundColorSelect': True, 'backgroundType': 'color',
                         'backgroundColor': 'rgba(255,255,255,1)', 'innerPadding': 0, 'borderRadius': 5},
    'state': 'ready', 'render': 'custom', 'id': chart_id, 'show': True,
    'isLock': False, 'isShow': True,
    'actionSelection': {'linkageActive': 'custom'},
}

# 5. Update dashboard
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

new_comps = [date_comp, chart_comp]
update_payload = {
    'id': M2_ID,
    'name': dv.get('name', 'm2dashboard'),
    'pid': dv.get('pid', 0),
    'type': dv.get('type', 'dashboard'),
    'busiFlag': 'dashboard',
    'componentData': json.dumps(new_comps, separators=(',', ':'), ensure_ascii=False),
    'canvasStyleData': json.dumps(old_canvas, separators=(',', ':')),
    'canvasViewInfo': {chart_id: chart_view},
    'checkVersion': str(cur_version),
    'version': cur_version + 1,
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
