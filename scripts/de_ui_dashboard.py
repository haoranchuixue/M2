"""Create dashboard through DataEase UI and capture API calls."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

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
    page = browser.new_page()
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Login
    page.goto(f'{base}/', timeout=30000)
    page.wait_for_load_state('networkidle', timeout=30000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Navigate to dashboard page
    page.goto(f'{base}/#/panel/index', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    api_log.clear()
    
    page.screenshot(path='d:/Projects/m2/scripts/de_dashboard_page.png')
    print(f"URL: {page.url}")
    
    # Look for create button - hover on the root node
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Tree nodes: {len(tree_nodes)}")
    
    # Try hovering on first node to find create button
    for node in tree_nodes[:3]:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            print(f"  Node: '{text}'")
            if text:
                content.hover()
                time.sleep(1)
                hover_icons = node.query_selector_all('.hover-icon')
                for i, icon in enumerate(hover_icons):
                    icon.hover()
                    time.sleep(0.5)
                    tooltips = page.query_selector_all('[role=tooltip], .ed-popper')
                    for tt in tooltips:
                        if tt.is_visible():
                            tt_text = tt.inner_text().strip()
                            if tt_text:
                                print(f"    Icon {i} tooltip: '{tt_text}'")
                
                # Click the first hover icon (should be create)
                if hover_icons:
                    hover_icons[0].click()
                    time.sleep(1)
                    
                    # Check for dropdown menu
                    dropdowns = page.query_selector_all('.ed-dropdown-menu')
                    for dd in dropdowns:
                        if dd.is_visible():
                            items = dd.query_selector_all('li')
                            for item in items:
                                t = item.inner_text().strip()
                                if t:
                                    print(f"    Dropdown: '{t}'")
                                    # Click "新建仪表板" if found
                                    if '仪表板' in t and '新建' in t:
                                        print(f"    --> Clicking '{t}'")
                                        item.click()
                                        time.sleep(3)
                                        page.wait_for_load_state('networkidle', timeout=15000)
                                        break
                    break
    
    page.screenshot(path='d:/Projects/m2/scripts/de_after_create_db.png')
    print(f"\nURL after create: {page.url}")
    
    # Check if a dialog appeared asking for dashboard name
    visible_inputs = page.query_selector_all('input:visible')
    for inp in visible_inputs:
        ph = inp.get_attribute('placeholder') or ''
        val = inp.input_value()
        print(f"  Input: placeholder='{ph}', value='{val}'")
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'visual' in url.lower() or 'panel' in url.lower() or 'save' in url.lower() or 'create' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                if len(body_str) > 3000:
                    with open(f'd:/Projects/m2/scripts/dashboard_create_body.json', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body saved ({len(body_str)} chars)")
                    print(f"    Preview: {body_str[:1000]}")
                else:
                    print(f"    Body: {body_str[:1000]}")
            if entry.get('response'):
                resp_str = str(entry['response'])
                print(f"    Resp: {resp_str[:500]}")
    
    browser.close()
