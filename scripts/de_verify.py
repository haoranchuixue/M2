"""Verify the dashboard after publishing."""
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

dashboard_id = 1236050016221663232

# Check from core
print("=== From core table ===")
r1 = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                   json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
d1 = r1.json().get('data', {})
comp1 = d1.get('componentData', '[]')
view1 = d1.get('canvasViewInfo', {})
print(f"  Status: {d1.get('status')}")
print(f"  Components: {comp1[:200]}")
print(f"  Views: {json.dumps(view1, ensure_ascii=False)[:200]}")

# Check from snapshot
print("\n=== From snapshot table ===")
r2 = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                   json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
d2 = r2.json().get('data', {})
comp2 = d2.get('componentData', '[]')
view2 = d2.get('canvasViewInfo', {})
print(f"  Status: {d2.get('status')}")
print(f"  Components: {comp2[:200]}")
print(f"  Views: {json.dumps(view2, ensure_ascii=False)[:200]}")

# Check the version
print(f"\n  Version (core): {d1.get('version')}")
print(f"  Version (snapshot): {d2.get('version')}")
print(f"  CheckVersion (core): {d1.get('checkVersion')}")
print(f"  CheckVersion (snapshot): {d2.get('checkVersion')}")
