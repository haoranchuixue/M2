"""Build DSP Report dataset and dashboard in DataEase."""
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

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

sr_ds_id = '1236022373120086016'

# Step 1: Get the dataset tree to find existing DSP Report group
print("=== Dataset Tree ===")
tree = api('/datasetTree/tree', {'busiFlag': 'dataset'})
dsp_group_id = None

def find_node(nodes, name):
    if not nodes:
        return None
    for n in nodes:
        if n.get('name') == name:
            return n
        found = find_node(n.get('children'), name)
        if found:
            return found
    return None

if tree.get('data'):
    # Print tree structure
    def print_tree(nodes, indent=0):
        if not nodes:
            return
        for n in nodes:
            print(f"{'  '*indent}{n.get('name')} (id={n.get('id')}, leaf={n.get('leaf')}, type={n.get('type')})")
            print_tree(n.get('children'), indent+1)
    print_tree(tree['data'])
    
    dsp_node = find_node(tree['data'], 'DSP Report')
    if dsp_node:
        dsp_group_id = dsp_node['id']
        print(f"\nFound DSP Report group: id={dsp_group_id}")

# Step 2: Look at an existing dataset to understand structure
print("\n=== Existing dataset details ===")
example_node = find_node(tree['data'], '茶饮原料费用')
if example_node:
    print(f"Example dataset: {example_node.get('name')}, id={example_node.get('id')}")
    # Get its details
    detail = api(f'/datasetTree/details', {'id': example_node['id']})
    if detail.get('data'):
        data = detail['data']
        # Save full details
        with open('d:/Projects/m2/scripts/example_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Details saved. Keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
        print(json.dumps(data, ensure_ascii=False)[:2000])
    else:
        print(f"Detail error: {json.dumps(detail, ensure_ascii=False)[:500]}")
        
        # Try other endpoints
        for ep in ['/dataset/details', '/datasetTable/detail']:
            detail2 = api(ep, {'id': example_node['id']})
            if detail2.get('data'):
                print(f"\n{ep} succeeded:")
                print(json.dumps(detail2['data'], ensure_ascii=False)[:2000])
                break

# Step 3: Get table fields for creating SQL dataset
print("\n=== Getting SQL dataset field structure ===")
# Let's first try to preview SQL to see what the API expects
preview_result = api('/datasource/executeSql', {
    'datasourceId': sr_ds_id,
    'sql': "SELECT create_date, SUM(request_count) as request_count FROM dsp_report WHERE create_date = '2026-03-29' GROUP BY create_date LIMIT 5"
})
print(f"SQL preview: {json.dumps(preview_result, ensure_ascii=False)[:1000]}")
