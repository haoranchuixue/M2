"""Click the '...' more menu on DSP Report to see options."""
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
    
    # Hover over DSP Report
    node = page.locator('.custom-tree-node:has-text("DSP Report")').first
    node.hover()
    time.sleep(0.5)
    
    # Click the second hover-icon (the '...' dropdown menu)
    icon_more = node.locator('.icon-more').first
    dropdown_trigger = icon_more.locator('.ed-dropdown .ed-icon.hover-icon').first
    dropdown_trigger.click(force=True)
    time.sleep(1)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_more_menu.png')
    
    # Check for dropdown menu items
    menu_items = page.locator('.ed-dropdown-menu__item, [class*="dropdown-item"]')
    count = menu_items.count()
    print(f"Menu items: {count}")
    for i in range(count):
        item = menu_items.nth(i)
        txt = item.inner_text().strip()
        if txt:
            print(f"  Item {i}: '{txt}'")
    
    # Check all visible text elements
    visible_items = page.locator('[class*="dropdown"] >> visible=true')
    count2 = visible_items.count()
    print(f"\nVisible dropdown elements: {count2}")
    
    # Try broader selector
    poppers = page.locator('.ed-popper, .ed-dropdown-menu')
    count3 = poppers.count()
    print(f"\nPopper/dropdown menus: {count3}")
    for i in range(count3):
        pop = poppers.nth(i)
        if pop.is_visible():
            txt = pop.inner_text()[:200]
            print(f"  Visible popper: '{txt}'")
    
    browser.close()

print("Done.")
