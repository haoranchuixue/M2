"""Capture save API call from existing dashboard editing."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
example_id = '985192741891870720'  # 连锁茶饮销售看板
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
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Navigate to panel section  
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        if '仪表板' in item.inner_text():
            item.click()
            time.sleep(3)
            break
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Expand 【官方示例】 and click 连锁茶饮销售看板
    page.wait_for_selector('.ed-tree-node', timeout=10000)
    time.sleep(1)
    
    # Click on 【官方示例】 to expand
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and '官方' in content.inner_text():
            print("Expanding 【官方示例】...")
            content.click()
            time.sleep(2)
            break
    
    # Now find and click 连锁茶饮销售看板
    page.wait_for_timeout(1000)
    all_labels = page.query_selector_all('.ed-tree-node__label')
    for label in all_labels:
        text = label.inner_text().strip()
        if '茶饮' in text:
            print(f"Found: '{text}'")
            label.click()
            time.sleep(3)
            page.wait_for_load_state('networkidle', timeout=15000)
            break
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_example_preview.png')
    
    # Look for edit button
    api_log.clear()
    
    edit_btn = page.locator('button:has-text("编辑")')
    if edit_btn.count() > 0 and edit_btn.first.is_visible():
        print("Clicking edit...")
        edit_btn.first.click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
        print(f"Edit URL: {page.url}")
        page.screenshot(path='d:/Projects/m2/scripts/de_example_edit.png')
        
        # Now save without changes to capture the save API call
        save_btn = page.locator('text=保存')
        if save_btn.count() > 0:
            print("Clicking save...")
            save_btn.first.click()
            time.sleep(5)
            page.wait_for_load_state('networkidle', timeout=15000)
    
    # Print API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if any(kw in url.lower() for kw in ['visual', 'canvas', 'save', 'update', 'find']):
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                fname = f"capture_{url.replace('/', '_').strip('_')}.json"
                with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                    f.write(body_str)
                print(f"    Body saved to {fname} ({len(body_str)} chars)")
                print(f"    Preview: {body_str[:500]}")
            if entry.get('response'):
                resp = str(entry['response'])
                print(f"    Status: {entry.get('status')}")
                print(f"    Resp: {resp[:300]}")
    
    browser.close()
