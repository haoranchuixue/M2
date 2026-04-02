"""Click the 查询 button on m2dashboard and check for data."""
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

    rc = page.query_selector('text="ReportCenter DSP Report"')
    if rc:
        rc.click()
        time.sleep(2)
    m2 = page.query_selector('text=m2dashboard')
    if m2:
        m2.dblclick()
        print('Opened m2dashboard')
    time.sleep(10)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_before_query.png', full_page=True)

    query_btn = page.query_selector('button:has-text("查询"), span:has-text("查询")')
    if query_btn:
        print('Found 查询 button, clicking...')
        query_btn.click()
        time.sleep(3)

    print('Waiting 60s for data...')
    time.sleep(60)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_after_query.png', full_page=True)

    body = page.inner_text('body')
    for kw in ['SQL ERROR', 'Error', 'error', '暂无数据', 'Date', 'Request',
               'cpu limit', 'Unknown thread', 'Memory', '获取数据异常', '查看异常原因',
               '2026-03']:
        if kw in body:
            idx = body.index(kw)
            snippet = body[max(0, idx - 40):idx + 120].replace('\n', ' ')
            print(f'  Found "{kw}": ...{snippet}...')

    browser.close()
    print('Done')
