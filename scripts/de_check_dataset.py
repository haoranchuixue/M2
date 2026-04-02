"""Check the DSP Report Data dataset configuration."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
DS_ID = '1236046190513098752'

def tok():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(base + '/', timeout=60000, wait_until='domcontentloaded')
        pg.wait_for_load_state('networkidle', timeout=30000)
        pg.wait_for_selector('input', timeout=10000)
        ins = pg.query_selector_all('input')
        ins[0].fill('admin')
        ins[1].fill('DataEase@123456')
        pg.query_selector('button').click()
        time.sleep(5)
        pg.wait_for_load_state('networkidle', timeout=30000)
        tr = pg.evaluate('() => localStorage.getItem("user.token")')
        jwt = json.loads(json.loads(tr)['v'])
        b.close()
        return jwt

h = {'x-de-token': tok(), 'Content-Type': 'application/json'}

# Get dataset details
print('=== Dataset Details ===')
r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=h, json={}, timeout=30)
d = r.json()['data']
print(f'name: {d.get("name")}')
print(f'type: {d.get("type")}')
print(f'datasourceId: {d.get("datasourceId")}')

# Check union and SQL info
for k in ['union', 'sql', 'sqlVariableDetails', 'info', 'createTime',
          'tableName', 'mode', 'datasource', 'table', 'configuration']:
    v = d.get(k)
    if v is not None:
        print(f'{k}: {json.dumps(v, ensure_ascii=False)[:300]}')

# Get all keys at top level
print(f'\nAll keys: {list(d.keys())}')

# Check the table info
if 'union' in d:
    union = d['union']
    if isinstance(union, list):
        for u in union:
            print(f'\nUnion item: {json.dumps(u, ensure_ascii=False)[:500]}')
    elif isinstance(union, dict):
        print(f'\nUnion: {json.dumps(union, ensure_ascii=False)[:500]}')

# Also try to get datasource info
ds_source_id = d.get('datasourceId')
if ds_source_id:
    print(f'\n=== Datasource: {ds_source_id} ===')
    r2 = requests.get(f'{base}/de2api/datasource/get/{ds_source_id}', headers=h, timeout=30)
    if r2.status_code == 200:
        ds = r2.json()
        print(json.dumps(ds, ensure_ascii=False)[:500])
    else:
        r3 = requests.post(f'{base}/de2api/datasource/get/{ds_source_id}', headers=h, json={}, timeout=30)
        print(f'POST get: {r3.status_code} {r3.text[:500]}')

# Try chart data with explicit filter
print('\n=== Test direct chart data call with small limit ===')
from de_fix_m2dashboard import date_field, source_field, field_map, DS_ID as ds, x_axis
# Build minimal chart view
mini_view = {
    'id': 'test_' + str(int(time.time())),
    'title': 'test',
    'tableId': str(ds),
    'type': 'table-info',
    'render': 'antv',
    'resultCount': 5,
    'resultMode': 'custom',
    'xAxis': x_axis[:3],
    'xAxisExt': [], 'yAxis': [], 'yAxisExt': [],
    'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
    'extColor': [], 'sortPriority': [],
    'customAttr': {'basicStyle': {}, 'tableHeader': {}, 'tableCell': {}, 'misc': {}, 'label': {}, 'tooltip': {}},
    'customStyle': {},
    'customFilter': {},
    'drillFields': [],
    'senior': {},
    'dataFrom': 'dataset',
    'datasetMode': 0,
}

r4 = requests.post(f'{base}/de2api/chartData/getData', headers=h, json=mini_view, timeout=300)
resp = r4.json()
print(f'Mini view (3 cols, limit 5): code={resp.get("code")}')
if resp.get('code') == 0:
    rows = resp.get('data', {}).get('tableRow', [])
    print(f'Rows: {len(rows)}')
    if rows:
        print(f'Sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
else:
    print(f'Error: {str(resp.get("msg",""))[:300]}')
