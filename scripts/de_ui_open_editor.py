"""Click the edit icon on DSP Report to open the dashboard editor."""
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
    api_calls.clear()
    
    # Hover over DSP Report node
    node = page.locator('.custom-tree-node:has-text("DSP Report")').first
    node.hover()
    time.sleep(0.5)
    
    # Click the first hover-icon (edit/pencil icon)
    edit_icon = node.locator('.ed-icon.hover-icon').first
    
    # Capture navigation
    with page.expect_navigation(timeout=15000, wait_until='domcontentloaded') as nav_info:
        try:
            edit_icon.click()
        except:
            pass
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL after clicking edit: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_editor_01.png')
    
    print(f"\nAPI calls after edit click: {len(api_calls)}")
    for c in api_calls:
        print(f"  {c['method']} {c['url']}")
        if c['post_data'] and ('findById' in c['url'] or 'Canvas' in c['url']):
            print(f"    Body: {c['post_data'][:300]}")
    
    # Check page content
    body = page.inner_text('body')[:800]
    print(f"\nPage content: {body[:500]}")
    
    browser.close()

print("Done.")
