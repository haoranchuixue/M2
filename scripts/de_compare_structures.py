"""Compare component structures between tea dashboard and DSP Report."""
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

tea_id = '985192741891870720'
dsp_id = '1236050016221663232'

# Get both dashboards from core
for name, did in [("Tea", tea_id), ("DSP", dsp_id)]:
    print(f"\n{'='*60}")
    print(f"=== {name} Dashboard ({did}) ===")
    r = api('/dataVisualization/findById', {"id": did, "busiFlag": "dashboard", "resourceTable": "core"})
    d = r.get('data', {})
    
    # Component data
    comp_str = d.get('componentData', '[]')
    if isinstance(comp_str, str):
        comps = json.loads(comp_str)
    else:
        comps = comp_str or []
    
    print(f"Components: {len(comps)}")
    for i, comp in enumerate(comps):
        print(f"\n  Component #{i}:")
        print(f"    id: {comp.get('id')}")
        print(f"    component: {comp.get('component')}")
        print(f"    innerType: {comp.get('innerType')}")
        print(f"    label: {comp.get('label')}")
        print(f"    x={comp.get('x')}, y={comp.get('y')}, sizeX={comp.get('sizeX')}, sizeY={comp.get('sizeY')}")
        style = comp.get('style', {})
        print(f"    style: w={style.get('width')}, h={style.get('height')}, l={style.get('left')}, t={style.get('top')}")
        pv = comp.get('propValue', {})
        print(f"    propValue: {json.dumps(pv, ensure_ascii=False)[:200]}")
        print(f"    render: {comp.get('render')}")
        
        # Print keys that differ between tea and dsp
        keys = sorted(comp.keys())
        print(f"    keys ({len(keys)}): {keys}")
    
    # Canvas view info
    cvi = d.get('canvasViewInfo', {}) or {}
    print(f"\nCanvas Views: {len(cvi)}")
    for vid, vinfo in cvi.items():
        print(f"  View {vid}:")
        print(f"    type: {vinfo.get('type')}")
        print(f"    tableId: {vinfo.get('tableId')}")
        print(f"    xAxis: {len(vinfo.get('xAxis', []))}")
        print(f"    yAxis: {len(vinfo.get('yAxis', []))}")
    
    # Canvas style
    css = d.get('canvasStyleData', '{}')
    if isinstance(css, str):
        css = json.loads(css)
    print(f"\nCanvas style keys: {sorted(css.keys()) if css else 'None'}")
    print(f"  auxiliaryMatrix: {css.get('auxiliaryMatrix')}")
    print(f"  dashboard: {css.get('dashboard')}")
    
    # Save first component of each for detailed comparison
    if comps:
        with open(f'd:/Projects/m2/scripts/comp_{name.lower()}.json', 'w', encoding='utf-8') as f:
            json.dump(comps[0], f, indent=2, ensure_ascii=False)
        print(f"  First component saved to comp_{name.lower()}.json")
