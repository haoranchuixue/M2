"""Test with narrow date filter (1 day) to fit within CPU limit."""
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

r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
views = r.json().get('data', {}).get('canvasViewInfo', {})

for vid, vdata in views.items():
    date_field = None
    for f in vdata.get('xAxis', []):
        if f.get('originName') == 'create_date':
            date_field = f
            break
    
    if not date_field:
        print("No create_date field")
        continue
    
    # Test 1: Single day filter (yesterday)
    for days_back, label in [(1, "2026-03-29"), (3, "2026-03-27")]:
        test_view = json.loads(json.dumps(vdata))
        test_view['customFilter'] = {
            "logic": "and",
            "items": [
                {
                    "type": "item",
                    "fieldId": int(date_field['id']),
                    "filterType": "logic",
                    "term": "eq",
                    "value": label,
                    "filterTypeTime": "dateValue"
                }
            ]
        }
        
        print(f"\nTest: create_date = {label}")
        r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view, timeout=180)
        resp = r2.json()
        code = resp.get('code')
        print(f"  Code: {code}")
        
        if code == 0:
            data = resp.get('data', {})
            table_rows = data.get('tableRow', [])
            print(f"  Rows: {len(table_rows)}")
            if table_rows:
                print(f"  First row: {json.dumps(table_rows[0], ensure_ascii=False)[:300]}")
            
            sql = resp.get('data', {}).get('sql', '')
            if sql:
                print(f"  SQL: {sql[:300]}")
            
            print("  *** SUCCESS ***")
            break
        else:
            print(f"  Error: {resp.get('msg', '')[:200]}")
    
    # Test 2: Use table-info with LIMIT + date filter
    print(f"\n\nTest: table-info with 1-day filter and LIMIT")
    test_view2 = json.loads(json.dumps(vdata))
    test_view2['type'] = 'table-info'
    test_view2['resultMode'] = 'custom'
    test_view2['resultCount'] = 100
    test_view2['customFilter'] = {
        "logic": "and",
        "items": [
            {
                "type": "item",
                "fieldId": int(date_field['id']),
                "filterType": "logic",
                "term": "eq",
                "value": "2026-03-29",
                "filterTypeTime": "dateValue"
            }
        ]
    }
    
    r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view2, timeout=180)
    resp3 = r3.json()
    print(f"  Code: {resp3.get('code')}")
    if resp3.get('code') == 0:
        data3 = resp3.get('data', {})
        rows3 = data3.get('tableRow', [])
        print(f"  Rows: {len(rows3)}")
        if rows3:
            print(f"  First row: {json.dumps(rows3[0], ensure_ascii=False)[:300]}")
        print("  *** SUCCESS ***")
    else:
        print(f"  Error: {resp3.get('msg', '')[:200]}")
