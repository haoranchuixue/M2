"""Find DataEase 2.x datasource API endpoints and execute direct SQL."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests

base = 'http://47.236.78.123:8100'
DATASOURCE_ID = '1236022373120086016'

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

# Scan for datasource API endpoints
api_paths = [
    ('GET', 'datasource/query/{}'),
    ('POST', 'datasource/query/{}'),
    ('GET', 'datasource/get/{}'),
    ('POST', 'datasource/getSchema/{}'),
    ('POST', 'datasource/getTables/{}'),
    ('POST', 'datasource/validate/{}'),
    ('POST', 'datasource/checkApiDatasource/{}'),
    ('POST', 'engine/getSchema/{}'),
    ('GET', 'engine/getSchema/{}'),
    ('POST', 'datasource/latestUse/list'),
    ('GET', 'datasource/types'),
    ('POST', 'datasource/types'),
    ('POST', 'datasource/getDetail/{}'),
]

for method, path in api_paths:
    url = f'{base}/de2api/{path.format(DATASOURCE_ID)}'
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=5)
        else:
            r = requests.post(url, headers=headers, json={}, timeout=5)
        status = r.status_code
        body_preview = r.text[:200] if status != 404 else '(404)'
        print(f'{method} {path.format("...")} -> {status}: {body_preview}')
    except Exception as e:
        print(f'{method} {path.format("...")} -> {type(e).__name__}')

# Try to find datasource connection info through dataset preview endpoints
print('\n=== Checking dataset data endpoints ===')
DS_ID = '1236046190513098752'

endpoints = [
    ('POST', 'datasetData/previewSql', {'id': DS_ID, 'sql': "SELECT COUNT(*) FROM dsp_report LIMIT 1"}),
    ('POST', 'datasetData/execSql', {'id': DS_ID, 'sql': "SELECT create_date, COUNT(*) cnt FROM dsp_report WHERE create_date='2026-03-31' GROUP BY create_date"}),
    ('POST', f'datasetTree/getFieldsFromDE/{DS_ID}', {}),
    ('POST', 'datasetData/previewData', {'id': DS_ID}),
    ('POST', 'datasetData/previewDataWithPage', {'id': DS_ID, 'page': 1, 'pageSize': 5}),
]

for method, ep, payload in endpoints:
    try:
        r = requests.post(f'{base}/de2api/{ep}', headers=headers, json=payload, timeout=15)
        print(f'\n{ep}: {r.status_code}')
        if r.status_code == 200:
            body = r.json()
            print(f'  code={body.get("code")}')
            if body.get('data'):
                print(f'  data: {str(body["data"])[:300]}')
            elif body.get('msg'):
                print(f'  msg: {str(body["msg"])[:200]}')
    except Exception as e:
        print(f'{ep}: {type(e).__name__}')

# Try datasource validate and schema endpoints
print('\n=== Datasource schema exploration ===')
schema_endpoints = [
    ('POST', f'datasource/validate/{DATASOURCE_ID}', {}),
    ('POST', 'datasource/validate', {'id': DATASOURCE_ID}),
    ('POST', f'datasource/getSchema/{DATASOURCE_ID}', {}),
    ('POST', 'datasource/getSchema', {'id': DATASOURCE_ID}),
    ('POST', f'datasource/getTables/{DATASOURCE_ID}', {}),
    ('POST', 'datasource/getTables', {'id': DATASOURCE_ID}),
]

for method, ep, payload in schema_endpoints:
    try:
        r = requests.post(f'{base}/de2api/{ep}', headers=headers, json=payload, timeout=15)
        print(f'\n{ep}: {r.status_code}')
        if r.status_code == 200:
            body = r.json()
            code = body.get('code')
            print(f'  code={code}')
            if code == 0:
                data = body.get('data', '')
                print(f'  data: {str(data)[:400]}')
    except Exception as e:
        print(f'{ep}: {type(e).__name__}')

print('\nDone')
