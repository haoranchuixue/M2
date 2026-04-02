"""Open DSP Report in edit mode and explore the editor."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = 1236050016221663232

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
    
    # Click on DSP Report to select it
    page.click('text="DSP Report"')
    time.sleep(2)
    
    # Now click the edit (pencil) icon next to DSP Report
    # The edit icon should be a small pencil/edit button near DSP Report
    edit_icon = page.locator('.ed-icon-edit, [class*="edit"]').first
    print("Looking for edit icon...")
    
    # Try to find the edit icon by looking at SVG icons or specific classes near DSP Report
    # From the screenshot, there's a pencil icon after "DSP Report"
    dsp_item = page.locator('text="DSP Report"').first
    parent = dsp_item.locator('..')
    
    # Find all clickable elements near DSP Report
    nearby = parent.locator('svg, i, span[class*="icon"], .ed-icon')
    count = nearby.count()
    print(f"Found {count} icon elements near DSP Report")
    
    # Try clicking the first icon-like element (the pencil/edit icon)
    if count > 0:
        for i in range(count):
            el = nearby.nth(i)
            try:
                cls = el.get_attribute('class') or ''
                tag = el.evaluate("e => e.tagName")
                print(f"  Icon {i}: tag={tag}, class={cls[:50]}")
            except:
                pass

    # Alternative: directly navigate to the edit URL pattern
    # Try #/dashboard/edit/ID
    api_calls.clear()
    print(f"\nTrying direct URL: {base}/#/dvCanvas?dvId={dashboard_id}&opt=edit")
    page.goto(f'{base}/#/dvCanvas?dvId={dashboard_id}&opt=edit', timeout=60000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_edit_direct_01.png')
    print(f"URL: {page.url}")
    print(f"API calls: {len(api_calls)}")
    for c in api_calls[:10]:
        print(f"  {c['method']} {c['url']}")
        if c['post_data'] and 'findById' in c['url']:
            print(f"    Body: {c['post_data'][:200]}")

    # Check page content
    body_text = page.inner_text('body')[:500]
    print(f"\nPage content: {body_text[:300]}")
    
    browser.close()

print("Done.")
