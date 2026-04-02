"""Test data query with filter via chartExtRequest."""
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

dashboard_id = 1236050016221663232

# Get current chart view
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
views = r.json().get('data', {}).get('canvasViewInfo', {})

for vid, vdata in views.items():
    print(f"Chart: {vid}")
    
    # Get the create_date field info
    date_field = None
    for f in vdata.get('xAxis', []):
        if f.get('originName') == 'create_date':
            date_field = f
            break
    
    if date_field:
        print(f"  Date field ID: {date_field['id']}")
        print(f"  Date field deType: {date_field['deType']}")
    
    # Test 1: Add chartExtRequest with filter
    test_view = json.loads(json.dumps(vdata))
    test_view['chartExtRequest'] = {
        "filter": [{
            "componentId": "",
            "fieldId": date_field['id'] if date_field else "",
            "operator": "ge",
            "value": ["2026-03-23"],
            "isTree": False
        }],
        "goPage": 1,
        "pageSize": 100,
        "resultMode": "custom",
        "resultCount": 100
    }
    
    print(f"\n  Test 1: chartExtRequest with date filter >= 2026-03-23")
    r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view, timeout=120)
    resp = r2.json()
    print(f"  Code: {resp.get('code')}")
    if resp.get('code') == 0:
        data = resp.get('data', {})
        table_rows = data.get('tableRow', [])
        print(f"  Rows: {len(table_rows)}")
        if table_rows:
            print(f"  First row: {json.dumps(table_rows[0], ensure_ascii=False)[:300]}")
        print("  *** SUCCESS ***")
    else:
        print(f"  Error: {resp.get('msg', '')[:300]}")
    
    # Test 2: Use xAxis field filter
    test_view2 = json.loads(json.dumps(vdata))
    for f in test_view2.get('xAxis', []):
        if f.get('originName') == 'create_date':
            f['filter'] = [{
                "term": "ge",
                "value": "2026-03-23",
                "fieldId": f['id']
            }]
    
    print(f"\n  Test 2: field-level filter on create_date >= 2026-03-23")
    r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view2, timeout=120)
    resp3 = r3.json()
    print(f"  Code: {resp3.get('code')}")
    if resp3.get('code') == 0:
        data = resp3.get('data', {})
        table_rows = data.get('tableRow', [])
        print(f"  Rows: {len(table_rows)}")
        if table_rows:
            print(f"  First row: {json.dumps(table_rows[0], ensure_ascii=False)[:300]}")
        print("  *** SUCCESS ***")
    else:
        print(f"  Error: {resp3.get('msg', '')[:300]}")

    # Test 3: customFilter with date condition
    test_view3 = json.loads(json.dumps(vdata))
    test_view3['customFilter'] = {
        "logic": "and",
        "items": [{
            "type": "tree",
            "logic": "and",
            "items": [{
                "type": "item",
                "fieldId": date_field['id'] if date_field else "",
                "filterType": "condition",
                "term": "ge",
                "value": ["2026-03-23"]
            }]
        }]
    }
    
    print(f"\n  Test 3: customFilter tree with date >= 2026-03-23")
    r4 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view3, timeout=120)
    resp4 = r4.json()
    print(f"  Code: {resp4.get('code')}")
    if resp4.get('code') == 0:
        data = resp4.get('data', {})
        table_rows = data.get('tableRow', [])
        print(f"  Rows: {len(table_rows)}")
        if table_rows:
            print(f"  First row: {json.dumps(table_rows[0], ensure_ascii=False)[:300]}")
        print("  *** SUCCESS ***")
    else:
        print(f"  Error: {resp4.get('msg', '')[:300]}")
