"""Study working VQuery configurations from existing dashboards."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests

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
r = requests.post(f'{base}/de2api/dataVisualization/tree', headers=headers,
                  json={'busiFlag': 'dashboard', 'leaf': None, 'weight': 7}, timeout=30)
dashboards = r.json().get('data', [])
print(f'Total dashboard items: {len(dashboards)}')

for d in dashboards:
    if d.get('type') != 'folder':
        print(f'  [{d.get("id")}] {d.get("name")} type={d.get("type")}')

# Also check dataV (data screens)
r2 = requests.post(f'{base}/de2api/dataVisualization/tree', headers=headers,
                   json={'busiFlag': 'dataV', 'leaf': None, 'weight': 7}, timeout=30)
datavs = r2.json().get('data', [])
print(f'\nTotal dataV items: {len(datavs)}')
for d in datavs:
    if d.get('type') != 'folder':
        print(f'  [{d.get("id")}] {d.get("name")} type={d.get("type")}')

# Check each non-m2dashboard for VQuery components
all_items = [(d, 'dashboard') for d in dashboards] + [(d, 'dataV') for d in datavs]
for item, busi in all_items:
    if item.get('type') == 'folder':
        continue
    item_id = item.get('id')
    item_name = item.get('name', '')
    
    try:
        r3 = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                          json={'id': item_id, 'busiFlag': busi, 'resourceTable': 'snapshot'}, timeout=10)
        data = r3.json().get('data', {})
        comp_str = data.get('componentData', '[]')
        if isinstance(comp_str, str):
            components = json.loads(comp_str)
        else:
            components = comp_str or []
        
        has_vquery = any(c.get('component') == 'VQuery' for c in components)
        has_userview = any(c.get('component') == 'UserView' for c in components)
        
        if has_vquery:
            print(f'\n*** VQuery found in [{item_name}] (id={item_id}, busi={busi}) ***')
            for comp in components:
                if comp.get('component') == 'VQuery':
                    pv = comp.get('propValue', [])
                    if isinstance(pv, list):
                        for criterion in pv:
                            print(f'  Criterion: name={criterion.get("name")} displayType={criterion.get("displayType")}')
                            print(f'    checkedFields: {criterion.get("checkedFields")}')
                            cfm = criterion.get('checkedFieldsMap', {})
                            print(f'    checkedFieldsMap keys: {list(cfm.keys())}')
                            for k, v in cfm.items():
                                print(f'    checkedFieldsMap[{k}]: {json.dumps(v, ensure_ascii=False)[:300]}')
                            print(f'    defaultValueCheck: {criterion.get("defaultValueCheck")}')
                            print(f'    defaultValue: {criterion.get("defaultValue")}')
                            print(f'    conditionType: {criterion.get("conditionType")}')
                            print(f'    full criterion: {json.dumps(criterion, ensure_ascii=False)[:800]}')
                    elif isinstance(pv, dict):
                        print(f'  propValue is dict: {json.dumps(pv, ensure_ascii=False)[:500]}')
        elif item_name == 'm2dashboard':
            print(f'\n--- m2dashboard components ---')
            for comp in components:
                print(f'  component={comp.get("component")} id={comp.get("id")} name={comp.get("name")}')
                if comp.get('component') == 'VQuery':
                    pv = comp.get('propValue', [])
                    print(f'  propValue: {json.dumps(pv, ensure_ascii=False)[:1000]}')
    except Exception as e:
        pass

print('\nDone')
