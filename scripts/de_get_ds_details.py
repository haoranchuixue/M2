"""Get datasource connection details and connect directly to StarRocks."""
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

# Get full datasource details
r = requests.get(f'{base}/de2api/datasource/get/{DATASOURCE_ID}', headers=headers, timeout=10)
body = r.json()
if body.get('code') == 0:
    ds = body['data']
    print(f"Name: {ds.get('name')}")
    print(f"Type: {ds.get('type')}")
    print(f"Description: {ds.get('description')}")
    
    config = ds.get('configuration')
    print(f"\nConfiguration type: {type(config)}")
    print(f"Configuration: {config}")
    
    # Print all fields
    print(f"\nAll fields:")
    for k, v in ds.items():
        if k != 'configuration':
            print(f"  {k}: {str(v)[:200]}")
else:
    print(f"Error: {body}")

print('\nDone')
