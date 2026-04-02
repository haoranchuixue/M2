"""Complete end-to-end build: create dataset from dsp_report, then create dashboard."""
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
    page.wait_for_load_state('networkidle', timeout=15000)
    api_log.clear()
    
    # Select starrocks data source
    ds_selector = page.query_selector('.ed-select')
    ds_selector.click()
    time.sleep(1)
    
    starrocks_opt = page.query_selector('text="starrocks"')
    if starrocks_opt:
        starrocks_opt.click()
        time.sleep(2)
    
    # Click on dsp_report table
    dsp_el = page.query_selector('text="dsp_report"')
    if dsp_el:
        dsp_el.click()
        time.sleep(3)
    
    page.screenshot(path='d:/Projects/m2/scripts/de_before_save.png')
    
    # Set the dataset name
    # The name input should be at the top
    name_input = page.query_selector('input[type="text"]')
    if name_input:
        current_val = name_input.input_value()
        print(f"Current name: '{current_val}'")
        name_input.fill('DSP Report Data')
        time.sleep(0.5)
    
    # Click Save
    print("Clicking Save...")
    save_btn = page.query_selector('text="保存"')
    if save_btn:
        save_btn.click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=30000)
    
    page.screenshot(path='d:/Projects/m2/scripts/de_after_save.png')
    print(f"URL after save: {page.url}")
    
    # Print API calls to understand the save request
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'save' in url.lower() or 'dataset' in url.lower() or 'table' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                if len(body_str) > 5000:
                    # Save to file
                    with open('d:/Projects/m2/scripts/save_request.json', 'w', encoding='utf-8') as f:
                        f.write(body_str)
                    print(f"    Body: (saved to save_request.json, {len(body_str)} chars)")
                    print(f"    Body preview: {body_str[:1000]}")
                else:
                    print(f"    Body: {body_str}")
            if entry.get('response'):
                print(f"    Resp: {str(entry['response'])[:500]}")
    
    # Check if save was successful
    for entry in api_log:
        if 'save' in entry['url'].lower() and entry.get('response'):
            resp = json.loads(entry['response'])
            if resp.get('code') == 0:
                print(f"\n*** Save successful! ***")
                ds_id = resp.get('data', {}).get('id') if isinstance(resp.get('data'), dict) else resp.get('data')
                print(f"Dataset ID: {ds_id}")
            else:
                print(f"\n*** Save failed: code={resp.get('code')}, msg={resp.get('msg')} ***")
    
    browser.close()
