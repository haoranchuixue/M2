"""Click 'Create Dataset' and capture the full creation flow."""
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
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000)
    time.sleep(3)
    api_log.clear()
    
    # Find DSP Report node, hover, click first hover icon, then click "新建数据集"
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and 'DSP Report' in content.inner_text():
            content.hover()
            time.sleep(1)
            
            hover_icons = node.query_selector_all('.hover-icon')
            if hover_icons:
                hover_icons[0].click()
                time.sleep(1)
                
                # Click "新建数据集"
                create_ds = page.query_selector('text="新建数据集"')
                if create_ds:
                    print("Clicking '新建数据集'...")
                    create_ds.click()
                    time.sleep(3)
                    page.wait_for_load_state('networkidle', timeout=15000)
                    
                    print(f"URL after create: {page.url}")
                    page.screenshot(path='d:/Projects/m2/scripts/de_create_ds_form.png')
                    
                    # Describe the current page
                    # Look for form elements
                    all_inputs = page.query_selector_all('input:visible, textarea:visible, select:visible')
                    print(f"\nVisible inputs: {len(all_inputs)}")
                    for inp in all_inputs:
                        ph = inp.get_attribute('placeholder') or ''
                        tp = inp.get_attribute('type') or ''
                        val = inp.input_value() if tp != 'file' else ''
                        print(f"  Input: type={tp}, placeholder={ph}, value={val[:50]}")
                    
                    # Look for tabs/radio buttons for dataset type
                    tabs = page.query_selector_all('[class*=tab], [class*=radio], [role=tab]')
                    for tab in tabs:
                        text = tab.inner_text().strip()
                        if text:
                            print(f"  Tab/Radio: '{text}'")
                    
                    # Look for "SQL" option
                    sql_option = page.query_selector('text="SQL"')
                    if sql_option:
                        print("\nFound SQL option, clicking...")
                        sql_option.click()
                        time.sleep(2)
                        page.screenshot(path='d:/Projects/m2/scripts/de_sql_option.png')
                    
                    # Look for datasource selector
                    selects = page.query_selector_all('.ed-select:visible, [class*=select]:visible')
                    print(f"\nSelects: {len(selects)}")
                    for s in selects:
                        text = s.inner_text()[:50]
                        print(f"  Select: '{text}'")
                    
                    # Check for any dropdowns that might have "数据库表" / "SQL" tabs
                    page_text = page.inner_text('body')
                    for keyword in ['SQL', '数据库表', '数据源', '表名', 'starrocks']:
                        if keyword in page_text:
                            print(f"  Found '{keyword}' on page")
            break
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        print(f"  POST {url}")
        if entry.get('body'):
            print(f"    Body: {str(entry['body'])[:500]}")
        if entry.get('response'):
            print(f"    Resp: {str(entry['response'])[:500]}")
    
    browser.close()
