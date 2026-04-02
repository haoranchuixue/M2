"""Find all available datasets and datasources in gray DataEase."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

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

# List dataset tree
print('=== Dataset Tree ===')
r = requests.post(f'{base}/de2api/datasetTree/tree', headers=headers, json={"leafType": "dataset"}, timeout=30)
print(f'Status: {r.status_code}')
data = r.json()
print(f'Code: {data.get("code")}, keys: {list(data.keys()) if isinstance(data, dict) else ""}')

def walk_tree(nodes, depth=0):
    results = []
    for n in (nodes or []):
        nid = n.get('id', '')
        name = n.get('name', '')
        nt = n.get('nodeType', n.get('type', ''))
        leaf = n.get('leaf', False)
        print('  ' * depth + f'{name!r} id={nid} type={nt} leaf={leaf}')
        results.append(n)
        results.extend(walk_tree(n.get('children'), depth + 1))
    return results

tree_data = data.get('data', [])
all_nodes = walk_tree(tree_data if isinstance(tree_data, list) else [tree_data] if tree_data else [])

# Try getting details for each dataset
datasets = [n for n in all_nodes if n.get('leaf') or n.get('nodeType') == 'dataset']
print(f'\n=== Found {len(datasets)} datasets ===')
for ds in datasets[:10]:
    ds_id = ds.get('id')
    ds_name = ds.get('name')
    print(f'\nDataset: {ds_name!r} (id={ds_id})')
    r2 = requests.post(f'{base}/de2api/datasetTree/details/{ds_id}', headers=headers, json={}, timeout=30)
    d2 = r2.json()
    if d2.get('data'):
        fields = d2['data'].get('allFields') or []
        print(f'  Fields: {len(fields)}')
        for f in fields[:8]:
            print(f'    {f.get("originName")} ({f.get("type")})')
        if len(fields) > 8:
            print(f'    ... and {len(fields)-8} more')
    else:
        print(f'  No data (code={d2.get("code")}, msg={str(d2.get("msg",""))[:100]})')

# Also try datasource endpoints
print('\n=== Datasources ===')
for ep in ['datasource/list', 'datasource/listDatasource']:
    r3 = requests.post(f'{base}/de2api/{ep}', headers=headers, json={}, timeout=30)
    print(f'{ep}: {r3.status_code} {str(r3.text[:500])}')

# Try GET on datasource
r4 = requests.get(f'{base}/de2api/datasource/list', headers=headers, timeout=30)
print(f'GET datasource/list: {r4.status_code} {r4.text[:500]}')
