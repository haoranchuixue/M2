"""Check the datasource configuration and try direct SQL execution."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests

base = 'http://47.236.78.123:8100'
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

# Get dataset details to find datasource info
r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
ds = r.json()['data']
print('Dataset info:')
print(f'  name: {ds.get("name")}')
print(f'  type: {ds.get("type")}')
print(f'  datasourceId: {ds.get("datasourceId")}')

info = ds.get('info')
if isinstance(info, str):
    info = json.loads(info)
print(f'  info: {json.dumps(info, ensure_ascii=False)[:500]}')

datasource_id = ds.get('datasourceId')

# List all datasources
for ep in ['datasource/list', 'datasource/listAll', 'datasource/getAll']:
    try:
        r2 = requests.get(f'{base}/de2api/{ep}', headers=headers, timeout=10)
        print(f'\n{ep}: status={r2.status_code}')
        if r2.status_code == 200:
            body = r2.json()
            print(f'  code={body.get("code")}')
            if body.get('data'):
                data = body['data']
                if isinstance(data, list):
                    for d in data[:5]:
                        print(f'  DS: id={d.get("id")} name={d.get("name")} type={d.get("type")}')
                else:
                    print(f'  data: {str(data)[:300]}')
    except Exception as e:
        print(f'{ep}: {type(e).__name__}')

# Try POST versions
for ep in ['datasource/list', 'datasource/listAll']:
    try:
        r3 = requests.post(f'{base}/de2api/{ep}', headers=headers, json={}, timeout=10)
        print(f'\nPOST {ep}: status={r3.status_code}')
        if r3.status_code == 200:
            body = r3.json()
            data = body.get('data', [])
            if isinstance(data, list):
                for d in data[:5]:
                    print(f'  DS: id={d.get("id")} name={d.get("name")} type={d.get("type")} conf={str(d.get("configuration",""))[:200]}')
    except Exception as e:
        print(f'POST {ep}: {type(e).__name__}')

# Get specific datasource details
if datasource_id:
    for ep in [f'datasource/get/{datasource_id}', f'datasource/{datasource_id}',
               f'datasource/detail/{datasource_id}']:
        try:
            r4 = requests.get(f'{base}/de2api/{ep}', headers=headers, timeout=10)
            print(f'\n{ep}: status={r4.status_code}')
            if r4.status_code == 200:
                body = r4.json()
                data = body.get('data', body)
                print(f'  {json.dumps(data, ensure_ascii=False)[:500]}')
        except Exception as e:
            print(f'{ep}: {type(e).__name__}')

# Try executing direct SQL via datasource
print('\n=== Trying direct SQL execution ===')
for ep in ['datasource/executeSql', 'datasource/execSql', 'datasetData/previewDataWithLimit']:
    sql = "SELECT create_date, COUNT(*) as cnt FROM dsp_report WHERE create_date >= '2026-03-28' GROUP BY create_date ORDER BY create_date DESC LIMIT 5"
    payloads = [
        {'datasourceId': datasource_id, 'sql': sql},
        {'id': datasource_id, 'sql': sql},
        {'datasourceId': datasource_id, 'sql': sql, 'tableName': 'dsp_report'},
    ]
    for payload in payloads:
        try:
            r5 = requests.post(f'{base}/de2api/{ep}', headers=headers, json=payload, timeout=30)
            print(f'\n{ep}: status={r5.status_code}')
            if r5.status_code == 200:
                body = r5.json()
                print(f'  code={body.get("code")}  data={str(body.get("data",""))[:300]}')
                if body.get('code') == 0:
                    break
        except Exception as e:
            print(f'{ep}: {type(e).__name__}')

# Try previewData on the dataset
print('\n=== Dataset previewData ===')
r6 = requests.post(f'{base}/de2api/datasetData/previewData',
                    headers=headers, json={'id': DS_ID, 'limit': 5}, timeout=120)
print(f'previewData: status={r6.status_code}')
try:
    body = r6.json()
    print(f'  code={body.get("code")}')
    if body.get('code') == 0:
        data = body.get('data', {})
        print(f'  fields: {len(data.get("fields", []))} rows: {len(data.get("data", []))}')
        if data.get('data'):
            for row in data['data'][:2]:
                print(f'  row: {json.dumps(row, ensure_ascii=False)[:300]}')
    else:
        print(f'  msg: {str(body.get("msg",""))[:300]}')
except:
    print(f'  raw: {r6.text[:300]}')

print('\nDone')
