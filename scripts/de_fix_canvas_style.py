"""Fix canvasStyleData to match tea dashboard structure."""
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

panel_id = "1236050016221663232"

# Get current state
snap = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dashboard", "resourceTable": "snapshot"})
snap_data = snap['data']
cur_version = snap_data.get('version') or 1
print(f"Version: {cur_version}")

# Get existing component and chart view
comp_str = snap_data.get('componentData', '[]')
comps = json.loads(comp_str) if isinstance(comp_str, str) else (comp_str or [])
cvi = snap_data.get('canvasViewInfo', {}) or {}
print(f"Components: {len(comps)}, Views: {len(cvi)}")

# Fix: Use canvasStyleData matching tea dashboard structure
canvas_style = {
    "width": 1920,
    "height": 1080,
    "scale": 100,
    "scaleWidth": 100,
    "scaleHeight": 100,
    "opacity": 1,
    "fontSize": 14,
    "backgroundType": "color",
    "background": "",
    "backgroundColor": "#f5f6f7",
    "backgroundColorSelect": True,
    "backgroundImageEnable": False,
    "color": "#ffffff",
    "themeId": "",
    "refreshViewEnable": False,
    "refreshViewLoading": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
    "openCommonStyle": True,
    "dashboard": {
        "gap": "yes",
        "gapSize": 5,
        "resultMode": "all",
        "resultCount": 1000,
        "themeColor": "light",
        "mobileSetting": {
            "customSetting": False,
            "imageUrl": None,
            "backgroundType": "image",
            "color": "#000"
        }
    },
    "component": {
        "commonBackground": {
            "backgroundType": "color",
            "color": "#ffffff",
            "alpha": 100,
            "borderRadius": 5,
            "innerPadding": 12,
            "outerPadding": 2,
            "borderWidth": 0,
            "borderColor": "#DCDFE6",
            "borderStyle": "solid"
        }
    }
}

compact_style = json.dumps(canvas_style, separators=(',', ':'))
compact_comp = json.dumps(comps, separators=(',', ':'), ensure_ascii=False)

# Verify component ID pattern
for c in comps:
    cid = c.get('id')
    pattern = f'"id":"{cid}"'
    if pattern not in compact_comp:
        pattern2 = f'"id":{cid}'
        if pattern2 not in compact_comp:
            print(f"WARNING: Pattern for {cid} not found!")
        else:
            print(f"Component ID {cid} found (numeric)")
    else:
        print(f"Component ID {cid} found (string)")

update_payload = {
    "id": panel_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": compact_comp,
    "canvasStyleData": compact_style,
    "canvasViewInfo": cvi,
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": str(snap_data.get('contentId', '0')),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0
}

print(f"\n=== Updating canvas style ===")
r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=update_payload, timeout=60)
print(f"HTTP: {r.status_code}")
if r.status_code == 200:
    resp = r.json()
    print(f"Code: {resp.get('code')}")
    if resp.get('code') == 0:
        pub = api('/dataVisualization/updatePublishStatus',
                   {"id": panel_id, "type": "dashboard", "busiFlag": "dashboard", "status": 1, "pid": 0})
        print(f"Publish: {pub.get('code')}")
        
        # Verify
        v = api('/dataVisualization/findById', {"id": panel_id, "busiFlag": "dashboard"})
        vd = v['data']
        vcsd = json.loads(vd['canvasStyleData']) if isinstance(vd['canvasStyleData'], str) else vd['canvasStyleData']
        print(f"Updated canvasStyleData keys: {sorted(vcsd.keys())}")
        
        # Take screenshot
        print("\n=== Screenshot ===")
        with sync_playwright() as pw:
            br = pw.chromium.launch(headless=True)
            pg = br.new_page(viewport={"width": 1920, "height": 1080})
            pg.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
            pg.wait_for_load_state('networkidle', timeout=30000)
            pg.wait_for_selector('input', timeout=10000)
            ins = pg.query_selector_all('input')
            ins[0].fill('admin')
            ins[1].fill('DataEase@123456')
            pg.query_selector('button').click()
            time.sleep(5)
            pg.wait_for_load_state('networkidle', timeout=30000)
            
            # Track API
            api_calls = []
            def on_resp(response):
                if '/de2api/' in response.url and ('getData' in response.url or 'findById' in response.url):
                    try:
                        body = response.json()
                        api_calls.append(f"{response.url.split('/de2api/')[1]}: code={body.get('code')}")
                    except:
                        pass
            pg.on('response', on_resp)
            
            pg.goto(f'{base}/#/panel/index?dvId={panel_id}', timeout=60000)
            time.sleep(60)
            
            pg.screenshot(path='d:/Projects/m2/scripts/ss_style_fixed.png')
            print(f"API calls: {len(api_calls)}")
            for c in api_calls:
                print(f"  {c}")
            
            br.close()
    else:
        print(f"Error: {resp.get('msg')}")
else:
    print(f"Error: {r.text[:500]}")
