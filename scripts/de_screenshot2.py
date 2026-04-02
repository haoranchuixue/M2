"""Navigate through DataEase menus to find and screenshot the dashboard."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
panel_id = '1236081407923720192'

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
    
    # Try navigating to dashboard list
    page.goto(f'{base}/#/panel/index', timeout=60000, wait_until='domcontentloaded')
    time.sleep(5)
    page.screenshot(path='d:/Projects/m2/scripts/ss_panel_list.png')
    print("Panel list screenshot saved")
    
    # Click on the dashboard in the list
    # Try to find our dashboard by name
    time.sleep(3)
    page.screenshot(path='d:/Projects/m2/scripts/ss_panel_list2.png')
    
    # Try direct URL to the edit page with different patterns
    urls = [
        f'{base}/#/dvCanvas?dvId={panel_id}',
        f'{base}/#/dvCanvas?dvId={panel_id}&opt=edit',
        f'{base}/#/panel/index?dvId={panel_id}',
        f'{base}/#/de-link/{panel_id}',
    ]
    
    for i, url in enumerate(urls):
        print(f"Trying URL {i}: {url}")
        page.goto(url, timeout=60000, wait_until='domcontentloaded')
        time.sleep(8)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(5)
        page.screenshot(path=f'd:/Projects/m2/scripts/ss_url_{i}.png')
        print(f"  Screenshot saved: ss_url_{i}.png")
        # Get page title/URL
        print(f"  Current URL: {page.url}")
    
    browser.close()
