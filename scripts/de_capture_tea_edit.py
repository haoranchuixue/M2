"""Click the Edit button on tea dashboard and capture the edit mode API calls."""
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
    
    # Navigate to tea dashboard
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    folder = page.locator('text="【官方示例】"').first
    folder.click()
    time.sleep(1)
    
    page.locator('text="连锁茶饮销售看板"').first.click()
    time.sleep(8)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL: {page.url}")
    
    # Now find and click the "编辑" button
    api_calls = []
    def on_request(request):
        if '/de2api/' in request.url:
            api_calls.append({
                'method': request.method,
                'url': request.url.split('?')[0],
                'full_url': request.url,
                'post_data': request.post_data
            })
    page.on('request', on_request)
    
    edit_btn = page.locator('text="编辑"').first
    bbox = edit_btn.bounding_box()
    print(f"Edit button bbox: {bbox}")
    
    if edit_btn.is_visible():
        print("Clicking 编辑 button...")
        edit_btn.click()
        time.sleep(10)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        print(f"URL after edit: {page.url}")
        page.screenshot(path='d:\\Projects\\m2\\scripts\\tea_edit_mode.png')
        
        print(f"\nAPI calls ({len(api_calls)}):")
        for c in api_calls:
            url_short = c['url'].replace(base, '')
            print(f"  {c['method']} {url_short}")
            if c['post_data'] and ('findById' in c['url'] or 'Canvas' in c['url'] or 'save' in c['url'].lower()):
                print(f"    Body: {c['post_data'][:300]}")
        
        body = page.inner_text('body')[:500]
        print(f"\nPage: {body[:400]}")
    
    browser.close()

print("Done.")
