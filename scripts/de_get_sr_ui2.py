"""Use Playwright to get StarRocks connection details from DataEase UI edit form."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    token_raw = page.evaluate("() => localStorage.getItem('user.token')")
    token_obj = json.loads(token_raw)
    jwt = json.loads(token_obj['v'])
    
    # Try hidePw endpoint to get host/port/database
    headers = {'x-de-token': jwt, 'Content-Type': 'application/json'}
    r = requests.get(f'{base}/de2api/datasource/hidePw/1236022373120086016', headers=headers, timeout=30)
    print(f"hidePw status: {r.status_code}")
    data = r.json().get('data', {})
    config_str = data.get('configuration', '')
    print(f"Config str preview: {str(config_str)[:500]}")
    if config_str and isinstance(config_str, str):
        try:
            config = json.loads(config_str)
            print(f"Host: {config.get('host')}")
            print(f"Port: {config.get('port')}")
            print(f"Database: {config.get('dataBase')}")
            print(f"Username: {config.get('username')}")
            print(f"Password: {config.get('password')}")
            print(f"Extra params: {config.get('extraParams', '')}")
        except:
            print("Config is not JSON")
    
    # Navigate to datasource page and try to find edit button
    page.goto(f'{base}/#/data/datasource', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    
    # Click on starrocks
    sr_el = page.query_selector('text="starrocks"')
    if sr_el:
        sr_el.click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        
        # Look for edit button
        edit_btn = page.query_selector('[class*="edit"]') or page.query_selector('text="编辑"')
        if edit_btn:
            print("\nFound edit button, clicking...")
            edit_btn.click()
            time.sleep(3)
            page.wait_for_load_state('networkidle', timeout=15000)
        
        # Take screenshot
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ds_sr_edit.png')
        
        # Check all visible input fields
        all_inputs = page.query_selector_all('input:visible')
        print(f"\nVisible input fields: {len(all_inputs)}")
        for i, inp in enumerate(all_inputs):
            val = inp.input_value()
            placeholder = inp.get_attribute('placeholder') or ''
            inp_type = inp.get_attribute('type') or ''
            parent = inp.evaluate("el => el.closest('.el-form-item, .ed-form-item')?.querySelector('label')?.textContent || ''")
            print(f"  [{i}] type={inp_type}, label='{parent}', placeholder='{placeholder}', value='{val}'")
    
    browser.close()
