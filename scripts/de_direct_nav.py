"""Navigate directly to DSP Report dashboard via URL and capture data loading."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dsp_id = '1236050016221663232'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
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
    print("Logged in")
    
    # Track responses
    api_calls = []
    def on_response(response):
        if '/de2api/' in response.url:
            url_short = response.url.replace(base + '/de2api/', '')
            try:
                body = response.json()
                code = body.get('code', 'N/A')
                msg = str(body.get('msg', ''))[:100]
                api_calls.append(f"[{response.status}] {url_short}: code={code}")
            except:
                api_calls.append(f"[{response.status}] {url_short}")
    page.on('response', on_response)
    
    console_errors = []
    page.on('console', lambda msg: console_errors.append(f"[{msg.type}] {msg.text[:300]}"))
    
    # Navigate directly with dvId
    print(f"Navigating to: {base}/#/panel/index?dvId={dsp_id}")
    page.goto(f'{base}/#/panel/index?dvId={dsp_id}', timeout=60000, wait_until='domcontentloaded')
    
    # Wait for chart data to load
    for wait in [10, 30, 60, 90]:
        time.sleep(10 if wait == 10 else 20 if wait == 30 else 30)
        print(f"\n--- After {wait}s ---")
        print(f"URL: {page.url}")
        new_calls = [c for c in api_calls if 'findById' in c or 'getData' in c or 'chartData' in c]
        print(f"Relevant API calls: {len(new_calls)}")
        for c in new_calls:
            print(f"  {c}")
        page.screenshot(path=f'd:/Projects/m2/scripts/ss_direct_{wait}.png')
        
        # Check for table rendering
        table_count = page.evaluate("document.querySelectorAll('table, [class*=table], [class*=Table]').length")
        print(f"Table elements: {table_count}")
        
        if wait >= 60:
            break
    
    print(f"\n=== All relevant API calls ===")
    for c in api_calls:
        if 'findById' in c or 'getData' in c or 'chartData' in c or 'linkage' in c:
            print(f"  {c}")
    
    print(f"\n=== Console messages ({len(console_errors)}) ===")
    for e in console_errors[:20]:
        print(f"  {e}")
    
    browser.close()
