"""Get StarRocks connection details from DataEase datasource."""
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

sr_ds_id = 1236022373120086016

# Get datasource details
r = requests.post(f'{base}/de2api/datasource/get/{sr_ds_id}', headers=headers, json={}, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json().get('data', {})
    print(f"Name: {data.get('name')}")
    print(f"Type: {data.get('type')}")
    config = data.get('configuration', '')
    if isinstance(config, str):
        try:
            config_obj = json.loads(config)
            print(f"Host: {config_obj.get('host')}")
            print(f"Port: {config_obj.get('port')}")
            print(f"Database: {config_obj.get('dataBase')}")
            print(f"Username: {config_obj.get('username')}")
            # Don't print password
            print(f"Has password: {'password' in config_obj}")
        except:
            pass
    print(f"\nFull response: {json.dumps(data, ensure_ascii=False)[:500]}")
else:
    # Try other endpoints
    for endpoint in ['get', 'detail', 'getDetail']:
        url = f'{base}/de2api/datasource/{endpoint}/{sr_ds_id}'
        r2 = requests.post(url, headers=headers, json={}, timeout=10)
        r3 = requests.get(url, headers=headers, timeout=10)
        if r2.status_code == 200:
            print(f"POST {endpoint}: {r2.text[:200]}")
        if r3.status_code == 200:
            print(f"GET {endpoint}: {r3.text[:200]}")

# Also try to execute SQL through DataEase datasource API
print("\n\n=== Trying to execute SQL via DataEase ===")
exec_endpoints = [
    'datasource/executeSql',
    'datasource/execute',
    'datasource/query',
]
for ep in exec_endpoints:
    r4 = requests.post(f'{base}/de2api/{ep}', headers=headers,
                      json={"datasourceId": sr_ds_id, "sql": "SELECT 1", "id": sr_ds_id},
                      timeout=10)
    print(f"POST {ep}: {r4.status_code}")
    if r4.status_code == 200:
        print(f"  Response: {r4.text[:200]}")
