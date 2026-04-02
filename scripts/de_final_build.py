"""Final comprehensive build: create dashboard and table chart."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time
import requests

base = 'http://47.236.78.123:8100'
api_log = []

def on_request(request):
    if '/de2api/' in request.url and request.method == 'POST':
        try:
            body = request.post_data
        except:
            body = None
        api_log.append({
            'url': request.url.replace(base, ''),
            'method': request.method,
            'body': body,
        })

def on_response(response):
    if '/de2api/' in response.url and response.request.method == 'POST':
        for entry in reversed(api_log):
            if entry['url'] == response.url.replace(base, '') and 'response' not in entry:
                try:
                    entry['response'] = response.body().decode('utf-8', errors='replace')
                    entry['status'] = response.status
                except:
                    pass
                break

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Login
    print("Logging in...")
    page.goto(f'{base}/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Wait for login form specifically
    page.wait_for_selector('input[type="text"]', timeout=10000)
    time.sleep(1)
    
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    time.sleep(0.3)
    inputs[1].fill('DataEase@123456')
    time.sleep(0.3)
    
    # Click login button
    page.query_selector('button').click()
    
    # Wait for redirect to workbranch
    page.wait_for_url('**/workbranch/**', timeout=30000)
    time.sleep(3)
    print(f"Logged in: {page.url}")
    
    # Get token from browser
    token_raw = page.evaluate("() => localStorage.getItem('user.token')")
    token_obj = json.loads(token_raw)
    jwt = json.loads(token_obj['v'])
    headers = {'x-de-token': jwt, 'Content-Type': 'application/json'}
    
    # Check existing dashboards
    r = requests.post(f'{base}/de2api/dataVisualization/tree', headers=headers, 
                      json={'busiFlag': 'panel'}, timeout=15)
    tree = r.json()
    print(f"\nExisting dashboard tree: {json.dumps(tree, ensure_ascii=False)[:500]}")
    
    # Navigate to dashboard section via sidebar
    print("\nNavigating to dashboards...")
    # Wait for sidebar to load
    page.wait_for_selector('[class*=menu-item]', timeout=10000)
    time.sleep(1)
    
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        text = item.inner_text().strip()
        if '仪表板' == text:
            item.click()
            time.sleep(3)
            break
    
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"Dashboard page: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_final_dashboard.png')
    
    # Now look for tree nodes
    page.wait_for_selector('.ed-tree-node', timeout=10000)
    time.sleep(1)
    
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Tree nodes: {len(tree_nodes)}")
    
    api_log.clear()
    
    # Hover on first tree node and click create icon
    if tree_nodes:
        content = tree_nodes[0].query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            print(f"First node: '{text}'")
            content.hover()
            time.sleep(1)
            
            hover_icons = content.query_selector_all('.hover-icon')
            print(f"Hover icons: {len(hover_icons)}")
            
            if hover_icons:
                hover_icons[0].click()
                time.sleep(1)
                page.screenshot(path='d:/Projects/m2/scripts/de_final_dropdown.png')
                
                # Wait for dropdown and click 新建仪表板
                page.wait_for_timeout(500)
                
                # Use locator to find and click
                try:
                    page.locator('li:has-text("新建仪表板")').click(timeout=3000)
                    print("Clicked '新建仪表板'")
                except:
                    # Try alternative selector
                    try:
                        page.locator('text=新建仪表板').click(timeout=3000)
                        print("Clicked '新建仪表板' (alt)")
                    except:
                        print("Could not find '新建仪表板'")
                        # Let's see what's in the dropdown
                        page.screenshot(path='d:/Projects/m2/scripts/de_final_dropdown2.png')
                        all_li = page.query_selector_all('li:visible')
                        for li in all_li:
                            lt = li.inner_text().strip()
                            if lt:
                                print(f"  li: '{lt}'")
                
                time.sleep(5)
                page.wait_for_load_state('networkidle', timeout=30000)
                print(f"\nURL after create: {page.url}")
                page.screenshot(path='d:/Projects/m2/scripts/de_final_editor.png')
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if len(api_log) < 20 or any(kw in url.lower() for kw in ['visual', 'panel', 'save', 'chart', 'create']):
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                if len(body_str) > 5000:
                    fname = f"final_{url.replace('/', '_').strip('_')}.json"
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body saved to {fname}")
                else:
                    print(f"    Body: {body_str[:500]}")
            if entry.get('response'):
                print(f"    Resp: {str(entry['response'])[:500]}")
    
    browser.close()
