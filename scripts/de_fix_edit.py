"""Fix: Check what's on the DSP Report page and find edit functionality."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
dashboard_id = '1236050016221663232'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1920, 'height': 1080})
    page = context.new_page()
    
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
    
    # Go to dashboard section first
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        if '仪表板' in item.inner_text():
            item.click()
            time.sleep(3)
            break
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Click DSP Report in the tree
    page.wait_for_selector('.ed-tree-node', timeout=10000)
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and 'DSP Report' in content.inner_text():
            content.click()
            time.sleep(3)
            break
    
    page.wait_for_load_state('networkidle', timeout=15000)
    print(f"URL: {page.url}")
    page.screenshot(path='d:/Projects/m2/scripts/de_dsp_selected.png')
    
    # List ALL buttons
    buttons = page.query_selector_all('button')
    for b in buttons:
        vis = b.is_visible()
        text = b.inner_text().strip()
        if text:
            print(f"  Button (visible={vis}): '{text}'")
    
    # Check for edit icon in header
    header_els = page.query_selector_all('[class*=head]:visible, [class*=header]:visible')
    for h in header_els[:5]:
        text = h.inner_text()[:100]
        if text.strip():
            print(f"  Header: '{text}'")
    
    # Try to directly navigate to editor URL
    print("\n=== Trying direct editor URLs ===")
    for route in [
        f'#/dvCanvas/edit/dashboard/{dashboard_id}',
        f'#/panel/edit/{dashboard_id}',
        f'#/dashboard-edit/{dashboard_id}',
        f'#/dvCanvas/preview/panel/{dashboard_id}',
    ]:
        page.goto(f'{base}/{route}', timeout=15000, wait_until='domcontentloaded')
        time.sleep(3)
        final_url = page.url
        page_text = page.inner_text('body')[:200]
        is_edit = '保存' in page_text or '图表' in page_text or '编辑' in page_text
        print(f"  {route}")
        print(f"    -> {final_url}")
        print(f"    Text: {page_text[:100]}")
        if is_edit or ('workbranch' not in final_url and 'login' not in final_url):
            page.screenshot(path='d:/Projects/m2/scripts/de_edit_found.png')
    
    browser.close()
