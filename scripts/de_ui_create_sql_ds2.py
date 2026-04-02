"""Create SQL-type dataset via DataEase UI - find the create button on dataset page."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
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
    print("Logged in")
    
    # Navigate to dataset page via the left nav
    ds_nav = page.query_selector('text="数据集"')
    if ds_nav:
        ds_nav.click()
        time.sleep(3)
    else:
        page.goto(f'{base}/#/data/dataset', timeout=30000)
        time.sleep(3)
    
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"URL: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds2_page.png')
    
    # Find "DSP Report" group and expand it
    dsp_el = page.query_selector('span:has-text("DSP Report")')
    if dsp_el:
        print("Found DSP Report group")
        dsp_el.click()
        time.sleep(2)
    
    # Look for any icon or button that could create a new dataset
    # Check for a "..." or "more" icon near the group, or a "+" icon
    # Take a screenshot of the full page HTML structure to understand layout
    html_snippet = page.evaluate("""() => {
        const sidebar = document.querySelector('.dataset-tree, .tree-container, [class*="tree"], [class*="sidebar"]');
        return sidebar ? sidebar.outerHTML.substring(0, 3000) : 'No sidebar found';
    }""")
    print(f"\nSidebar HTML:\n{html_snippet[:2000]}")
    
    # Try to find create button - might be an icon at the top of the tree
    icons = page.query_selector_all('[class*="icon-add"], [class*="icon-plus"], [class*="icon-create"], .ed-icon-plus, .el-icon-plus')
    print(f"\nAdd icons found: {len(icons)}")
    
    # Also check for buttons
    buttons = page.query_selector_all('button')
    print(f"Buttons found: {len(buttons)}")
    for i, btn in enumerate(buttons):
        text = btn.text_content() or ''
        cls = btn.get_attribute('class') or ''
        vis = btn.is_visible()
        if vis:
            print(f"  [{i}] visible, text='{text.strip()[:50]}', class='{cls[:80]}'")
    
    # Check for any element with "新建" in text
    new_els = page.query_selector_all('*:has-text("新建")')
    print(f"\nElements with '新建': {len(new_els)}")
    for i, el in enumerate(new_els[:10]):
        tag = el.evaluate("el => el.tagName")
        text = el.text_content() or ''
        vis = el.is_visible()
        if vis and len(text.strip()) < 50:
            print(f"  [{i}] <{tag}> visible: '{text.strip()}'")
    
    # Look for hover-triggered create icons on the DSP Report group
    if dsp_el:
        dsp_el.hover()
        time.sleep(1)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds2_hover.png')
        
        # Check for icons that appear on hover
        parent = dsp_el.evaluate("el => el.closest('.tree-node, [class*=\"tree-node\"]')?.outerHTML?.substring(0, 500) || 'no parent'")
        print(f"\nDSP Report parent HTML:\n{parent}")
    
    browser.close()
    print("\nDone!")
