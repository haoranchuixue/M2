"""Check the existing example dashboard '连锁茶饮销售看板' to study working chart structure."""
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

# First, find the tea dashboard by navigating via Playwright and capturing the dvId
# Use Playwright to click on it and capture the ID from the URL
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    # Set token in localStorage
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
        if '/de2api/' in request.url and 'findById' in request.url:
            api_calls.append({
                'url': request.url,
                'post_data': request.post_data
            })
    page.on('request', on_request)
    
    # Navigate to dashboard page
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Expand example folder and click tea dashboard
    folder = page.locator('text="【官方示例】"').first
    folder.click()
    time.sleep(1)
    
    tea = page.locator('text="连锁茶饮销售看板"').first
    tea.click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL: {page.url}")
    # Extract dvId from URL
    import re
    match = re.search(r'dvId=(\d+)', page.url)
    if match:
        tea_id = int(match.group(1))
        print(f"Tea dashboard ID: {tea_id}")
    
    # Also check API calls
    print(f"\nfindById calls: {len(api_calls)}")
    for c in api_calls:
        print(f"  {c['url']}")
        print(f"  Body: {c['post_data']}")
    
    browser.close()

# Now fetch the tea dashboard details
if match:
    print(f"\n=== Fetching tea dashboard details ===")
    r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                     json={"id": tea_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
    data = r.json().get('data', {})
    
    views = data.get('canvasViewInfo', {})
    comp_str = data.get('componentData', '[]')
    
    print(f"Name: {data.get('name')}")
    print(f"Status: {data.get('status')}")
    print(f"Views count: {len(views)}")
    print(f"Components length: {len(comp_str)}")
    
    if views:
        # Save the first view for study
        for vid, vdata in views.items():
            print(f"\n--- View {vid} ---")
            print(f"  Type: {vdata.get('type')}")
            print(f"  Title: {vdata.get('title')}")
            print(f"  Keys: {list(vdata.keys())}")
            
            # Save full view
            with open(f'd:\\Projects\\m2\\scripts\\tea_view_{vid[:20]}.json', 'w', encoding='utf-8') as f:
                json.dump(vdata, f, indent=2, ensure_ascii=False)
            print(f"  Saved to tea_view_{vid[:20]}.json")
        
        # Save full dashboard data
        with open('d:\\Projects\\m2\\scripts\\tea_dashboard_full.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\nSaved full dashboard to tea_dashboard_full.json")
    else:
        print("No views found!")
        # Try with different busiFlag
        for flag in ['dashboard', 'dataV', 'panel']:
            r2 = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                             json={"id": tea_id, "busiFlag": flag}, timeout=30)
            d2 = r2.json().get('data', {})
            v2 = d2.get('canvasViewInfo', {})
            print(f"  busiFlag='{flag}': views={len(v2)}, status={d2.get('status')}")
