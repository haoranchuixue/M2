"""Create DSP Report dashboard with table chart via DataEase API."""
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

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

# Step 1: First let me examine how an existing dashboard is structured
# by navigating to one with Playwright and capturing the API calls
# Let me first check if there are any existing dashboards

print("=== Checking existing dashboards ===")
panel_tree = api('/dataVisualization/tree', {'busiFlag': 'panel'})
print(json.dumps(panel_tree, indent=2, ensure_ascii=False)[:2000])

# Step 2: Create a new dashboard via API
# Let me first capture API calls when creating a dashboard through the UI

# Actually, let me just try the save API for dashboards
print("\n=== Creating Dashboard ===")

# Dashboard payload
dashboard_payload = {
    "name": "DSP Report",
    "pid": "0",
    "nodeType": "panel",
    "type": "dashboard",
    "watermarkInfo": None,
    "contentId": None
}

# Try different endpoints
for ep in ['/dataVisualization/save', '/dataVisualization/create']:
    result = api(ep, dashboard_payload)
    code = result.get('code')
    status = result.get('status')
    msg = result.get('msg') or ''
    print(f"{ep}: code={code}, status={status}, msg={msg[:200]}")
    if code == 0:
        data = result.get('data')
        if isinstance(data, dict):
            print(f"Dashboard ID: {data.get('id')}")
            with open('d:/Projects/m2/scripts/dashboard_result.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            print(f"Data: {str(data)[:500]}")
        break
