"""Hover DSP Report tree node and click edit to enter editor."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
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
    
    # Navigate to dashboard page
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Hover over the custom-tree-node containing DSP Report
    node = page.locator('.custom-tree-node:has-text("DSP Report")').first
    node.hover()
    time.sleep(1)
    
    # Now check what's visible
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_hover_edit.png')
    
    # Get HTML of the hovered node to find edit icon
    html = node.evaluate("e => e.outerHTML")
    print(f"Node HTML:\n{html[:2000]}")
    
    # Look for the icons that appeared on hover
    icons = node.locator('svg, i.ed-icon, [class*="icon"]')
    count = icons.count()
    print(f"\nIcons in node: {count}")
    for i in range(count):
        icon = icons.nth(i)
        try:
            cls = icon.get_attribute('class') or ''
            tag = icon.evaluate("e => e.tagName")
            visible = icon.is_visible()
            bbox = icon.bounding_box()
            print(f"  Icon {i}: tag={tag}, class='{cls[:50]}', visible={visible}, bbox={bbox}")
        except:
            pass
    
    # Look for the edit icon using common patterns
    edit_btns = node.locator('[class*="edit"], [class*="rename"]')
    count2 = edit_btns.count()
    print(f"\nEdit buttons: {count2}")
    
    # Also check for ed-dropdown and el-dropdown menus
    dropdowns = node.locator('.ed-dropdown')
    count3 = dropdowns.count()
    print(f"Dropdowns: {count3}")
    
    browser.close()

print("Done.")
