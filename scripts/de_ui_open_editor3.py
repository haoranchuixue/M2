"""Click edit icon properly to enter dashboard editor."""
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
    
    # Click DSP Report to select it first
    page.click('text="DSP Report"')
    time.sleep(2)
    
    api_calls.clear()
    
    # Now hover over DSP Report and click the edit icon
    node = page.locator('.custom-tree-node:has-text("DSP Report")').first
    node.hover()
    time.sleep(0.5)
    
    # The icon-more div contains two icons: edit and dropdown
    icon_more = node.locator('.icon-more').first
    # Get both hover-icon elements
    hover_icons = icon_more.locator('.ed-icon.hover-icon')
    count = hover_icons.count()
    print(f"Hover icons in icon-more: {count}")
    
    # The first hover-icon is the edit icon
    if count >= 1:
        edit_icon = hover_icons.nth(0)
        bbox = edit_icon.bounding_box()
        print(f"Edit icon bbox: {bbox}")
        
        # Click directly on the edit icon
        edit_icon.click(force=True)
        time.sleep(8)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        print(f"URL after clicking edit: {page.url}")
        page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_editor_03.png')
        
        print(f"\nAPI calls after edit: {len(api_calls)}")
        for c in api_calls:
            print(f"  {c['method']} {c['url']}")
            if c['post_data']:
                print(f"    Body: {c['post_data'][:300]}")
        
        body = page.inner_text('body')[:500]
        print(f"\nPage content: {body}")
    
    browser.close()

print("Done.")
