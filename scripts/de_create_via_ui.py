"""Create dataset via DataEase UI automation with Playwright."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
api_log = []

def on_request(request):
    if '/de2api/' in request.url:
        try:
            body = request.post_data
        except:
            body = None
        api_log.append({
            'url': request.url.replace(base, ''),
            'method': request.method,
            'body': body
        })

def on_response(response):
    if '/de2api/' in response.url:
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
    
    # Clear API log after login
    api_log.clear()
    
    # Find and click root node or "+" button to create a new dataset group
    # Look for the root "数据集" node
    root_nodes = page.query_selector_all('.ed-tree-node__content')
    print(f"Tree nodes found: {len(root_nodes)}")
    for i, node in enumerate(root_nodes):
        text = node.inner_text().strip()
        print(f"  Node {i}: '{text[:50]}'")
    
    # Right-click on the first tree node (root) to see context menu
    if root_nodes:
        print("\nRight-clicking on first tree node...")
        root_nodes[0].click(button='right')
        time.sleep(1)
        page.screenshot(path='d:/Projects/m2/scripts/de_rightclick.png')
        
        # Look for context menu items
        menu_items = page.query_selector_all('.ed-dropdown-menu__item, .el-dropdown-menu__item, [class*=menu-item], [class*=context]')
        print(f"Menu items found: {len(menu_items)}")
        for m in menu_items:
            text = m.inner_text().strip()
            if text:
                print(f"  Menu: '{text}'")
        
        # Also check for any popover/dialog
        dialogs = page.query_selector_all('.ed-dialog, .el-dialog, [class*=dialog], [class*=popover], [class*=dropdown]')
        print(f"Dialogs/popovers: {len(dialogs)}")
        for d in dialogs[:5]:
            text = d.inner_text()[:100]
            if text.strip():
                print(f"  Dialog: '{text}'")
    
    # Try clicking on "数据集" text directly
    dataset_label = page.query_selector('text="数据集"')
    if dataset_label:
        print("\nFound '数据集' label, clicking...")
        dataset_label.click()
        time.sleep(1)
    
    # Look for any buttons with + icon or "新建"
    all_els = page.query_selector_all('*')
    for el in all_els:
        try:
            text = el.inner_text()
            if '新建' in text and len(text) < 20:
                print(f"  Found '新建': tag={el.evaluate('e=>e.tagName')}, text='{text}'")
        except:
            pass
    
    # Check for "+" icon buttons
    plus_btns = page.query_selector_all('[class*="plus"], [class*="add"], [class*="create"]')
    print(f"\nPlus/Add buttons: {len(plus_btns)}")
    for b in plus_btns[:5]:
        cls = b.get_attribute('class') or ''
        print(f"  Class: {cls[:100]}")
    
    page.screenshot(path='d:/Projects/m2/scripts/de_dataset_ui.png')
    
    # Print any captured API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        if entry.get('method') == 'POST':
            print(f"  {entry['method']} {entry['url']}")
            if entry.get('body'):
                print(f"    Body: {str(entry['body'])[:300]}")
    
    browser.close()
