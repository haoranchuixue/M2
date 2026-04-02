"""Create SQL dataset through DataEase UI with Playwright."""
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
            'ts': time.time()
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
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    api_log.clear()
    
    # Look for the "DSP Report" folder and interact with it
    # In DataEase, the left side tree shows dataset folders
    # Let me hover over the DSP Report folder to reveal action buttons
    
    # Find the DSP Report node
    tree_nodes = page.query_selector_all('.ed-tree-node')
    print(f"Total tree nodes: {len(tree_nodes)}")
    
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content:
            text = content.inner_text().strip()
            if 'DSP Report' in text:
                print(f"Found DSP Report node, hovering...")
                content.hover()
                time.sleep(1)
                page.screenshot(path='d:/Projects/m2/scripts/de_hover_dsp.png')
                
                # Look for action buttons that appeared
                action_btns = node.query_selector_all('button, [class*=icon], [class*=more], [class*=action], svg')
                print(f"Action elements: {len(action_btns)}")
                for ab in action_btns:
                    cls = ab.get_attribute('class') or ''
                    tag = ab.evaluate('e => e.tagName')
                    print(f"  Tag: {tag}, Class: {cls[:80]}")
                
                # Try clicking on the "more" or "..." button
                more_btn = node.query_selector('[class*=more], [class*=icon-more], .ed-icon--more')
                if more_btn:
                    print("Found more button, clicking...")
                    more_btn.click()
                    time.sleep(1)
                else:
                    # Try right-click on the node
                    print("No more button found, trying right-click...")
                    content.click(button='right')
                    time.sleep(1)
                
                page.screenshot(path='d:/Projects/m2/scripts/de_context_menu.png')
                
                # Look for dropdown/context menu
                menus = page.query_selector_all('.ed-dropdown-menu, .el-dropdown-menu, [class*=dropdown-menu]')
                for menu in menus:
                    if menu.is_visible():
                        items = menu.query_selector_all('li, [class*=item]')
                        print(f"Menu items ({len(items)}):")
                        for item in items:
                            text = item.inner_text().strip()
                            if text:
                                print(f"  '{text}'")
                                if '新建' in text or 'SQL' in text or '数据集' in text:
                                    print(f"  --> Clicking '{text}'")
                                    item.click()
                                    time.sleep(2)
                                    page.screenshot(path='d:/Projects/m2/scripts/de_after_click_create.png')
                                    break
                break
    
    # Wait and check for any dialog
    time.sleep(2)
    page.screenshot(path='d:/Projects/m2/scripts/de_after_action.png')
    
    # Check for any dialog/form
    dialogs = page.query_selector_all('[class*=dialog], [class*=drawer]')
    for d in dialogs:
        if d.is_visible():
            text = d.inner_text()[:500]
            print(f"\nVisible dialog/drawer: {text}")
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'dataset' in url.lower() or 'datasource' in url.lower() or 'sql' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                print(f"    Body: {str(entry['body'])[:500]}")
            if entry.get('response'):
                print(f"    Resp: {str(entry['response'])[:500]}")
    
    browser.close()
