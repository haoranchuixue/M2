"""Capture API calls when creating dataset in DataEase UI."""
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
            'body': body[:500] if body else None
        })

def on_response(response):
    if '/de2api/' in response.url and response.request.method == 'POST':
        for entry in api_log:
            if entry['url'] == response.url.replace(base, '') and 'response' not in entry:
                try:
                    entry['response'] = response.body().decode('utf-8', errors='replace')[:1000]
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
    print(f"Logged in, URL: {page.url}")
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    page.screenshot(path='d:/Projects/m2/scripts/de_dataset_page.png')
    print(f"Dataset page, URL: {page.url}")
    
    # Look for create/add button
    buttons = page.query_selector_all('button')
    for b in buttons:
        text = b.inner_text().strip()
        if text:
            print(f"  Button: '{text}'")
    
    # Also look for any "+" or "新建" icons/links
    add_elements = page.query_selector_all('[class*=add], [class*=create], [class*=new]')
    for el in add_elements:
        print(f"  Add element: {el.get_attribute('class')}: {el.inner_text()[:50]}")
    
    # Try clicking the add/create button for datasets
    # In DataEase v2, the dataset creation is done in the left sidebar
    # Look for specific elements
    page.screenshot(path='d:/Projects/m2/scripts/de_dataset_page2.png')
    
    # Try to find the dataset creation trigger
    # Let me look at the page structure
    html = page.content()
    # Find elements with "新建" or "新增" or "创建" text
    for text in ['新建', '新增', '创建', '添加']:
        els = page.query_selector_all(f'text="{text}"')
        if els:
            print(f"  Found elements with text '{text}': {len(els)}")
            for el in els[:3]:
                tag = el.evaluate('e => e.tagName')
                cls = el.get_attribute('class') or ''
                print(f"    Tag: {tag}, Class: {cls[:80]}")
    
    # Look at the sidebar navigation
    nav = page.query_selector_all('.el-tree-node, .tree-node, [class*=tree]')
    print(f"\nTree nodes: {len(nav)}")
    for n in nav[:10]:
        text = n.inner_text()[:100]
        print(f"  Node: {text}")
    
    # Look for icon buttons
    icons = page.query_selector_all('.el-icon, [class*=icon], svg')
    print(f"\nIcon elements: {len(icons)}")
    
    # Let me try right-clicking on the root folder to see context menu
    root_node = page.query_selector('.ed-tree-node__content')
    if root_node:
        print(f"\nRoot node found: {root_node.inner_text()[:50]}")
        root_node.click()
        time.sleep(1)
    
    # Print captured API calls for dataset page
    print(f"\n=== Captured API calls ({len(api_log)}) ===")
    for entry in api_log:
        if 'dataset' in entry['url'].lower() or 'data' in entry['url'].lower():
            print(f"\n  {entry['method']} {entry['url']}")
            if entry.get('body'):
                print(f"    Body: {entry['body'][:300]}")
            if entry.get('response'):
                print(f"    Resp: {entry['response'][:300]}")
    
    browser.close()
