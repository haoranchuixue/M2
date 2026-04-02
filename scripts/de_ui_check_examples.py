"""Check the example dashboards in 【官方示例】 to see a working edit flow."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
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
    
    api_calls = []
    def on_request(request):
        if '/de2api/' in request.url:
            api_calls.append({
                'method': request.method,
                'url': request.url.split('?')[0],
                'post_data': request.post_data
            })
    page.on('request', on_request)
    
    # Navigate to dashboard page
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Expand 【官方示例】 folder
    folder = page.locator('text="【官方示例】"').first
    folder.click()
    time.sleep(2)
    page.screenshot(path='d:\\Projects\\m2\\scripts\\examples_01.png')
    
    # Check what's in the folder
    tree_items = page.query_selector_all('.custom-tree-node')
    for item in tree_items:
        txt = item.inner_text()[:60].strip()
        print(f"  Tree item: '{txt}'")
    
    # Find an example dashboard
    example_dashboards = page.locator('.custom-tree-node').all()
    for item in example_dashboards:
        txt = item.inner_text()[:60].strip()
        if txt and txt not in ['DSP Report', 'mchat1', '【官方示例】']:
            print(f"\nFound example: '{txt}'")
            # Hover and click edit icon
            api_calls.clear()
            item.hover()
            time.sleep(0.5)
            
            # Click the edit icon
            edit_icon = item.locator('.icon-more .ed-icon.hover-icon').first
            if edit_icon.is_visible():
                print("Clicking edit icon...")
                edit_icon.click(force=True)
                time.sleep(8)
                page.wait_for_load_state('networkidle', timeout=15000)
                
                print(f"URL: {page.url}")
                page.screenshot(path='d:\\Projects\\m2\\scripts\\example_editor.png')
                
                print(f"API calls: {len(api_calls)}")
                for c in api_calls:
                    print(f"  {c['method']} {c['url']}")
                    if c['post_data'] and 'findById' in c['url']:
                        print(f"    Body: {c['post_data'][:300]}")
                
                body = page.inner_text('body')[:500]
                print(f"Page: {body[:300]}")
            break
    
    browser.close()

print("Done.")
