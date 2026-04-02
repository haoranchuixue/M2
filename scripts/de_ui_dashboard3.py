"""Navigate to dashboard page via sidebar click and create dashboard."""
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
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Click "仪表板" in sidebar
    sidebar_items = page.query_selector_all('[class*=menu-item], [class*=nav-item]')
    for item in sidebar_items:
        text = item.inner_text().strip()
        if text == '仪表板':
            print(f"Clicking sidebar '仪表板'...")
            item.click()
            time.sleep(3)
            page.wait_for_load_state('networkidle', timeout=15000)
            break
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_dashboard_nav.png')
    api_log.clear()
    
    # Now look for tree nodes and create button
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Tree nodes: {len(tree_nodes)}")
    for node in tree_nodes[:10]:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            print(f"  '{text}'")
    
    # If there are existing dashboards, look for create button
    # Find root or first folder node and hover to get create button
    if tree_nodes:
        # Hover on first node
        first_content = tree_nodes[0].query_selector('.ed-tree-node__content')
        if first_content:
            first_content.hover()
            time.sleep(1)
            hover_icons = tree_nodes[0].query_selector_all('.hover-icon')
            print(f"\nHover icons on first node: {len(hover_icons)}")
            
            for i, icon in enumerate(hover_icons):
                icon.hover()
                time.sleep(0.5)
                tooltips = page.query_selector_all('[role=tooltip], .ed-popper')
                for tt in tooltips:
                    if tt.is_visible():
                        print(f"  Icon {i}: '{tt.inner_text().strip()}'")
            
            if hover_icons:
                hover_icons[0].click()
                time.sleep(1)
                
                # Check for dropdown
                dropdowns = page.query_selector_all('.ed-dropdown-menu')
                for dd in dropdowns:
                    if dd.is_visible():
                        items = dd.query_selector_all('li')
                        for item in items:
                            t = item.inner_text().strip()
                            if t:
                                print(f"  Dropdown: '{t}'")
                                if '新建仪表板' in t:
                                    print(f"  --> Clicking '{t}'")
                                    item.click()
                                    time.sleep(5)
                                    page.wait_for_load_state('networkidle', timeout=30000)
                                    break
    
    print(f"\nURL after create: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_new_dashboard.png')
    
    # Print captured API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'visual' in url.lower() or 'panel' in url.lower() or 'save' in url.lower() or 'chart' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                if len(body_str) > 3000:
                    fname = f"db_{url.replace('/', '_').strip('_')}.json"
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body saved to {fname} ({len(body_str)} chars)")
                    print(f"    Preview: {body_str[:500]}")
                else:
                    print(f"    Body: {body_str[:500]}")
            if entry.get('response'):
                resp_str = str(entry['response'])
                print(f"    Resp: {resp_str[:500]}")
    
    browser.close()
