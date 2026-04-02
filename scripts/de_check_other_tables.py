"""Check other StarRocks tables to find a smaller alternative to dsp_report."""
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

sr_ds_id = "1236022373120086016"

# Try to get table columns from DataEase API
tables = ['ads_dsp_cost_metric_daily_dr', 'ads_dsp_adv_index_report', 'resource_watch_mv']

for table_name in tables:
    print(f"\n=== {table_name} ===")
    # Try to get columns via DataEase API
    r = requests.post(f'{base}/de2api/datasource/getTableField',
                     headers=headers,
                     json={"datasourceId": sr_ds_id, "tableName": table_name},
                     timeout=30)
    if r.status_code == 200:
        resp = r.json()
        if resp.get('code') == 0:
            fields = resp.get('data', [])
            print(f"  Fields: {len(fields)}")
            for f in fields:
                name = f.get('fieldName', f.get('originName', f.get('name', 'N/A')))
                ftype = f.get('fieldType', f.get('type', 'N/A'))
                print(f"    {name}: {ftype}")
        else:
            print(f"  Error: {resp.get('msg', '')[:200]}")
    else:
        print(f"  Status: {r.status_code}")
        
        # Try alternative endpoint
        r2 = requests.post(f'{base}/de2api/datasource/getSchema',
                          headers=headers,
                          json={"id": sr_ds_id, "tableName": table_name},
                          timeout=30)
        if r2.status_code == 200:
            print(f"  Schema: {r2.json().get('data', '')[:500]}")
        else:
            print(f"  Alt status: {r2.status_code}")

# Also try to create a dataset from ads_dsp_cost_metric_daily_dr 
# and test if it queries faster
print(f"\n\n=== Try creating dataset from ads_dsp_cost_metric_daily_dr ===")
# First, get the field list for this table
r3 = requests.post(f'{base}/de2api/datasource/getTableField',
                   headers=headers,
                   json={"datasourceId": sr_ds_id, "tableName": "ads_dsp_cost_metric_daily_dr"},
                   timeout=30)

if r3.status_code != 200:
    # Try with different API
    r3 = requests.post(f'{base}/de2api/datasource/tableField',
                      headers=headers,
                      json={"datasourceId": sr_ds_id, "tableName": "ads_dsp_cost_metric_daily_dr"},
                      timeout=30)
    
print(f"Field API status: {r3.status_code}")
if r3.status_code == 200:
    resp3 = r3.json()
    print(f"Code: {resp3.get('code')}")
    print(f"Data preview: {json.dumps(resp3.get('data', [])[:3], ensure_ascii=False)[:500]}")
