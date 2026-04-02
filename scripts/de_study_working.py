"""Study a working dashboard's component structure for reference."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'

def tok():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page()
        pg.goto(base + '/', timeout=60000, wait_until='domcontentloaded')
        pg.wait_for_load_state('networkidle', timeout=30000)
        pg.wait_for_selector('input', timeout=10000)
        ins = pg.query_selector_all('input')
        ins[0].fill('admin')
        ins[1].fill('DataEase@123456')
        pg.query_selector('button').click()
        time.sleep(5)
        pg.wait_for_load_state('networkidle', timeout=30000)
        tr = pg.evaluate('() => localStorage.getItem("user.token")')
        jwt = json.loads(json.loads(tr)['v'])
        b.close()
        return jwt

h = {'x-de-token': tok(), 'Content-Type': 'application/json'}

# Find all panels
r = requests.post(base + '/de2api/dataVisualization/tree', headers=h,
                  json={'busiFlag': 'dataV', 'leafType': 'panel'}, timeout=30)
tree = r.json().get('data') or []

def find_panels(nodes, depth=0):
    res = []
    for n in (nodes or []):
        name = n.get('name', '')
        nid = n.get('id', '')
        print('  ' * depth + f'{name!r} id={nid}')
        if nid != '0':
            res.append(n)
        res.extend(find_panels(n.get('children'), depth + 1))
    return res

panels = find_panels(tree)

# Also check dashboard type
r2 = requests.post(base + '/de2api/dataVisualization/tree', headers=h,
                  json={'busiFlag': 'dashboard', 'leafType': 'panel'}, timeout=30)
tree2 = r2.json().get('data') or []
print('\n=== dashboard type tree ===')
find_panels(tree2)

# Find tea dashboard
tea_id = None
for p in panels:
    if '茶饮' in p.get('name', ''):
        tea_id = p['id']
        break

if tea_id:
    print(f'\n=== Tea dashboard: {tea_id} ===')
    r3 = requests.post(base + '/de2api/dataVisualization/findById', headers=h,
                       json={'id': tea_id, 'busiFlag': 'dataV', 'resourceTable': 'snapshot'}, timeout=30)
    d = r3.json().get('data') or {}
    print(f'type: {d.get("type")}, version: {d.get("version")}')
    comps = d.get('componentData', '[]')
    if isinstance(comps, str):
        comps = json.loads(comps)
    print(f'components: {len(comps)}')
    for c in comps[:5]:
        print(f'  {c.get("component")} / {c.get("innerType")} / canvasId={c.get("canvasId")}')
    cs = d.get('canvasStyleData', '{}')
    if isinstance(cs, str):
        cs = json.loads(cs)
    print(f'canvasStyle dashboard: {cs.get("dashboard")}')
    print(f'canvasStyle selfAdaption: {cs.get("selfAdaption")}')
    print(f'canvasStyle auxiliaryMatrix: {cs.get("auxiliaryMatrix")}')
