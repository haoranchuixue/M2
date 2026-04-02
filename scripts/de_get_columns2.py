"""Get raw column data from dsp_report table."""
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

sr_ds_id = '1236022373120086016'

# Get raw fields
r = requests.post(f'{base}/de2api/datasource/getTableField', headers=headers, 
                   json={'datasourceId': sr_ds_id, 'tableName': 'dsp_report', 'type': 'db'}, timeout=30)
resp = r.json()

# Print first 5 raw fields to understand structure
if resp.get('data'):
    print(f"Total fields: {len(resp['data'])}")
    print(f"\nField keys: {list(resp['data'][0].keys())}")
    for f in resp['data'][:10]:
        print(json.dumps(f, ensure_ascii=False))

# Save full response
with open('d:/Projects/m2/scripts/dsp_report_fields.json', 'w', encoding='utf-8') as out:
    json.dump(resp, out, indent=2, ensure_ascii=False)
print(f"\nFull response saved to dsp_report_fields.json")
