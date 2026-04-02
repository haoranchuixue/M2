"""Test chart data query with the filtered dataset."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
M2_ID = '1236684857652940800'

def tok():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(base + '/', timeout=60000, wait_until='domcontentloaded')
        pg.wait_for_load_state('networkidle', timeout=30000)
        pg.wait_for_selector('input', timeout=10000)
        ins = pg.query_selector_all('input')
        ins[0].fill('admin')
        ins[1].fill('DataEase@123456')
        pg.query_selector('button').click()
        time.sleep(5)
        pg.wait_for_load_state('networkidle', timeout=30000)
        tr = pg.evaluate('() => localStorage.getItem("user.token")')
        jwt = json.loads(json.loads(tr)['v'])
        b.close()
        return jwt

h = {'x-de-token': tok(), 'Content-Type': 'application/json'}

# Get dashboard
r = requests.post(base + '/de2api/dataVisualization/findById', headers=h,
                  json={'id': M2_ID, 'busiFlag': 'dashboard', 'resourceTable': 'snapshot'}, timeout=30)
dv = r.json()['data']
cvi = dv.get('canvasViewInfo') or {}

for vid, view in cvi.items():
    print(f'Chart: {vid} type={view.get("type")} tableId={view.get("tableId")}')
    print(f'  xAxis: {len(view.get("xAxis",[]))} yAxis: {len(view.get("yAxis",[]))}')
    print(f'  resultCount: {view.get("resultCount")} resultMode: {view.get("resultMode")}')
    print(f'  customFilter: {view.get("customFilter")}')

    # Test getData
    print(f'\nTesting getData (timeout=300s)...')
    t0 = time.time()
    r2 = requests.post(base + '/de2api/chartData/getData', headers=h, json=view, timeout=300)
    t1 = time.time()
    resp = r2.json()
    print(f'  Time: {t1-t0:.1f}s')
    print(f'  Code: {resp.get("code")}')
    if resp.get('code') == 0:
        rows = resp.get('data', {}).get('tableRow', [])
        print(f'  Rows: {len(rows)}')
        if rows:
            print(f'  Sample: {json.dumps(rows[0], ensure_ascii=False)[:400]}')
    else:
        print(f'  Error: {str(resp.get("msg",""))[:300]}')
