"""Click the quick create dashboard button in the sidebar."""
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
    
    # Click the quick create "仪表板" (index 2, at y~362)
    all_dashboard = page.locator('text="仪表板"').all()
    for i, el in enumerate(all_dashboard):
        bbox = el.bounding_box()
        if bbox and bbox['y'] > 300:
            print(f"Clicking quick create 仪表板 (#{i}) at {bbox}")
            el.click()
            time.sleep(8)
            page.wait_for_load_state('networkidle', timeout=15000)
            
            print(f"URL: {page.url}")
            page.screenshot(path='d:\\Projects\\m2\\scripts\\new_dash_create.png')
            
            print(f"\nAPI calls: {len(api_calls)}")
            for c in api_calls:
                print(f"  {c['method']} {c['url']}")
                if c['post_data']:
                    print(f"    Body: {c['post_data'][:300]}")
            
            body = page.inner_text('body')[:500]
            print(f"\nPage: {body[:400]}")
            break
    
    browser.close()

print("Done.")
