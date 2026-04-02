"""List all dashboards via various endpoints."""
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

# Try various endpoints
endpoints = [
    ("interactiveTree (dashboard)", {"busiFlag": "dashboard"}),
    ("interactiveTree (dataV)", {"busiFlag": "dataV"}),
    ("interactiveTree (panel)", {"busiFlag": "panel"}),
    ("interactiveTree (empty)", {}),
]

for name, payload in endpoints:
    r = requests.post(f'{base}/de2api/dataVisualization/interactiveTree', headers=headers,
                     json=payload, timeout=30)
    data = r.json().get('data', [])
    print(f"\n{name}: {len(data)} items")
    for item in data[:5]:
        print(f"  id={item.get('id')}, name={item.get('name')}, type={item.get('type')}")

# Also try to capture what the UI does when loading dashboard page
print("\n\n=== Capturing UI dashboard page API calls ===")
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
    
    api_calls = []
    def on_request(request):
        if '/de2api/' in request.url:
            api_calls.append({
                'method': request.method,
                'url': request.url,
                'post_data': request.post_data
            })
    
    page.on('request', on_request)
    
    # Navigate to dashboard index
    page.goto(f'{base}/#/panel/index', timeout=30000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"Captured {len(api_calls)} API calls:")
    for call in api_calls:
        print(f"  {call['method']} {call['url']}")
        if call['post_data']:
            print(f"    Body: {call['post_data'][:200]}")
    
    # Take screenshot
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dashboard_page.png')
    print("\nScreenshot saved.")
    browser.close()
