"""Explore StarRocks data source tables in DataEase."""
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
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=15)
    return r.json()

sr_ds_id = '1236022373120086016'

# 1. Get tables in StarRocks
print("=== StarRocks Tables ===")
tables = api_post('/datasource/getTables', {'datasourceId': sr_ds_id})
if tables.get('data'):
    for t in tables['data']:
        print(f"  {t.get('tableName')} ({t.get('name')})")
else:
    print(json.dumps(tables, indent=2, ensure_ascii=False)[:2000])

# 2. Get data source details
print("\n=== Data Source Details ===")
ds_detail = api_post('/datasource/get', {'id': sr_ds_id})
if ds_detail.get('code') != 0:
    ds_detail = api_post(f'/datasource/detail/{sr_ds_id}')
print(json.dumps(ds_detail, indent=2, ensure_ascii=False)[:2000])

# 3. List existing datasets (different API)
print("\n=== Dataset Groups ===")
for path in ['/dataset/tree', '/dataset/group/tree', '/datasetGroup/tree']:
    result = api_post(path)
    if result.get('code') == 0 and result.get('data'):
        print(f"\n{path}:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
        break
    else:
        print(f"{path}: code={result.get('code')}, msg={result.get('msg', '')[:100]}")

# 4. List dashboards  
print("\n=== Dashboards ===")
for path in ['/dataVisualization/tree', '/dataVisualization/interactiveTree']:
    result = api_post(path, {'busiFlag': 'panel'})
    if result.get('code') == 0:
        print(f"\n{path}:")
        print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
