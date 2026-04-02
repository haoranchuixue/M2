"""Verify the dashboard works - test data query and check rendering."""
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

panel_id = "1236081407923720192"

# Get dashboard data including chart view info
print("=== Getting dashboard with chart views ===")
r = requests.post(f'{base}/de2api/dataVisualization/findById',
                   headers=headers,
                   json={"id": panel_id, "busiFlag": "dataV", "resourceTable": "core"},
                   timeout=30)
resp = r.json()
if resp.get('code') != 0:
    r = requests.post(f'{base}/de2api/dataVisualization/findById/{panel_id}', headers=headers, json={}, timeout=30)
    resp = r.json()

dv = resp.get('data', {})
print(f"Name: {dv.get('name')}")

cvi = dv.get('canvasViewInfo', {}) or {}
print(f"Chart views: {len(cvi)}")

for chart_id, view in cvi.items():
    print(f"\n=== Chart: {chart_id} ===")
    print(f"Type: {view.get('type')}")
    print(f"Table (dataset): {view.get('tableId')}")
    
    x_axis = view.get('xAxis', [])
    y_axis = view.get('yAxis', [])
    print(f"Dimensions (xAxis): {len(x_axis)}")
    for f in x_axis:
        print(f"  {f.get('name', f.get('originName', '?'))}")
    print(f"Metrics (yAxis): {len(y_axis)}")
    for f in y_axis:
        print(f"  {f.get('name', f.get('originName', '?'))} [{f.get('summary', 'N/A')}]")
    
    cf = view.get('customFilter', {})
    print(f"Custom filter: {json.dumps(cf, ensure_ascii=False)[:200] if cf else 'None'}")
    
    # Test query
    print(f"\n--- Testing chart data query ---")
    query = {
        "type": view['type'],
        "tableId": view['tableId'],
        "xAxis": x_axis,
        "xAxisExt": view.get('xAxisExt', []),
        "yAxis": y_axis,
        "yAxisExt": view.get('yAxisExt', []),
        "extStack": [], "extBubble": [], "extLabel": [], "extTooltip": [],
        "customFilter": cf,
        "drill": False,
        "drillFields": [],
        "drillFilters": [],
        "senior": view.get('senior', {}),
        "resultCount": 100,
        "resultMode": "custom",
        "chartExtRequest": {"user": 1, "filter": [], "drill": [], "queryFrom": "panel", "resultCount": 100, "resultMode": "custom"}
    }
    
    start = time.time()
    r_data = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=query, timeout=300)
    elapsed = time.time() - start
    
    resp_data = r_data.json()
    code = resp_data.get('code', -1)
    print(f"Status: {r_data.status_code}, Code: {code}, Time: {elapsed:.1f}s")
    
    if code == 0:
        data = resp_data.get('data', {})
        table_data = data.get('data', {})
        fields = table_data.get('fields', [])
        rows = table_data.get('tableRow', [])
        print(f"Fields returned: {len(fields)}")
        print(f"Rows returned: {len(rows)}")
        
        if fields:
            print(f"\nColumn headers:")
            for f in fields:
                print(f"  {f.get('dataeaseName', '?'):10s} -> {f.get('name', '?')}")
        
        if rows:
            print(f"\nSample data (first 3 rows):")
            for row in rows[:3]:
                formatted = {}
                for f in fields:
                    dname = f.get('dataeaseName', '')
                    display = f.get('name', dname)
                    val = row.get(dname, '')
                    formatted[display] = val
                print(f"  {json.dumps(formatted, ensure_ascii=False)[:300]}")
    else:
        print(f"Error: {resp_data.get('msg', '')[:300]}")

print(f"\n=== Dashboard URLs ===")
print(f"Preview: {base}/#/preview/{panel_id}")
print(f"Edit:    {base}/#/dvCanvas?dvId={panel_id}&opt=edit")
