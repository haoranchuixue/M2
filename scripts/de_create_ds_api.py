"""Create dataset via DataEase API."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time

base = 'http://47.236.78.123:8100'

def get_fresh_token():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f'{base}/', timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        inputs = page.query_selector_all('input')
        inputs[0].fill('admin')
        inputs[1].fill('DataEase@123456')
        page.query_selector('button').click()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=15000)
        token_raw = page.evaluate("() => localStorage.getItem('user.token')")
        token_obj = json.loads(token_raw)
        jwt = json.loads(token_obj['v'])
        browser.close()
        return jwt

token = get_fresh_token()
headers = {'x-de-token': token, 'Content-Type': 'application/json'}

def api(method, path, data=None):
    url = f'{base}/de2api{path}'
    if method == 'POST':
        r = requests.post(url, headers=headers, json=data or {}, timeout=30)
    else:
        r = requests.get(url, headers=headers, timeout=30)
    return r.json()

sr_ds_id = '1236022373120086016'

# Try to create a dataset group (folder)
print("=== Creating dataset group ===")
endpoints_to_try = [
    '/datasetTree/save',
    '/datasetTree/create',
    '/datasetGroup/save',
    '/dataset/save',
]

group_payloads = [
    {"name": "DSP Report", "nodeType": "folder", "pid": "0", "type": "group", "busiFlag": "dataset"},
    {"name": "DSP Report", "nodeType": "folder", "pid": "0", "leaf": False},
]

for ep in endpoints_to_try:
    for payload in group_payloads:
        result = api('POST', ep, payload)
        code = result.get('code')
        status = result.get('status')
        if status != 404 and code != None:
            msg = result.get('msg') or ''
            print(f"  {ep}: code={code}, msg={msg[:100]}")
            if code == 0:
                print(f"  SUCCESS! Data: {json.dumps(result.get('data'), ensure_ascii=False)[:500]}")
                break
    else:
        continue
    break

# Let's also try creating a SQL dataset directly
print("\n=== Trying SQL dataset creation ===")
sql = """SELECT 
    create_date as `date`,
    source,
    affiliate_id,
    SUM(request_count) as request,
    SUM(IFNULL(request_filter_count,0)+IFNULL(request_count,0)) as total_request,
    SUM(response_count) as response,
    SUM(win_count) as wins,
    SUM(imp_count) as impressions,
    SUM(clean_imp_count) as clean_impressions,
    SUM(cheat_imp_count) as cheat_impressions,
    SUM(exceed_imp_count) as exceed_impressions,
    SUM(click_count) as click,
    SUM(clean_click_count) as clean_clicks
FROM dsp_report
WHERE create_date >= '2026-03-29'
GROUP BY create_date, source, affiliate_id"""

sql_payloads = [
    {
        "name": "DSP Report Data",
        "nodeType": "dataset",
        "pid": "0",
        "type": "sql",
        "datasourceId": sr_ds_id,
        "info": json.dumps({"sql": sql}),
        "busiFlag": "dataset"
    },
    {
        "name": "DSP Report Data", 
        "type": "sql",
        "datasourceId": sr_ds_id,
        "sql": sql,
        "pid": "0",
    },
]

for ep in endpoints_to_try:
    for payload in sql_payloads:
        result = api('POST', ep, payload)
        code = result.get('code')
        status = result.get('status')
        if status != 404 and code != None:
            msg = result.get('msg') or ''
            print(f"  {ep}: code={code}, msg={msg[:100]}")
            if code == 0:
                print(f"  SUCCESS! Data: {json.dumps(result.get('data'), ensure_ascii=False)[:500]}")
                break
    else:
        continue
    break
