"""Find existing DSP Report dashboard and update it with new dataset chart."""
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

def api(path, data=None):
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=60)
    return r.json()

# Step 1: Find dashboards (type=dashboard)
print("=== Finding dashboards ===")
tree = api('/dataVisualization/interactiveTree', {"busiFlag": "dashboard", "type": "dashboard"})
datas = tree.get('data', [])

def find_panels(nodes, depth=0):
    results = []
    for n in nodes:
        name, nid, ntype = n.get('name',''), n.get('id',''), n.get('nodeType','')
        print(f"{'  '*depth}[{ntype}] {name} (id={nid})")
        if ntype in ('panel', 'dashboard'):
            results.append(n)
        for c in (n.get('children') or []):
            find_panels([c], depth+1)
            if c.get('nodeType') in ('panel', 'dashboard'):
                results.append(c)
    return results

all_panels = find_panels(datas)
print(f"\nFound {len(all_panels)} panels")

# Also try the dashboard tree
tree2 = api('/dataVisualization/tree', {"busiFlag": "dashboard", "leafType": "panel"})
datas2 = tree2.get('data', [])
print("\n=== Dashboard tree ===")
find_panels(datas2)

# Get DSP Report details
dsp_id = None
for item in all_panels:
    if 'DSP' in item.get('name', '') or 'dsp' in item.get('name', '').lower():
        dsp_id = item['id']
        break

# Try to find by listing all
if not dsp_id:
    for item in datas:
        if 'DSP' in item.get('name', '') or 'Report' in item.get('name', ''):
            dsp_id = item['id']
            break
        for c in (item.get('children') or []):
            if 'DSP' in c.get('name', '') or 'Report' in c.get('name', ''):
                dsp_id = c['id']
                break

if dsp_id:
    print(f"\n=== DSP Report found: {dsp_id} ===")
    # Get details
    for rt in ['snapshot', 'core']:
        r = api('/dataVisualization/findById', {"id": str(dsp_id), "busiFlag": "dashboard", "resourceTable": rt})
        d = r.get('data', {})
        if d:
            cvi = d.get('canvasViewInfo', {}) or {}
            comps = d.get('componentData', '[]')
            if isinstance(comps, str):
                comps = json.loads(comps)
            print(f"  {rt}: name={d.get('name')}, type={d.get('type')}, version={d.get('version')}, views={len(cvi)}, components={len(comps)}")
            if cvi:
                for vid, vinfo in cvi.items():
                    print(f"    View {vid}: type={vinfo.get('type')}, tableId={vinfo.get('tableId')}, x={len(vinfo.get('xAxis',[]))}, y={len(vinfo.get('yAxis',[]))}")
else:
    print("\nDSP Report not found. Let me create a new dashboard.")
    create_resp = api('/dataVisualization/saveCanvas', {
        "name": "ReportCenter DSP Report",
        "pid": "0",
        "type": "dashboard",
        "nodeType": "panel",
        "componentData": "[]",
        "canvasStyleData": json.dumps({"width":1920,"height":1080,"selfAdaption":True,"auxiliaryMatrix":True,"openCommonStyle":True,"panel":{"themeColor":"light","color":"#f5f6f7","imageUrl":"","borderRadius":0},"dashboard":{}}, separators=(',',':')),
        "busiFlag": "dashboard"
    })
    print(f"Create: code={create_resp.get('code')}, data={create_resp.get('data')}")
    if create_resp.get('code') == 0:
        dsp_id = create_resp['data']
    elif '重复' in str(create_resp.get('msg', '')):
        create_resp = api('/dataVisualization/saveCanvas', {
            "name": "ReportCenter DSP v2",
            "pid": "0",
            "type": "dashboard",
            "nodeType": "panel",
            "componentData": "[]",
            "canvasStyleData": json.dumps({"width":1920,"height":1080,"selfAdaption":True,"auxiliaryMatrix":True,"openCommonStyle":True,"panel":{"themeColor":"light","color":"#f5f6f7","imageUrl":"","borderRadius":0},"dashboard":{}}, separators=(',',':')),
            "busiFlag": "dashboard"
        })
        print(f"Create v2: code={create_resp.get('code')}, data={create_resp.get('data')}")
        if create_resp.get('code') == 0:
            dsp_id = create_resp['data']

print(f"\nUsing dashboard ID: {dsp_id}")
