"""Check existing dashboards to understand canvasViewInfo structure."""
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

# List all dashboards
r = requests.post(f'{base}/de2api/dataVisualization/interactiveTree', headers=headers,
                 json={"busiFlag": "dashboard"}, timeout=30)
dashboards = r.json().get('data', [])
print(f"Found {len(dashboards)} items in dashboard tree")

# Find dashboards (not folders) and check for ones with actual charts
for db in dashboards:
    if db.get('type') == 'dashboard' and db.get('id') != 1236050016221663232:
        db_id = db['id']
        db_name = db.get('name', 'unknown')
        # Get details
        r2 = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                          json={"id": db_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
        d = r2.json().get('data', {})
        views = d.get('canvasViewInfo', {})
        comp_str = d.get('componentData', '[]')
        try:
            comps = json.loads(comp_str) if isinstance(comp_str, str) else comp_str
        except:
            comps = []
        
        if views:
            print(f"\n=== Dashboard: {db_name} (id={db_id}) ===")
            print(f"  Components count: {len(comps)}")
            print(f"  Views count: {len(views)}")
            
            for vid, vdata in views.items():
                print(f"\n  --- View ID: {vid} ---")
                print(f"  Type: {vdata.get('type')}")
                print(f"  Title: {vdata.get('title')}")
                print(f"  TableId (dataset): {vdata.get('tableId')}")
                # Print all top-level keys
                print(f"  Keys: {list(vdata.keys())}")
                # Print full view data to file
                with open(f'd:\\Projects\\m2\\scripts\\existing_view_{vid}.json', 'w', encoding='utf-8') as f:
                    json.dump(vdata, f, indent=2, ensure_ascii=False)
                print(f"  Saved to existing_view_{vid}.json")
                
                # Check types of key fields
                for key in ['xAxis', 'yAxis', 'customAttr', 'customStyle', 'customFilter', 'senior']:
                    val = vdata.get(key)
                    if val is not None:
                        print(f"  {key}: type={type(val).__name__}, preview={json.dumps(val, ensure_ascii=False)[:100]}")
            
            # Also save component data
            if comps:
                with open(f'd:\\Projects\\m2\\scripts\\existing_comp_{db_id}.json', 'w', encoding='utf-8') as f:
                    json.dump(comps, f, indent=2, ensure_ascii=False)
                print(f"  Saved components to existing_comp_{db_id}.json")
            break  # Just need one example
