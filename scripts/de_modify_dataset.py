"""
Modify the existing DSP Report Data dataset to use SQL mode with a date filter.
This avoids full table scans on the huge dsp_report table.
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time, base64

base_url = 'http://47.236.78.123:8100'
DS_ID = '1236046190513098752'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base_url}/', timeout=60000, wait_until='domcontentloaded')
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

# Get current dataset
r = requests.post(f'{base_url}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
d = r.json()['data']
union = d.get('union', [])
all_fields = d.get('allFields', [])

print(f'Dataset: {d.get("name")}')
print(f'Union items: {len(union)}')
print(f'Fields: {len(all_fields)}')

current_ds = union[0]['currentDs']
print(f'Table: {current_ds.get("tableName")}')
print(f'Type: {current_ds.get("type")}')
print(f'Info: {current_ds.get("info")}')

# Modify: Change type from 'db' to 'sql' and add SQL query
sql_query = "SELECT * FROM dsp_report WHERE create_date = '2026-03-29' LIMIT 5000"

# Try base64-encoding the SQL as DataEase might expect that
import base64 as b64
sql_b64 = b64.b64encode(sql_query.encode('utf-8')).decode('utf-8')
print(f'SQL base64: {sql_b64[:60]}...')
new_info = json.dumps({'table': current_ds.get('tableName', 'dsp_report'), 'sql': sql_b64})

current_ds['type'] = 'sql'
current_ds['info'] = new_info
union[0]['currentDs'] = current_ds

# Try updating the dataset
# Filter out calculated/problematic fields
clean_fields = [f for f in all_fields if len(f.get('originName', '')) <= 50 and f.get('extField', 0) == 0]
print(f'Clean fields (without calculated): {len(clean_fields)}')

# Also clean union currentDsFields
for u in union:
    cds_fields = u.get('currentDsFields') or []
    u['currentDsFields'] = [f for f in cds_fields if len(f.get('originName', '')) <= 50 and f.get('extField', 0) == 0]

update_payload = {
    'id': DS_ID,
    'name': d.get('name'),
    'pid': d.get('pid'),
    'nodeType': 'dataset',
    'isCross': d.get('isCross', False) or False,
    'union': union,
    'allFields': clean_fields,
}

print(f'\n=== Update dataset to SQL mode ===')
print(f'SQL: {sql_query}')

# Try save endpoint
r2 = requests.post(f'{base_url}/de2api/datasetTree/save', headers=headers, json=update_payload, timeout=60)
resp = r2.json()
print(f'save: code={resp.get("code")}, msg={str(resp.get("msg",""))[:200]}')

if resp.get('code') != 0:
    # Try update endpoint
    r3 = requests.post(f'{base_url}/de2api/datasetTree/update', headers=headers, json=update_payload, timeout=60)
    resp3 = r3.json()
    print(f'update: code={resp3.get("code")}, msg={str(resp3.get("msg",""))[:200]}')

    if resp3.get('code') != 0:
        # Try with just the union change
        r4 = requests.put(f'{base_url}/de2api/datasetTree/update', headers=headers, json=update_payload, timeout=60)
        print(f'PUT update: {r4.status_code} {r4.text[:300]}')

# Verify
print('\n=== Verify ===')
r5 = requests.post(f'{base_url}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
d5 = r5.json()['data']
u5 = d5.get('union', [{}])
if u5:
    print(f'Type: {u5[0]["currentDs"].get("type")}')
    print(f'Info: {u5[0]["currentDs"].get("info")}')
