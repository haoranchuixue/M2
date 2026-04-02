"""Take a screenshot after waiting longer for data to load."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

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
    
    # Go to dashboards
    page.goto(f'{base}/#/panel/index', timeout=60000)
    time.sleep(5)
    
    # Click DSP Report
    elements = page.query_selector_all('span')
    for el in elements:
        text = el.text_content()
        if text and text.strip() == 'DSP Report':
            print(f"Clicking: {text}")
            el.click()
            break
    
    # Wait much longer for data
    print("Waiting 60s for full load...")
    time.sleep(60)
    
    page.screenshot(path='d:/Projects/m2/scripts/ss_60s.png')
    print("60s screenshot saved")
    
    # Check if there are any error messages visible
    error_els = page.query_selector_all('.el-message--error, .error-message, [class*="error"]')
    for el in error_els:
        text = el.text_content()
        if text:
            print(f"Error element: {text[:200]}")
    
    # Check for table elements
    table_els = page.query_selector_all('table, .ant-table, .s2-table, [class*="table"]')
    print(f"Table elements found: {len(table_els)}")
    
    # Check the page content
    body_text = page.evaluate("document.body.innerText")
    if body_text:
        lines = [l.strip() for l in body_text.split('\n') if l.strip()]
        print(f"Page text ({len(lines)} lines):")
        for line in lines[:30]:
            print(f"  {line[:100]}")
    
    browser.close()
