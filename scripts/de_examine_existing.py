"""Examine existing dataset structure by navigating to it in the UI."""
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
    
    # Navigate to an existing dataset to see its API calls
    # The 茶饮原料费用 dataset has id=985189703189925888
    print("Navigating to existing dataset...")
    page.goto(f'{base}/#/dataset-form?id=985189703189925888', timeout=30000)
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:/Projects/m2/scripts/de_existing_dataset.png')
    print(f"URL: {page.url}")
    
    # Print captured API calls - especially the dataset detail/load call
    print(f"\n=== API calls ({len(api_log)}) ===")
    for entry in api_log:
        url = entry['url']
        if 'dataset' in url.lower() or 'field' in url.lower() or 'table' in url.lower():
            print(f"\n  POST {url}")
            if entry.get('body'):
                body_str = str(entry['body'])
                print(f"    Body: {body_str[:500]}")
            if entry.get('response'):
                resp_str = str(entry['response'])
                if len(resp_str) > 5000:
                    fname = f"existing_{url.replace('/', '_').strip('_')}.json"
                    with open(f'd:/Projects/m2/scripts/{fname}', 'w', encoding='utf-8') as f:
                        f.write(resp_str)
                    print(f"    Resp saved to {fname} ({len(resp_str)} chars)")
                    print(f"    Preview: {resp_str[:1000]}")
                else:
                    print(f"    Resp: {resp_str[:1000]}")
    
    browser.close()
