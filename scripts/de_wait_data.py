"""Navigate to m2dashboard and wait for data to load."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 900})

    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    print('Logged in')

    # Navigate to 仪表板 - use URL
    page.goto(f'{base}/#/panel/index', timeout=60000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_step1.png')
    print('At panel list')

    # Expand ReportCenter DSP Report folder
    all_text = page.inner_text('body')
    print(f'Body contains "ReportCenter DSP Report": {"ReportCenter DSP Report" in all_text}')
    print(f'Body contains "m2dashboard": {"m2dashboard" in all_text}')

    # Try to expand the folder by clicking the arrow
    tree_items = page.query_selector_all('[class*="tree"] [class*="node"], [class*="el-tree-node"]')
    print(f'Tree nodes: {len(tree_items)}')
    for item in tree_items:
        txt = item.text_content() or ''
        if 'ReportCenter DSP' in txt and 'm2dashboard' not in txt:
            # Click the expand arrow
            arrow = item.query_selector('[class*="expand"], [class*="arrow"], svg, i')
            if arrow:
                arrow.click()
                time.sleep(2)
                print(f'Expanded folder: {txt[:40]}')
            else:
                item.click()
                time.sleep(2)
                print(f'Clicked folder: {txt[:40]}')

    page.screenshot(path=r'd:\Projects\m2\scripts\ss_step2.png')

    # Now find m2dashboard
    m2 = page.query_selector('text=m2dashboard')
    if not m2:
        # Maybe it's nested - try double clicking the folder
        tree_items2 = page.query_selector_all('[class*="tree"] [class*="node"], [class*="el-tree-node"]')
        for item in tree_items2:
            txt = item.text_content() or ''
            if 'm2dashboard' in txt:
                # Find the actual clickable part
                content = item.query_selector('[class*="content"], [class*="label"], span')
                if content and 'm2dashboard' in (content.text_content() or ''):
                    m2 = content
                    break
                m2 = item
                break

    if m2:
        m2.click()
        print('Clicked m2dashboard')
        time.sleep(3)
        page.screenshot(path=r'd:\Projects\m2\scripts\ss_step3.png')

        # Wait for data to load
        for secs in [10, 30, 60, 90]:
            time.sleep(max(secs - 10, 5))
            page.screenshot(path=rf'd:\Projects\m2\scripts\ss_m2_{secs}s.png')
            body = page.inner_text('body')

            if 'SQL ERROR' in body:
                idx = body.index('SQL ERROR')
                print(f'[{secs}s] SQL ERROR: {body[idx:idx+200]}')
                break
            elif 'DEException' in body:
                idx = body.index('DEException')
                print(f'[{secs}s] Error: {body[idx:idx+200]}')
                break

            tds = page.query_selector_all('td, [class*="cell"]')
            nums = [td for td in tds if (td.text_content() or '').strip()]
            if len(nums) > 5:
                print(f'[{secs}s] Data loaded! {len(nums)} cells')
                for n in nums[:10]:
                    print(f'  {n.text_content()[:50]}')
                break
            print(f'[{secs}s] Still loading... ({len(nums)} cells)')

        page.screenshot(path=r'd:\Projects\m2\scripts\ss_m2_final.png')
    else:
        print('Could not find m2dashboard')
        page.screenshot(path=r'd:\Projects\m2\scripts\ss_m2_notfound.png')

    browser.close()
    print('Done')
