"""List dashboards - check raw responses."""
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

# Check raw responses
for flag in ['dashboard', 'dataV', 'panel', '']:
    r = requests.post(f'{base}/de2api/dataVisualization/interactiveTree', headers=headers,
                     json={"busiFlag": flag} if flag else {}, timeout=30)
    raw = r.json()
    print(f"\nbusiFlag='{flag}': code={raw.get('code')}, data type={type(raw.get('data')).__name__}")
    data = raw.get('data')
    if isinstance(data, list):
        print(f"  Count: {len(data)}")
        for item in data[:3]:
            print(f"  {json.dumps(item, ensure_ascii=False)[:200]}")
    elif isinstance(data, dict):
        print(f"  Keys: {list(data.keys())[:10]}")
        print(f"  Preview: {json.dumps(data, ensure_ascii=False)[:300]}")
    else:
        print(f"  Value: {data}")

# Try findById on our dashboard directly
print("\n\n=== Direct findById on our dashboard ===")
dashboard_id = 1236050016221663232
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard"}, timeout=30)
raw = r.json()
print(f"Status: {r.status_code}, Code: {raw.get('code')}")
data = raw.get('data', {})
if data:
    print(f"Keys: {list(data.keys())}")
    print(f"Name: {data.get('name')}")
    print(f"Status: {data.get('status')}")
    comp = data.get('componentData', '')
    views = data.get('canvasViewInfo', {})
    print(f"componentData length: {len(comp)}")
    print(f"componentData: {comp[:500]}")
    print(f"canvasViewInfo type: {type(views).__name__}")
    print(f"canvasViewInfo: {json.dumps(views, ensure_ascii=False)[:500]}")
    
    # Save full response
    with open('d:\\Projects\\m2\\scripts\\our_dashboard_full.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved full response to our_dashboard_full.json")
