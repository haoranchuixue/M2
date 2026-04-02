"""Create SQL-type dataset via DataEase UI using Playwright."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

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
    print("Logged in")
    
    # Navigate to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_page.png')
    
    # Look for "DSP Report" group in left sidebar and click it
    dsp_group = page.query_selector('text="DSP Report"')
    if dsp_group:
        print("Found DSP Report group, clicking...")
        dsp_group.click()
        time.sleep(2)
    else:
        print("DSP Report group not found in sidebar")
        # List what's visible
        all_text = page.evaluate("() => document.body.innerText")
        print(f"Page text (first 2000):\n{all_text[:2000]}")
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_group.png')
    
    # Look for a "+" or "create" button to add a new dataset
    # In DataEase, there should be a button like "新建数据集" or a "+" icon
    create_btns = page.query_selector_all('[class*="create"], [class*="add"], [class*="new"]')
    print(f"\nFound {len(create_btns)} potential create buttons")
    for i, btn in enumerate(create_btns):
        text = btn.text_content() or ''
        cls = btn.get_attribute('class') or ''
        print(f"  [{i}] text='{text.strip()[:50]}', class='{cls[:80]}'")
    
    # Try to find "新建数据集" button or a context menu
    new_ds_btn = page.query_selector('text="新建数据集"')
    if not new_ds_btn:
        new_ds_btn = page.query_selector('text="添加数据集"')
    if not new_ds_btn:
        # Try right-clicking on the group for context menu
        if dsp_group:
            print("\nTrying right-click on DSP Report group...")
            dsp_group.click(button='right')
            time.sleep(2)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_context.png')
            
            menu_items = page.query_selector_all('.el-dropdown-menu__item, .ed-dropdown-menu__item, [class*="menu-item"]')
            print(f"Context menu items: {len(menu_items)}")
            for mi in menu_items:
                text = mi.text_content() or ''
                print(f"  - {text.strip()}")
    
    # Also try looking for "SQL数据集" or "SQL" option
    sql_opt = page.query_selector('text="SQL数据集"')
    if sql_opt:
        print("\nFound SQL dataset option!")
        sql_opt.click()
        time.sleep(2)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds_final.png')
    
    browser.close()
    print("\nDone!")
