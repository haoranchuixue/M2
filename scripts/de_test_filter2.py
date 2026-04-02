"""Test customFilter with correct FilterTreeObj structure based on DataEase source code."""
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

# Get current chart view from published dashboard
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
views = r.json().get('data', {}).get('canvasViewInfo', {})
print(f"Views: {len(views)}")

for vid, vdata in views.items():
    print(f"\nChart: {vid}, type: {vdata.get('type')}")
    
    # Find create_date field
    date_field = None
    for f in vdata.get('xAxis', []):
        if f.get('originName') == 'create_date':
            date_field = f
            break
    if not date_field:
        for f in vdata.get('yAxis', []):
            if f.get('originName') == 'create_date':
                date_field = f
                break
    
    if not date_field:
        print("  No create_date field found, checking all fields...")
        all_axis = vdata.get('xAxis', []) + vdata.get('yAxis', [])
        for f in all_axis:
            print(f"    {f.get('originName')} (id={f.get('id')}, deType={f.get('deType')})")
        continue
    
    print(f"  Date field: id={date_field['id']}, deType={date_field['deType']}")
    
    # Test with properly structured FilterTreeObj
    # Based on source code:
    # FilterTreeObj: { logic: String, items: List<FilterTreeItem> }
    # FilterTreeItem: { type, fieldId(Long), field, filterType, term, value(String), enumValue, filterTypeTime, dynamicTimeSetting, timeType, subTree, valueType }
    
    test_view = json.loads(json.dumps(vdata))
    
    # Set customFilter with proper FilterTreeObj structure
    test_view['customFilter'] = {
        "logic": "and",
        "items": [
            {
                "type": "item",
                "fieldId": int(date_field['id']),
                "field": None,
                "filterType": "logic",
                "term": "ge",
                "value": "2026-03-23",
                "enumValue": None,
                "filterTypeTime": "dateValue",
                "dynamicTimeSetting": None,
                "timeType": None,
                "subTree": None,
                "valueType": None
            }
        ]
    }
    
    print(f"\n  Test: customFilter with create_date >= 2026-03-23")
    print(f"  customFilter: {json.dumps(test_view['customFilter'], ensure_ascii=False)}")
    
    r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view, timeout=120)
    resp = r2.json()
    print(f"  Code: {resp.get('code')}")
    
    if resp.get('code') == 0:
        data = resp.get('data', {})
        table_rows = data.get('tableRow', [])
        print(f"  Rows: {len(table_rows)}")
        if table_rows and len(table_rows) > 0:
            print(f"  First row: {json.dumps(table_rows[0], ensure_ascii=False)[:300]}")
        print("  *** SUCCESS ***")
    else:
        msg = resp.get('msg', '')
        print(f"  Error: {msg[:500]}")
        
        # If still fails, try alternative structures
        if 'copyBean' in msg or 'BeanUtils' in msg or msg == '':
            print("\n  Trying alternative: fieldId as string...")
            test_view2 = json.loads(json.dumps(vdata))
            test_view2['customFilter'] = {
                "logic": "and",
                "items": [
                    {
                        "type": "item",
                        "fieldId": str(date_field['id']),
                        "field": None,
                        "filterType": "logic",
                        "term": "ge",
                        "value": "2026-03-23",
                        "enumValue": None,
                        "filterTypeTime": None,
                        "dynamicTimeSetting": None,
                        "timeType": None,
                        "subTree": None,
                        "valueType": None
                    }
                ]
            }
            r3 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view2, timeout=120)
            resp3 = r3.json()
            print(f"  Code: {resp3.get('code')}")
            if resp3.get('code') == 0:
                data3 = resp3.get('data', {})
                rows3 = data3.get('tableRow', [])
                print(f"  Rows: {len(rows3)}")
                print("  *** SUCCESS with string fieldId ***")
            else:
                print(f"  Error: {resp3.get('msg', '')[:500]}")
                
                # Try with minimal structure
                print("\n  Trying minimal: just logic and items with fieldId only...")
                test_view3 = json.loads(json.dumps(vdata))
                test_view3['customFilter'] = {
                    "logic": "and",
                    "items": [
                        {
                            "type": "item",
                            "fieldId": str(date_field['id']),
                            "filterType": "logic",
                            "term": "ge",
                            "value": "2026-03-23"
                        }
                    ]
                }
                r4 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=test_view3, timeout=120)
                resp4 = r4.json()
                print(f"  Code: {resp4.get('code')}")
                if resp4.get('code') == 0:
                    data4 = resp4.get('data', {})
                    rows4 = data4.get('tableRow', [])
                    print(f"  Rows: {len(rows4)}")
                    print("  *** SUCCESS with minimal structure ***")
                else:
                    print(f"  Error: {resp4.get('msg', '')[:500]}")
