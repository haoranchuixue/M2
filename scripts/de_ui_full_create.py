"""Full automated dataset creation through DataEase UI."""
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
    
    # Go directly to the dataset creation form
    page.goto(f'{base}/#/dataset-form?pid=1236043392912330752', timeout=30000)
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    api_log.clear()
    
    # Step 1: Select data source "starrocks"
    print("=== Step 1: Select data source ===")
    ds_selector = page.query_selector('.ed-select')
    if ds_selector:
        ds_selector.click()
        time.sleep(1)
        
        # Look for the starrocks option
        options = page.query_selector_all('.ed-select-dropdown__item, .ed-tree-node')
        print(f"Options/tree nodes: {len(options)}")
        for opt in options:
            text = opt.inner_text().strip()
            if text and len(text) < 100:
                print(f"  Option: '{text}'")
            if 'starrocks' in text.lower():
                print(f"  --> Selecting starrocks")
                opt.click()
                time.sleep(2)
                break
    
    page.screenshot(path='d:/Projects/m2/scripts/de_ds_selected.png')
    
    # Step 2: Wait for tables to load and look for SQL tab or dsp_report table
    print("\n=== Step 2: Look for SQL tab or dsp_report table ===")
    time.sleep(2)
    
    # Look for SQL tab/option
    page_text = page.inner_text('body')
    has_sql = 'SQL' in page_text
    print(f"SQL option on page: {has_sql}")
    
    # Look for tabs
    all_text_els = page.query_selector_all('[class*=tab-item], [class*=radio], [role=tab]')
    for el in all_text_els:
        t = el.inner_text().strip()
        if t and 'SQL' in t:
            print(f"  Found SQL tab: '{t}'")
            el.click()
            time.sleep(2)
            page.screenshot(path='d:/Projects/m2/scripts/de_sql_tab.png')
            break
    
    # Look for the table list
    # In DataEase, after selecting data source, tables appear in the left panel
    # The table list should have dsp_report
    table_items = page.query_selector_all('[class*=table-item], [class*=tree-node]')
    print(f"\nTable/tree items: {len(table_items)}")
    for item in table_items:
        text = item.inner_text().strip()
        if text and len(text) < 100:
            print(f"  Item: '{text}'")
    
    # Try to find dsp_report in the page
    dsp_el = page.query_selector('text="dsp_report"')
    if dsp_el:
        print("\nFound dsp_report, clicking...")
        dsp_el.click()
        time.sleep(3)
        page.screenshot(path='d:/Projects/m2/scripts/de_dsp_selected.png')
    
    # Check what happened
    time.sleep(2)
    
    # Check for tables with checkboxes
    checkboxes = page.query_selector_all('[class*=checkbox]:visible')
    print(f"\nCheckboxes: {len(checkboxes)}")
    
    # Look for save button
    buttons = page.query_selector_all('button:visible')
    for b in buttons:
        text = b.inner_text().strip()
        if text and len(text) < 20:
            print(f"  Button: '{text}'")
    
    # Print captured API calls
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'dataset' in url.lower() or 'datasource' in url.lower() or 'table' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                print(f"    Body: {str(entry['body'])[:500]}")
            if entry.get('response'):
                print(f"    Resp: {str(entry['response'])[:500]}")
    
    browser.close()
