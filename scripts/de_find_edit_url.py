"""Find the edit URL for an existing dashboard by examining navigation."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

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
    
    # Go to dashboard section
    sidebar_items = page.query_selector_all('[class*=menu-item]')
    for item in sidebar_items:
        if '仪表板' in item.inner_text():
            item.click()
            time.sleep(3)
            break
    
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Navigate into an existing dashboard - mchat1
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and 'mchat1' in content.inner_text():
            print("Found mchat1, checking if it's a folder or dashboard...")
            
            # Click to expand or navigate
            content.click()
            time.sleep(2)
            print(f"URL after click: {page.url}")
            
            # Check if it expanded to show children
            children = node.query_selector_all('.ed-tree-node')
            print(f"Children: {len(children)}")
            for child in children[:5]:
                cc = child.query_selector('.ed-tree-node__content')
                if cc:
                    print(f"  Child: '{cc.inner_text().strip()}'")
                    # Try double-clicking a child (actual dashboard)
                    cc.dblclick()
                    time.sleep(5)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    print(f"URL after dblclick: {page.url}")
                    page.screenshot(path='d:/Projects/m2/scripts/de_actual_dashboard.png')
                    break
            break
    
    # Also check the 【官方示例】 folder
    print("\nChecking 【官方示例】...")
    page.goto(f'{base}/#/panel/index', timeout=30000, wait_until='domcontentloaded')
    time.sleep(3)
    
    tree_nodes = page.query_selector_all('.ed-tree-node')
    for node in tree_nodes:
        content = node.query_selector('.ed-tree-node__content')
        if content and '官方' in content.inner_text():
            content.click()
            time.sleep(2)
            # Get children
            child_nodes = node.query_selector_all('.ed-tree-node')
            for child in child_nodes[:5]:
                cc = child.query_selector('.ed-tree-node__content')
                if cc:
                    text = cc.inner_text().strip()
                    print(f"  Child: '{text}'")
            
            # Try navigating to a child
            if child_nodes:
                first_child = child_nodes[0].query_selector('.ed-tree-node__content')
                if first_child:
                    # Single click
                    first_child.click()
                    time.sleep(3)
                    print(f"After single click: {page.url}")
                    
                    # Check for edit/preview buttons
                    btns = page.query_selector_all('button:visible')
                    for b in btns:
                        t = b.inner_text().strip()
                        if t and len(t) < 20:
                            print(f"  Button: '{t}'")
                    
                    # Check for icon links
                    icons = page.query_selector_all('[class*=preview]:visible, [class*=edit]:visible')
                    for ico in icons[:5]:
                        cls = ico.get_attribute('class') or ''
                        print(f"  Icon: class={cls[:80]}")
            break
    
    # Try the DSP Report with different approaches
    print("\n\n=== Trying to open DSP Report ===")
    # In DataEase v2, dashboard editing uses the route: #/dvCanvas/preview/panel/{id}
    # or #/de-link/{id}/dashboard
    routes_to_try = [
        f'#/dvCanvas/preview/panel/{1236050016221663232}',
        f'#/de-link/{1236050016221663232}/dashboard',
        f'#/preview/{1236050016221663232}',
        f'#/dvCanvas/edit/dashboard/{1236050016221663232}',
        f'#/panel/edit/{1236050016221663232}',
    ]
    
    for route in routes_to_try:
        page.goto(f'{base}/{route}', timeout=15000, wait_until='domcontentloaded')
        time.sleep(3)
        final_url = page.url
        print(f"  {route} -> {final_url}")
        if final_url != f'{base}/#/workbranch/index' and 'login' not in final_url:
            page.screenshot(path='d:/Projects/m2/scripts/de_found_route.png')
            break
    
    browser.close()
