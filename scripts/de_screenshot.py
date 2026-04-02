"""Take a screenshot of the dashboard."""
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
    
    # Navigate to preview
    page.goto(f'{base}/#/preview/{panel_id}', timeout=60000, wait_until='domcontentloaded')
    print("Navigating to preview...")
    time.sleep(10)
    page.wait_for_load_state('networkidle', timeout=60000)
    
    # Wait for chart data to load
    print("Waiting for data to load...")
    time.sleep(20)
    
    # Take screenshot
    page.screenshot(path='d:/Projects/m2/scripts/dashboard_preview.png', full_page=True)
    print("Screenshot saved to dashboard_preview.png")
    
    # Also try edit mode
    page.goto(f'{base}/#/dvCanvas?dvId={panel_id}&opt=edit', timeout=60000, wait_until='domcontentloaded')
    time.sleep(10)
    page.wait_for_load_state('networkidle', timeout=60000)
    time.sleep(15)
    page.screenshot(path='d:/Projects/m2/scripts/dashboard_edit.png', full_page=True)
    print("Edit screenshot saved to dashboard_edit.png")
    
    browser.close()
