"""Debug the chartData/getData error."""
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

# Get the chart view from the dashboard
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
data = r.json().get('data', {})
views = data.get('canvasViewInfo', {})

for vid, vdata in views.items():
    print(f"Chart: {vid}, type: {vdata.get('type')}, title: {vdata.get('title')}")
    
    # Call getData
    r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=vdata, timeout=60)
    resp = r2.json()
    print(f"  Status: {r2.status_code}")
    print(f"  Code: {resp.get('code')}")
    print(f"  Msg: {resp.get('msg', '')[:500]}")
    
    if resp.get('data'):
        data_info = resp.get('data', {})
        print(f"  Data keys: {list(data_info.keys()) if isinstance(data_info, dict) else 'not dict'}")
