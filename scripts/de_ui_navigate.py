"""Navigate to dashboard list, find DSP Report, open in edit mode."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = 1236050016221663232

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
    
    # Click on "仪表板" tab in top nav
    print("Clicking 仪表板 tab...")
    dashboard_tab = page.locator('text="仪表板"').first
    dashboard_tab.click()
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_list_01.png')
    print("Screenshot: dash_list_01.png")
    
    # Current URL
    print(f"Current URL: {page.url}")
    
    # Look for DSP Report in the page
    all_text = page.inner_text('body')
    if 'DSP Report' in all_text:
        print("Found 'DSP Report' on page!")
        dsp_el = page.locator('text="DSP Report"').first
        print(f"  DSP Report visible: {dsp_el.is_visible()}")
    else:
        print("'DSP Report' not found on page")
        # Print visible items
        print(f"Page text (first 500): {all_text[:500]}")
    
    # Look for tree items or list items  
    tree_nodes = page.query_selector_all('[class*="tree-node"], [class*="list-item"], [class*="folder"]')
    print(f"\nTree/list elements: {len(tree_nodes)}")
    for node in tree_nodes[:20]:
        txt = node.inner_text()[:60].strip()
        if txt:
            print(f"  '{txt}'")
    
    # Try clicking on DSP Report
    try:
        dsp = page.locator('text="DSP Report"').first
        if dsp.is_visible():
            print("\nClicking on DSP Report...")
            dsp.click()
            time.sleep(2)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_list_02.png')
            print("Screenshot after click: dash_list_02.png")
            print(f"URL after click: {page.url}")
            
            # Look for edit button or right-click context menu
            dsp.click(button='right')
            time.sleep(1)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_list_03.png')
            print("Screenshot after right-click: dash_list_03.png")
            
            # Check context menu
            menus = page.query_selector_all('[class*="dropdown"], [class*="menu-item"], [class*="context"]')
            print(f"\nMenu elements: {len(menus)}")
            for m in menus[:10]:
                cls = m.get_attribute('class') or ''
                txt = m.inner_text()[:60].strip()
                print(f"  class='{cls[:50]}', text='{txt}'")
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(2)
    browser.close()

print("Done.")
