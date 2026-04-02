"""Compare findById responses for tea vs DSP via API."""
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

tea_id = '985192741891870720'
dsp_id = '1236050016221663232'

for name, did in [("Tea", tea_id), ("DSP", dsp_id)]:
    print(f"\n{'='*60}")
    print(f"=== {name} ({did}) - from core ===")
    
    # The frontend calls findById with body: {id: xxx, busiFlag: "dashboard"}
    r = requests.post(f'{base}/de2api/dataVisualization/findById',
                      headers=headers,
                      json={"id": did, "busiFlag": "dashboard"},
                      timeout=30)
    resp = r.json()
    
    if resp.get('code') != 0:
        print(f"Error: code={resp.get('code')}, msg={resp.get('msg')}")
        continue
    
    d = resp['data']
    
    # Key structure comparison
    print(f"  name: {d.get('name')}")
    print(f"  type: {d.get('type')}")
    print(f"  nodeType: {d.get('nodeType')}")
    print(f"  version: {d.get('version')}")
    print(f"  status: {d.get('status')}")
    
    # componentData
    cd = d.get('componentData')
    print(f"\n  componentData type: {type(cd).__name__}")
    if isinstance(cd, str):
        try:
            comps = json.loads(cd)
            print(f"  componentData parsed: {len(comps)} components")
        except:
            print(f"  componentData parse failed, first 200 chars: {cd[:200]}")
    else:
        print(f"  componentData: {cd}")
    
    # canvasStyleData
    csd = d.get('canvasStyleData')
    print(f"\n  canvasStyleData type: {type(csd).__name__}")
    if isinstance(csd, str):
        try:
            css = json.loads(csd)
            print(f"  canvasStyleData keys: {sorted(css.keys())}")
        except:
            print(f"  canvasStyleData parse failed: {csd[:200]}")
    
    # canvasViewInfo
    cvi = d.get('canvasViewInfo')
    print(f"\n  canvasViewInfo type: {type(cvi).__name__}")
    if isinstance(cvi, dict):
        print(f"  canvasViewInfo views: {len(cvi)}")
        for vid in list(cvi.keys())[:3]:
            v = cvi[vid]
            print(f"    {vid}: type={v.get('type')}, xAxis={len(v.get('xAxis',[]))}, yAxis={len(v.get('yAxis',[]))}")
    elif cvi is None:
        print(f"  canvasViewInfo is NULL!")
    
    # Check if componentData references match canvasViewInfo keys
    if isinstance(cd, str) and isinstance(cvi, dict):
        comps = json.loads(cd)
        comp_ids = [c.get('id') for c in comps if c.get('component') == 'UserView']
        view_ids = list(cvi.keys())
        print(f"\n  Component IDs (UserView): {comp_ids[:5]}")
        print(f"  View IDs: {view_ids[:5]}")
        matching = set(str(c) for c in comp_ids) & set(str(v) for v in view_ids)
        print(f"  Matching IDs: {matching}")
