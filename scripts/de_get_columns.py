"""Get columns of dsp_report table and create dataset."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time

base = 'http://47.236.78.123:8100'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base}/', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        inputs = page.query_selector_all('input')
        inputs[0].fill('admin')
        inputs[1].fill('DataEase@123456')
        page.query_selector('button').click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt

token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

def api_post(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

sr_ds_id = '1236022373120086016'

# Get table fields/columns
print("=== dsp_report columns ===")
# Try different endpoints
for table_name in ['dsp_report']:
    payload = {
        'datasourceId': sr_ds_id,
        'tableName': table_name,
        'type': 'db'
    }
    fields = api_post('/datasource/getTableField', payload)
    if fields.get('data'):
        print(f"\nTable: {table_name}")
        for f in fields['data']:
            print(f"  {f.get('fieldName', f.get('name', '?'))}: {f.get('fieldType', '?')}")
    else:
        print(f"  {table_name}: {json.dumps(fields, ensure_ascii=False)[:300]}")

# Also try ads_dsp_adv_index_report
print("\n=== ads_dsp_adv_index_report columns ===")
payload = {
    'datasourceId': sr_ds_id,
    'tableName': 'ads_dsp_adv_index_report',
    'type': 'db'
}
fields2 = api_post('/datasource/getTableField', payload)
if fields2.get('data'):
    for f in fields2['data']:
        print(f"  {f.get('fieldName', f.get('name', '?'))}: {f.get('fieldType', '?')}")
else:
    print(f"  {json.dumps(fields2, ensure_ascii=False)[:300]}")
