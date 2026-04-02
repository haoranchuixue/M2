"""Debug updateCanvas API by trying minimal payloads."""
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

dashboard_id = 1236050016221663232

# Try minimal update first - just change the name
payloads = [
    # 1. Minimal: just update name
    {
        "id": dashboard_id,
        "type": "dashboard",
        "busiFlag": "dashboard",
        "componentData": "[]",
        "canvasStyleData": "{}",
        "canvasViewInfo": {},
    },
    # 2. With string ID
    {
        "id": str(dashboard_id),
        "type": "dashboard",
        "busiFlag": "dashboard",
        "componentData": "[]",
        "canvasStyleData": "{}",
        "canvasViewInfo": {},
    },
    # 3. With checkVersion
    {
        "id": dashboard_id,
        "type": "dashboard",
        "busiFlag": "dashboard",
        "componentData": "[]",
        "canvasStyleData": "{}",
        "canvasViewInfo": {},
        "checkVersion": "1",
    },
    # 4. With more fields from the findById response
    {
        "id": dashboard_id,
        "name": "DSP Report",
        "pid": 0,
        "type": "dashboard",
        "busiFlag": "dashboard",
        "componentData": "[]",
        "canvasStyleData": json.dumps({"width":1920,"height":1080,"selfAdaption":True,"auxiliaryMatrix":True,"openCommonStyle":True,"panel":{"themeColor":"light","color":"#ffffff","imageUrl":"","borderRadius":0},"dashboard":{}}),
        "canvasViewInfo": {},
        "checkVersion": "1",
        "version": 3,
        "contentId": "0",
        "status": 0,
        "mobileLayout": False,
        "selfWatermarkStatus": False,
        "extFlag": 0,
    },
]

for i, payload in enumerate(payloads):
    r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', 
                      headers=headers, json=payload, timeout=30)
    print(f"\nPayload {i+1}: Status {r.status_code}")
    print(f"  Response: {r.text[:500]}")
    if r.status_code == 200:
        resp = r.json()
        print(f"  Code: {resp.get('code')}, Msg: {(resp.get('msg') or '')[:200]}")
        if resp.get('code') == 0:
            print(f"  *** SUCCESS! ***")
            break
