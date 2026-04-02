"""Try to refresh the dataset schema cache after SQL change."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
DS_ID = '1236046190513098752'
DATASOURCE_ID = '1236022373120086016'

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

# Try various schema refresh endpoints
endpoints = [
    ('POST', f'datasetTree/details/{DS_ID}', {}),
    ('POST', f'datasource/checkApiDatasource/{DATASOURCE_ID}', {}),
    ('POST', f'datasource/checkStatus/{DATASOURCE_ID}', {}),
    ('POST', f'datasource/validate/{DATASOURCE_ID}', {}),
    ('POST', f'datasource/getSchema/{DATASOURCE_ID}', {}),
    ('POST', f'datasource/flush/{DATASOURCE_ID}', {}),
    ('POST', f'calcite/flush', {'dsId': DATASOURCE_ID}),
    ('POST', f'dataset/flush/{DS_ID}', {}),
]

for method, ep, body in endpoints:
    try:
        if method == 'POST':
            r = requests.post(f'{base}/de2api/{ep}', headers=h, json=body, timeout=30)
        else:
            r = requests.get(f'{base}/de2api/{ep}', headers=h, timeout=30)
        print(f'{method} {ep}: {r.status_code} {r.text[:200]}')
    except Exception as e:
        print(f'{method} {ep}: ERROR {e}')

# Also try previewDataWithLimit endpoint to test SQL directly
print('\n=== Test SQL preview ===')
import base64
sql = "SELECT * FROM dsp_report WHERE create_date = '2026-03-29' LIMIT 5"
sql_b64 = base64.b64encode(sql.encode()).decode()

r2 = requests.post(f'{base}/de2api/datasetData/previewDataWithLimit', headers=h, json={
    'id': DS_ID,
    'info': json.dumps({'sql': sql_b64, 'table': 'dsp_report'}),
    'type': 'sql',
    'datasourceId': DATASOURCE_ID,
    'limit': 5,
}, timeout=120)
print(f'previewDataWithLimit: {r2.status_code} {r2.text[:500]}')

# Try previewSqlWithLog
r3 = requests.post(f'{base}/de2api/datasetData/previewSqlWithLog', headers=h, json={
    'sql': sql_b64,
    'datasourceId': DATASOURCE_ID,
    'tableId': DS_ID,
}, timeout=120)
print(f'\npreviewSqlWithLog: {r3.status_code} {r3.text[:500]}')
