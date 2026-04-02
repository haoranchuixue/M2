"""
1. Restore original dataset to db mode
2. Create a NEW SQL-based dataset with date filter
3. Rebuild m2dashboard to use the new dataset
"""
import sys, json, base64, copy
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

# ─── Step 1: Restore original dataset to db mode ───
print('=== Step 1: Restore dataset to db mode ===')
r = requests.post(f'{base}/de2api/datasetTree/details/{OLD_DS_ID}', headers=headers, json={}, timeout=30)
old_ds = r.json()['data']
old_union = old_ds.get('union', [])
old_fields = [f for f in old_ds.get('allFields', []) if f.get('extField', 0) == 0 and len(f.get('originName', '')) <= 50]

if old_union:
    cds = old_union[0]['currentDs']
    cds['type'] = 'db'
    cds['info'] = json.dumps({'table': 'dsp_report', 'sql': ''})

restore_payload = {
    'id': OLD_DS_ID,
    'name': old_ds.get('name'),
    'pid': old_ds.get('pid'),
    'nodeType': 'dataset',
    'isCross': False,
    'union': old_union,
    'allFields': old_fields,
}
r2 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=restore_payload, timeout=60)
print(f'Restore: code={r2.json().get("code")}')

# ─── Step 2: Create new SQL dataset ───
print('\n=== Step 2: Create new SQL dataset ===')
# Cast DECIMAL columns to DOUBLE to avoid date_format type mismatch in Calcite
core_cols = [
    'source', 'create_date', 'affiliate_id', 'country', 'connection_type',
    'adv_id', 'adv_type', 'p_cvr_version', 'p_ctr_version',
    'tag_id', 'tag_name', 'audience',
    'request_count', 'request_filter_count', 'response_count',
    'win_count', 'CAST(bid_price_total AS DOUBLE) AS bid_price_total',
    'imp_count', 'clean_imp_count',
    'cheat_imp_count', 'exceed_imp_count', 'click_count',
    'clean_click_count', 'cheat_click_count',
    'CAST(price_total AS DOUBLE) AS price_total',
]
sql_columns = ', '.join(core_cols)
sql_query = f"SELECT {sql_columns} FROM dsp_report WHERE create_date = '2026-03-29' LIMIT 5000"
sql_b64 = base64.b64encode(sql_query.encode()).decode()

new_table_id = str(int(time.time() * 1000))
new_table_info = {
    'id': new_table_id,
    'name': None,
    'tableName': 'dsp_report',
    'datasourceId': DATASOURCE_ID,
    'type': 'sql',
    'info': json.dumps({'table': 'dsp_report', 'sql': sql_b64}),
    'sqlVariableDetails': None,
    'isCross': False,
}

# Copy fields from old dataset but only those in core_cols
core_set = set(core_cols)
new_fields = []
for f in old_fields:
    if f['originName'] not in core_set:
        continue
    nf = copy.deepcopy(f)
    nf['datasetTableId'] = new_table_id
    nf['datasetGroupId'] = None
    if 'id' in nf:
        del nf['id']
    new_fields.append(nf)
print(f'Using {len(new_fields)} fields for new dataset')

new_ds_fields = copy.deepcopy(new_fields)

# Try without dataeaseName/fieldShortName to let DataEase generate them
simple_fields = []
for f in new_fields:
    sf = {k: v for k, v in f.items() if k not in ('dataeaseName', 'fieldShortName', 'dbFieldName')}
    simple_fields.append(sf)

simple_ds_fields = copy.deepcopy(simple_fields)

create_payload = {
    'name': 'DSP_Report_v2',
    'pid': FOLDER_ID,
    'nodeType': 'dataset',
    'isCross': False,
    'union': [{
        'currentDs': new_table_info,
        'currentDsField': None,
        'currentDsFields': simple_ds_fields,
    }],
    'allFields': simple_fields,
}

r3 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=create_payload, timeout=60)
resp3 = r3.json()
print(f'Create: code={resp3.get("code")}, msg={str(resp3.get("msg",""))[:200]}')

if resp3.get('code') == 0:
    new_ds_id = resp3.get('data')
    if isinstance(new_ds_id, dict):
        new_ds_id = new_ds_id.get('id')
    new_ds_id = str(new_ds_id)
    print(f'New dataset ID: {new_ds_id}')

    # Get fresh fields
    time.sleep(2)
    r4 = requests.post(f'{base}/de2api/datasetTree/details/{new_ds_id}', headers=headers, json={}, timeout=30)
    d4 = r4.json()['data']
    fresh_fields = d4.get('allFields', [])
    print(f'Fresh fields: {len(fresh_fields)}')
    for f in fresh_fields[:5]:
        print(f'  {f["originName"]:25s} id={f["id"]}')

    field_map = {f['originName']: f for f in fresh_fields}
    DS_ID = new_ds_id

    # Test getData
    print('\n=== Test getData with new dataset ===')
    date_field = field_map.get('create_date')
    test_xaxis = []
    for fname in ['create_date', 'source', 'country']:
        f = field_map.get(fname)
        if f:
            test_xaxis.append({
                'id': f['id'], 'originName': f['originName'], 'name': f['originName'],
                'datasetGroupId': DS_ID, 'groupType': 'd', 'type': f['type'],
                'deType': f.get('deType', 0), 'checked': True, 'chartType': 'table-info',
                'sort': 'none', 'filter': [],
            })

    test_view = {
        'id': 'test_' + str(int(time.time())),
        'title': 'test', 'tableId': DS_ID,
        'type': 'table-info', 'render': 'antv',
        'resultCount': 100, 'resultMode': 'custom',
        'xAxis': test_xaxis, 'xAxisExt': [], 'yAxis': [], 'yAxisExt': [],
        'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
        'extColor': [], 'sortPriority': [],
        'customAttr': {'basicStyle': {}, 'tableHeader': {}, 'tableCell': {}, 'misc': {}, 'label': {}, 'tooltip': {}},
        'customStyle': {}, 'customFilter': {},
        'drillFields': [], 'senior': {},
        'dataFrom': 'dataset', 'datasetMode': 0,
    }

    t0 = time.time()
    r5 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view, timeout=300)
    t1 = time.time()
    resp5 = r5.json()
    print(f'Time: {t1-t0:.1f}s  Code: {resp5.get("code")}')
    if resp5.get('code') == 0:
        rows = resp5.get('data', {}).get('tableRow', [])
        fields = resp5.get('data', {}).get('fields', [])
        print(f'Rows: {len(rows)} Fields: {len(fields)}')
        if rows:
            print(f'Sample: {json.dumps(rows[0], ensure_ascii=False)[:400]}')
    else:
        print(f'Error: {str(resp5.get("msg",""))[:300]}')
else:
    print(f'Failed to create dataset')
    sys.exit(1)
