"""Debug updateCanvas - try minimal payload first."""
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

panel_id = "1236081407923720192"

# Get current state with different busiFlag options
for bf in ["dataV", "dashboard", None]:
    body = {"id": panel_id}
    if bf:
        body["busiFlag"] = bf
    body["resourceTable"] = "snapshot"
    r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers, json=body, timeout=30)
    resp = r.json()
    code = resp.get('code')
    data = resp.get('data', {})
    if code == 0 and data:
        print(f"\nbusiFlag={bf}: code={code}")
        print(f"  name={data.get('name')}, type={data.get('type')}, version={data.get('version')}")
        print(f"  contentId={data.get('contentId')}, status={data.get('status')}")
        print(f"  pid={data.get('pid')}, id={data.get('id')}")
        csd = data.get('canvasStyleData', '{}')
        print(f"  canvasStyleData: {str(csd)[:200]}")
        cd = data.get('componentData', '[]')
        print(f"  componentData: {str(cd)[:200]}")
        cvi = data.get('canvasViewInfo', {})
        print(f"  canvasViewInfo: {json.dumps(cvi, ensure_ascii=False)[:200] if cvi else 'None'}")
    else:
        print(f"\nbusiFlag={bf}: code={code}, msg={resp.get('msg','')[:200]}")

# Also try findById/{id} (path param)
r2 = requests.post(f'{base}/de2api/dataVisualization/findById/{panel_id}', headers=headers, json={}, timeout=30)
resp2 = r2.json()
if resp2.get('code') == 0:
    data2 = resp2['data']
    print(f"\nfindById/{{id}}: name={data2.get('name')}, type={data2.get('type')}, version={data2.get('version')}")

# Try minimal updateCanvas
print("\n\n=== Attempt 1: Minimal update with empty components ===")
for bf in ["dataV", "dashboard"]:
    payload = {
        "id": panel_id,
        "name": "ReportCenter - DSP Report",
        "pid": 0,
        "type": bf,
        "busiFlag": bf,
        "componentData": "[]",
        "canvasStyleData": json.dumps({"width":1600,"height":900,"selfAdaption":True,"auxiliaryMatrix":True}, separators=(',', ':')),
        "canvasViewInfo": {},
        "checkVersion": "3",
        "version": 4,
        "contentId": "0",
        "status": 0,
        "mobileLayout": False,
        "selfWatermarkStatus": False,
        "extFlag": 0
    }
    r = requests.post(f'{base}/de2api/dataVisualization/updateCanvas', headers=headers, json=payload, timeout=30)
    print(f"  busiFlag={bf}: status={r.status_code}, body={r.text[:300]}")
    if r.status_code == 200:
        resp = r.json()
        print(f"  code={resp.get('code')}, msg={str(resp.get('msg',''))[:200]}")
