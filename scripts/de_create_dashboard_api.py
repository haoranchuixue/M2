"""Create DSP Report dashboard via DataEase saveCanvas API."""
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
    r = requests.post(f'{base}/de2api{path}', headers=headers, json=data or {}, timeout=30)
    return r.json()

# Create dashboard via saveCanvas
print("=== Creating Dashboard via saveCanvas ===")

dashboard_payload = {
    "name": "DSP Report",
    "pid": "0",
    "type": "dashboard",
    "componentData": "[]",
    "canvasStyleData": json.dumps({
        "width": 1920,
        "height": 1080,
        "selfAdaption": True,
        "auxiliaryMatrix": True,
        "openCommonStyle": True,
        "panel": {
            "themeColor": "light",
            "color": "#ffffff",
            "imageUrl": "",
            "borderRadius": 0
        },
        "dashboard": {}
    }),
    "watermarkInfo": None,
    "dynamicData": None,
    "linkageActive": False,
    "busiFlag": "dashboard"
}

result = api('/dataVisualization/saveCanvas', dashboard_payload)
print(f"Code: {result.get('code')}")
msg = result.get('msg') or ''
print(f"Msg: {msg[:500]}")
data = result.get('data')
print(f"Data: {str(data)[:500]}")

if result.get('code') == 0 and data:
    dashboard_id = data
    print(f"\n*** Dashboard created! ID: {dashboard_id} ***")
    
    # Save the ID for later use
    with open('d:/Projects/m2/scripts/dashboard_id.txt', 'w') as f:
        f.write(str(dashboard_id))
    
    # Now verify by getting the dashboard
    print("\n=== Verifying dashboard ===")
    detail = api('/dataVisualization/findById', {'id': str(dashboard_id), 'busiFlag': 'dashboard'})
    print(f"Detail code: {detail.get('code')}")
    if detail.get('data'):
        d = detail['data']
        print(f"  Name: {d.get('name')}")
        print(f"  ID: {d.get('id')}")
        print(f"  Type: {d.get('type')}")
        with open('d:/Projects/m2/scripts/dashboard_detail.json', 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        print("  Full detail saved to dashboard_detail.json")
