"""
Fix 'Unknown thread id' error by:
1. Testing if the chart data API still errors
2. Attempting datasource connection test to force pool refresh
3. Retrying chart data
"""
import sys, json, copy
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
PANEL_ID = '1236081407923720192'


def get_fresh_token():
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
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt


token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

# Step 1: Get dashboard and chart view
print('=== Step 1: Fetch dashboard ===')
r = requests.post(
    f'{base}/de2api/dataVisualization/findById',
    headers=headers,
    json={'id': PANEL_ID, 'busiFlag': 'dataV', 'resourceTable': 'snapshot'},
    timeout=30,
)
dv = r.json().get('data') or {}
cvi = dv.get('canvasViewInfo') or {}
chart_id = None
chart_view = None
for vid, view in cvi.items():
    if view.get('type') == 'table-normal':
        chart_id = vid
        chart_view = view
        break

if not chart_view:
    print('ERROR: No table chart found')
    sys.exit(1)

print(f'Chart id: {chart_id}, dataset: {chart_view.get("tableId")}')

# Step 2: Try getData to confirm the error
print('\n=== Step 2: Test getData (first attempt) ===')
r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=120)
resp2 = r2.json()
print(f'Code: {resp2.get("code")}, Msg: {str(resp2.get("msg",""))[:200]}')

if resp2.get('code') == 0:
    rows = resp2.get('data', {}).get('tableRow', [])
    print(f'OK! {len(rows)} rows returned. Error has self-healed.')
    sys.exit(0)

# Step 3: List datasources and try to validate/test the StarRocks connection
print('\n=== Step 3: Try datasource validation to refresh pool ===')
r3 = requests.post(f'{base}/de2api/datasource/list', headers=headers, json={}, timeout=30)
print(f'Datasource list: {r3.status_code}')
ds_list = r3.json().get('data') or []
if not isinstance(ds_list, list):
    ds_list = [ds_list] if ds_list else []

sr_ds = None
for ds in ds_list:
    name = ds.get('name', '')
    ds_type = ds.get('type', '')
    print(f'  {name} (type={ds_type}, id={ds.get("id")})')
    if 'starrocks' in ds_type.lower() or 'starrocks' in name.lower() or 'mysql' in ds_type.lower():
        sr_ds = ds

if sr_ds:
    print(f'\nValidating datasource: {sr_ds.get("name")} (id={sr_ds.get("id")})')
    r4 = requests.post(
        f'{base}/de2api/datasource/validate/{sr_ds["id"]}',
        headers=headers, json={}, timeout=30,
    )
    print(f'Validate: {r4.status_code} {r4.text[:300]}')

    r4b = requests.post(
        f'{base}/de2api/datasource/checkStatus/{sr_ds["id"]}',
        headers=headers, json={}, timeout=30,
    )
    print(f'checkStatus: {r4b.status_code} {r4b.text[:300]}')

# Step 4: Wait a moment and retry getData
print('\n=== Step 4: Retry getData after pool refresh ===')
time.sleep(3)
token2 = get_fresh_token()
headers2 = {'x-de-token': token2, 'Content-Type': 'application/json'}
r5 = requests.post(f'{base}/de2api/chartData/getData', headers=headers2, json=chart_view, timeout=120)
resp5 = r5.json()
print(f'Code: {resp5.get("code")}, Msg: {str(resp5.get("msg",""))[:200]}')
if resp5.get('code') == 0:
    rows = resp5.get('data', {}).get('tableRow', [])
    print(f'OK! {len(rows)} rows. Connection recovered after refresh.')
else:
    print('Still failing. Need to restart DataEase service on the server.')
    print('If you have SSH access to 47.236.78.123, run:')
    print('  docker restart dataease')
