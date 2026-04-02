"""Open the dashboard in browser, take screenshot to verify state."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

base = 'http://47.236.78.123:8100'
PANEL_ID = '1236684857652940800'

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

    page.goto(f'{base}/#/panel/index', timeout=60000, wait_until='domcontentloaded')
    time.sleep(5)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_panel_index.png', full_page=True)
    print('At panel index')

    body = page.inner_text('body')
    if 'm2dashboard' in body:
        print('m2dashboard visible in tree')
        m2 = page.query_selector('text=m2dashboard')
        if m2:
            m2.dblclick()
            print('Double-clicked m2dashboard')
    elif 'ReportCenter' in body:
        print('Found ReportCenter, expanding...')
        rc = page.query_selector('text="ReportCenter DSP Report"')
        if rc:
            rc.click()
            time.sleep(3)
        m2 = page.query_selector('text=m2dashboard')
        if m2:
            m2.dblclick()
            print('Double-clicked m2dashboard')

    print('Waiting 30s for dashboard to load...')
    time.sleep(30)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_m2dashboard_30s.png', full_page=True)
    print('Screenshot at 30s')

    body2 = page.inner_text('body')
    for kw in ['Time Range', 'Source', 'DSP Report', 'SQL ERROR', 'Error', 'error',
               'Date', 'Request', '暂无数据', '加载中']:
        if kw in body2:
            idx = body2.index(kw)
            snippet = body2[max(0, idx - 50):idx + 120].replace('\n', ' ')
            print(f'  Found "{kw}": ...{snippet}...')

    print('Waiting 30s more...')
    time.sleep(30)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_m2dashboard_60s.png', full_page=True)
    print('Screenshot at 60s')

    body3 = page.inner_text('body')
    for kw in ['SQL ERROR', 'Error', 'error', '暂无数据', 'Date', 'Request', 'cpu limit',
               'Unknown thread', 'Memory']:
        if kw in body3:
            idx = body3.index(kw)
            snippet = body3[max(0, idx - 50):idx + 150].replace('\n', ' ')
            print(f'  Found "{kw}": ...{snippet}...')

    has_error = any(k in body3 for k in ['SQL ERROR', 'cpu limit', 'Unknown thread', 'Memory'])
    has_data = 'Request' in body3 and 'Date' in body3
    if has_error:
        print('\n*** ERRORS DETECTED ***')
    elif has_data:
        print('\n*** DATA APPEARS LOADED ***')
    else:
        print('\n*** UNKNOWN STATE - check screenshots ***')

    browser.close()
    print('Done')
