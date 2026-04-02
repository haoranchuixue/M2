"""Check what's actually stored in the dashboard after updates."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
PANEL_ID = '1236081407923720192'

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

for rt in ['snapshot', 'core']:
    r = requests.post(
        base + '/de2api/dataVisualization/findById',
        headers=h,
        json={'id': PANEL_ID, 'busiFlag': 'dataV', 'resourceTable': rt},
        timeout=30,
    )
    d = r.json().get('data') or {}
    cvi = d.get('canvasViewInfo') or {}
    comps = d.get('componentData', '[]')
    if isinstance(comps, str):
        comps_list = json.loads(comps)
    else:
        comps_list = comps or []
    print(f'=== {rt} ===')
    print(f'  version: {d.get("version")}')
    print(f'  status: {d.get("status")}')
    print(f'  type: {d.get("type")}')
    print(f'  components: {len(comps_list)}')
    print(f'  canvasViewInfo keys: {list(cvi.keys())}')
    for c in comps_list:
        print(f'    {c.get("component")} / {c.get("innerType")} / canvasId={c.get("canvasId")} / id={c.get("id")}')
    cs = d.get('canvasStyleData', '{}')
    if isinstance(cs, str):
        cs = json.loads(cs)
    print(f'  canvasStyle keys: {list(cs.keys()) if isinstance(cs, dict) else "?"}')
    print(f'  canvasStyle dashboard: {cs.get("dashboard") if isinstance(cs, dict) else "?"}')
