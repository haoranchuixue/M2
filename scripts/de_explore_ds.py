"""Explore DataEase StarRocks data source and existing datasets."""
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

print("Getting fresh token...")
token = get_fresh_token()
print(f"Token: {token[:60]}...")

headers = {
    'x-de-token': token,
    'Content-Type': 'application/json'
}

def api_post(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=15)
    return r.json()

def api_get(path):
    r = requests.get(f'{base}/de2api{path}', headers=headers, timeout=15)
    return r.json()

# 1. Get data source tree
print("\n=== Data Source Tree ===")
tree = api_post('/datasource/tree')
print(json.dumps(tree, indent=2, ensure_ascii=False)[:2000])

# 2. Get data source details
ds_id = None
if tree.get('data'):
    for node in tree['data']:
        if node.get('children'):
            for child in node['children']:
                print(f"\nDatasource: {child.get('name')} (ID: {child.get('id')})")
                ds_id = child.get('id')

# 3. Get tables in StarRocks
if ds_id:
    print(f"\n=== Tables in datasource {ds_id} ===")
    tables = api_post('/datasource/getTables', {'datasourceId': ds_id})
    if tables.get('data'):
        for t in tables['data'][:30]:
            print(f"  Table: {json.dumps(t, ensure_ascii=False)[:200]}")
    else:
        # Try alternative endpoint
        tables2 = api_post(f'/datasource/{ds_id}/getTables')
        print(json.dumps(tables2, ensure_ascii=False)[:2000])

# 4. Get existing datasets
print("\n=== Dataset Tree ===")
ds_tree = api_post('/dataVisualization/interactiveTree')
print(json.dumps(ds_tree, indent=2, ensure_ascii=False)[:3000])

# 5. Get existing dashboards/panels
print("\n=== Panel (Dashboard) Tree ===")
panel_tree = api_post('/panel/tree')
if panel_tree.get('code') != 0:
    panel_tree = api_post('/dataVisualization/tree', {'busiFlag': 'panel'})
print(json.dumps(panel_tree, indent=2, ensure_ascii=False)[:3000])
