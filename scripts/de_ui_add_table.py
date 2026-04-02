"""Add dsp_report table to dataset and save via UI."""
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
    
    # Go to dataset creation form
    page.goto(f'{base}/#/dataset-form?pid=1236043392912330752', timeout=30000)
    time.sleep(3)
    api_log.clear()
    
    # Select starrocks data source
    ds_selector = page.query_selector('.ed-select')
    ds_selector.click()
    time.sleep(1)
    page.query_selector('text="starrocks"').click()
    time.sleep(2)
    
    # Double-click on dsp_report to add it
    dsp_el = page.query_selector('text="dsp_report"')
    if dsp_el:
        print("Double-clicking dsp_report...")
        dsp_el.dblclick()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:/Projects/m2/scripts/de_dblclick.png')
    
    # Check if fields are loaded
    print(f"\nURL: {page.url}")
    
    # Check the field tables
    rows = page.query_selector_all('tr:visible')
    print(f"Visible table rows: {len(rows)}")
    for row in rows[:5]:
        text = row.inner_text().strip()
        if text:
            print(f"  Row: {text[:100]}")
    
    # Now set the name and save
    name_input = page.query_selector('input[type="text"]')
    if name_input:
        name_input.fill('DSP Report Data')
        time.sleep(0.5)
    
    # Click Save
    print("\nClicking Save...")
    # The save button might not be directly "保存" text
    buttons = page.query_selector_all('button:visible')
    for b in buttons:
        text = b.inner_text().strip()
        if '保存' in text and '返回' not in text:
            print(f"  Found save button: '{text}'")
            b.click()
            time.sleep(5)
            page.wait_for_load_state('networkidle', timeout=15000)
            break
    
    page.screenshot(path='d:/Projects/m2/scripts/de_after_save2.png')
    
    # Print ALL API calls
    print(f"\n=== ALL API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        print(f"\n  POST {url}")
        if entry.get('body'):
            body_str = str(entry['body'])
            if len(body_str) > 3000:
                # Save to file
                fname = url.replace('/', '_').replace('de2api_', '') + '.json'
                with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                    f.write(body_str)
                print(f"    Body saved to {fname} ({len(body_str)} chars)")
                print(f"    Preview: {body_str[:500]}")
            else:
                print(f"    Body: {body_str[:500]}")
        if entry.get('response'):
            resp_str = str(entry['response'])
            print(f"    Status: {entry.get('status')}")
            print(f"    Resp: {resp_str[:500]}")
    
    browser.close()
