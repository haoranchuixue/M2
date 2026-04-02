"""
Create a SQL-based dataset with date filter on dsp_report.
Provides complete field definitions.
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
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

# Get old dataset details (for field definitions)
r = requests.post(f'{base}/de2api/datasetTree/details/{OLD_DS_ID}', headers=headers, json={}, timeout=30)
old_ds = r.json()['data']
old_union = old_ds.get('union', [])
old_fields = old_ds.get('allFields', [])

# Get old table config
old_table = old_union[0]['currentDs'] if old_union else {}
old_table_id = old_table.get('id')
print(f'Old table ID: {old_table_id}')
print(f'Old datasource ID: {old_table.get("datasourceId")}')

# Build fields for new SQL dataset - same as old but with new parent
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"
new_table_id = str(int(time.time() * 1000))

skip_fields = set()
for f in old_fields:
    if len(f.get('originName', '')) > 50 or f.get('extField', 0) != 0:
        skip_fields.add(f['originName'])
        print(f'Skipping calculated field: {f["originName"][:30]}...')

new_fields = []
for f in old_fields:
    if f['originName'] in skip_fields:
        continue
    nf = {
        'id': f['id'],
        'datasourceId': f.get('datasourceId'),
        'datasetTableId': new_table_id,
        'datasetGroupId': None,
        'chartId': None,
        'originName': f['originName'],
        'name': f.get('name') or f['originName'],
        'dataeaseName': f.get('dataeaseName'),
        'groupType': f.get('groupType', 'd'),
        'type': f['type'],
        'deType': f.get('deType', 0),
        'deExtractType': f.get('deExtractType', 0),
        'extField': f.get('extField', 0),
        'checked': True,
        'columnIndex': f.get('columnIndex', 0),
        'dateFormat': f.get('dateFormat'),
        'dateFormatType': f.get('dateFormatType'),
        'fieldShortName': f.get('fieldShortName'),
    }
    new_fields.append(nf)

ds_fields_for_union = []
for f in old_fields:
    if f['originName'] in skip_fields:
        continue
    ds_fields_for_union.append({
        'id': f['id'],
        'datasourceId': f.get('datasourceId'),
        'datasetTableId': new_table_id,
        'originName': f['originName'],
        'name': f.get('name') or f['originName'],
        'type': f['type'],
        'deType': f.get('deType', 0),
        'deExtractType': f.get('deExtractType', 0),
        'extField': f.get('extField', 0),
        'checked': True,
        'columnIndex': f.get('columnIndex', 0),
        'groupType': f.get('groupType', 'd'),
        'fieldShortName': f.get('fieldShortName'),
    })

new_table_info = {
    'id': new_table_id,
    'name': None,
    'tableName': 'custom_sql',
    'datasourceId': DATASOURCE_ID,
    'datasetGroupId': None,
    'type': 'sql',
    'info': json.dumps({'table': 'custom_sql', 'sql': sql_query}),
    'sqlVariableDetails': None,
    'fields': None,
    'lastUpdateTime': 0,
    'isCross': False,
}

# Build minimal field list with no IDs
min_fields = []
for f in old_fields:
    if f['originName'] in skip_fields:
        continue
    min_fields.append({
        'originName': f['originName'],
        'name': f.get('name') or f['originName'],
        'type': f['type'],
        'deType': f.get('deType', 0),
        'checked': True,
        'groupType': f.get('groupType', 'd'),
    })

new_ds_payload = {
    'name': 'DSPReportRecent',
    'pid': FOLDER_ID,
    'nodeType': 'dataset',
    'isCross': False,
    'union': [{
        'currentDs': new_table_info,
        'currentDsField': None,
        'currentDsFields': min_fields,
        'childDs': None,
        'unionType': None,
        'unionFields': None,
    }],
    'allFields': min_fields,
}

print(f'\n=== Create SQL dataset ===')
print(f'SQL: {sql_query}')
print(f'Fields: {len(new_fields)}')

r2 = requests.post(f'{base}/de2api/datasetTree/save', headers=headers, json=new_ds_payload, timeout=60)
print(f'Status: {r2.status_code}')
resp = r2.json()
print(f'Code: {resp.get("code")}, Msg: {str(resp.get("msg",""))[:200]}')

if resp.get('code') == 0:
    new_ds_id = resp.get('data')
    if isinstance(new_ds_id, dict):
        new_ds_id = new_ds_id.get('id')
    print(f'New dataset ID: {new_ds_id}')

    # Verify
    time.sleep(2)
    r3 = requests.post(f'{base}/de2api/datasetTree/details/{new_ds_id}', headers=headers, json={}, timeout=30)
    d3 = r3.json().get('data') or {}
    nf = d3.get('allFields') or []
    print(f'Verified fields: {len(nf)}')
    for f in nf[:5]:
        print(f'  {f.get("originName")} type={f.get("type")} id={f.get("id")}')
else:
    print(f'Full response: {json.dumps(resp, ensure_ascii=False)[:500]}')
