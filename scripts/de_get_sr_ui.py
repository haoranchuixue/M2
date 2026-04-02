"""Use Playwright to get StarRocks connection details from DataEase UI."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
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
    
    # Capture API responses
    responses = {}
    def handle_response(response):
        url = response.url
        if 'datasource' in url and response.status == 200:
            try:
                body = response.json()
                responses[url] = body
            except:
                pass
    page.on('response', handle_response)
    
    # Navigate to data source page
    page.goto(f'{base}/#/data/datasource', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ds_page.png')
    
    # Look for starrocks data source in the sidebar
    sr_el = page.query_selector('text="starrocks"')
    if not sr_el:
        sr_el = page.query_selector('text="StarRocks"')
    if not sr_el:
        # Try to find any text containing starrocks
        all_text = page.evaluate("() => document.body.innerText")
        print(f"Page text (first 2000 chars):\n{all_text[:2000]}")
    
    if sr_el:
        print("Found starrocks element, clicking...")
        sr_el.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ds_sr_detail.png')
        
        # Try to find input fields with connection details
        all_inputs = page.query_selector_all('input')
        print(f"\nFound {len(all_inputs)} input fields:")
        for i, inp in enumerate(all_inputs):
            val = inp.get_attribute('value') or inp.input_value()
            placeholder = inp.get_attribute('placeholder') or ''
            inp_type = inp.get_attribute('type') or ''
            label = inp.get_attribute('aria-label') or ''
            print(f"  [{i}] type={inp_type}, label={label}, placeholder={placeholder}, value={val}")
    
    # Also check captured API responses
    print(f"\nCaptured {len(responses)} datasource API responses:")
    for url, body in responses.items():
        print(f"  URL: {url}")
        data = body.get('data', body)
        if isinstance(data, dict):
            config_str = data.get('configuration', '')
            if config_str and isinstance(config_str, str) and config_str.startswith('{'):
                config = json.loads(config_str)
                print(f"  Host: {config.get('host')}")
                print(f"  Port: {config.get('port')}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = item.get('name', '')
                    if 'star' in name.lower():
                        print(f"  Found: {name}, id={item.get('id')}")
                        config_str = item.get('configuration', '')
                        if config_str:
                            print(f"  Config type: {type(config_str).__name__}")
                            print(f"  Config preview: {str(config_str)[:200]}")
    
    browser.close()
