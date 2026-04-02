"""Intercept network requests to see what getData payload the dashboard sends."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import time

base = 'http://47.236.78.123:8100'

captured = []

def handle_request(request):
    url = request.url
    if 'getData' in url or 'chartData' in url:
        body = request.post_data
        captured.append({'url': url, 'method': request.method, 'body': body})
        if body:
            try:
                j = json.loads(body)
                print(f'\n=== REQUEST to {url} ===')
                print(f'  type: {j.get("type")}')
                print(f'  tableId: {j.get("tableId")}')
                print(f'  resultCount: {j.get("resultCount")}')
                print(f'  xAxis count: {len(j.get("xAxis", []))}')
                print(f'  yAxis count: {len(j.get("yAxis", []))}')
                cf = j.get('customFilter', {})
                print(f'  customFilter: {json.dumps(cf, ensure_ascii=False)[:500]}')
                print(f'  drill: {j.get("drill")}')
                for f in j.get('xAxis', [])[:3]:
                    print(f'  xAxis field: {f.get("originName")} filter={f.get("filter")}')
            except:
                print(f'  [non-json body: {body[:200]}]')

def handle_response(response):
    url = response.url
    if 'getData' in url or 'chartData' in url:
        try:
            body = response.json()
            print(f'\n=== RESPONSE from {url} ===')
            print(f'  code: {body.get("code")}')
            if body.get('code') == 0:
                data = body.get('data') or {}
                rows = data.get('tableRow', [])
                flds = data.get('fields', [])
                print(f'  rows: {len(rows)}, fields: {len(flds)}')
                if rows:
                    print(f'  sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
            else:
                print(f'  msg: {str(body.get("msg",""))[:300]}')
        except:
            print(f'  [non-json response status={response.status}]')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 900})
    page.on('request', handle_request)
    page.on('response', handle_response)

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
    
    print('Waiting 20s for initial load...')
    time.sleep(20)
    
    print(f'\nTotal captured requests so far: {len(captured)}')

    query_btn = page.query_selector('button:has-text("查询")')
    if query_btn:
        print('\nClicking 查询...')
        query_btn.click()
    
    print('Waiting 30s after clicking 查询...')
    time.sleep(30)

    print(f'\nTotal captured requests: {len(captured)}')
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_intercept.png', full_page=True)
    
    browser.close()
    print('Done')
