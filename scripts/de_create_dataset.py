"""Create DSP Report dataset and dashboard in DataEase via API."""
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

# Step 1: Create a dataset group (folder) for DSP Report
print("=== Step 1: Create dataset group ===")
group_payload = {
    "name": "DSP Report",
    "nodeType": "folder",
    "pid": "0",
    "type": "group"
}
# Try creating dataset group
group_result = api_post('/datasetGroup/save', group_payload)
print(f"Group save result: {json.dumps(group_result, ensure_ascii=False)[:500]}")

# If it failed, try other endpoint
if group_result.get('code') != 0:
    # Try the dataset tree API to create a group
    group_result = api_post('/dataset/save', group_payload)
    print(f"Dataset save result: {json.dumps(group_result, ensure_ascii=False)[:500]}")

# Step 2: Find existing datasets to understand the API
print("\n=== Step 2: Check existing datasets ===")
# Let's capture API calls when creating a dataset via UI
# First, let's look at the DataEase dataset API structure
for endpoint in ['/datasetGroup/tree', '/dataset/tree', '/dataVisualization/interactiveTree']:
    result = api_post(endpoint)
    if result.get('data'):
        print(f"{endpoint}: {json.dumps(result, ensure_ascii=False)[:500]}")
