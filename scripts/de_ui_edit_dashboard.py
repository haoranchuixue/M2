"""Open the DSP Report dashboard in edit mode and capture all interactions."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = 1236050016221663232

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
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
    
    def on_response(response):
        url = response.url.split('?')[0]
        if '/de2api/' in url and 'updateCanvas' in url:
            try:
                body = response.json()
                print(f"\n[RESPONSE] {url}: {json.dumps(body, ensure_ascii=False)[:300]}")
            except:
                pass
    
    page.on('request', on_request)
    page.on('response', on_response)
    
    # Navigate to dashboard edit mode
    edit_url = f'{base}/#/dashboard/edit/{dashboard_id}'
    print(f"Navigating to: {edit_url}")
    page.goto(edit_url, timeout=60000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_edit_01.png')
    print("Screenshot: dash_edit_01.png")
    
    # Print captured API calls so far
    print(f"\nCaptured {len(api_calls)} API calls during edit load:")
    for c in api_calls:
        print(f"  {c['method']} {c['url']}")
    
    # Look for any chart/view add buttons
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_edit_02.png', full_page=True)
    
    # Check the page for any interactive elements
    buttons = page.query_selector_all('button')
    print(f"\nButtons found: {len(buttons)}")
    for btn in buttons[:15]:
        text = btn.inner_text().strip()
        if text:
            print(f"  Button: '{text}'")
    
    # Look for sidebar/menu items
    divs = page.query_selector_all('[class*="menu"], [class*="sidebar"], [class*="panel"]')
    print(f"\nMenu/sidebar/panel elements: {len(divs)}")
    for d in divs[:10]:
        cls = d.get_attribute('class')
        txt = d.inner_text()[:80].strip()
        print(f"  class='{cls}', text='{txt}'")
    
    # Check for "添加" or "图表" or "视图" elements
    for text in ['添加', '图表', '视图', 'chart', 'view', '表格']:
        elements = page.query_selector_all(f'text="{text}"')
        if elements:
            print(f"\n  Found '{text}': {len(elements)} elements")
            for el in elements[:3]:
                tag = el.evaluate("e => e.tagName")
                print(f"    tag={tag}, text={el.inner_text()[:50]}")
    
    time.sleep(2)
    browser.close()
    
print("\nDone.")
