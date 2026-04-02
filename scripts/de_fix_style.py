"""Fix the dashboard canvasStyleData to match the proper dashboard format."""
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

# Get current dashboard data
r = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                 json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "snapshot"}, timeout=30)
cur_data = r.json().get('data', {})

# Get the existing componentData (already has our chart)
existing_comp = cur_data.get('componentData', '[]')
existing_views = cur_data.get('canvasViewInfo', {})
cur_version = cur_data.get('version', 4)

print(f"Current version: {cur_version}")
print(f"Current views: {len(existing_views)}")
print(f"Components preview: {existing_comp[:100]}")

# Build proper canvasStyleData matching the tea dashboard
canvas_style = {
    "width": 1920,
    "height": 1080,
    "refreshViewEnable": False,
    "refreshViewLoading": False,
    "refreshUnit": "minute",
    "refreshTime": 5,
    "scale": 60,
    "scaleWidth": 100,
    "scaleHeight": 100,
    "selfAdaption": True,
    "auxiliaryMatrix": True,
    "backgroundColorSelect": True,
    "backgroundImageEnable": False,
    "backgroundType": "backgroundColor",
    "background": "",
    "openCommonStyle": True,
    "opacity": 1,
    "fontSize": 14,
    "themeId": "10001",
    "color": "#000000",
    "backgroundColor": "rgba(245, 246, 247, 1)",
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
        "chartTitle": {
            "show": True,
            "fontSize": "18",
            "hPosition": "left",
            "vPosition": "top",
            "isItalic": False,
            "isBolder": True,
            "remarkShow": False,
            "remark": "",
            "fontFamily": "Microsoft YaHei",
            "letterSpace": "0",
            "fontShadow": False,
            "color": "#000000",
            "remarkBackgroundColor": "#ffffff"
        },
        "chartColor": {
            "basicStyle": {
                "colorScheme": "default",
                "colors": ["#1E90FF","#90EE90","#00CED1","#E2BD84","#7A90E0","#3BA272","#2BE7FF","#0A8ADA","#FFD700"],
                "alpha": 100,
                "gradient": True,
                "mapStyle": "normal",
                "areaBaseColor": "#FFFFFF",
                "areaBorderColor": "#303133",
                "gaugeStyle": "default",
                "tableBorderColor": "#E6E7E4",
                "tableScrollBarColor": "#00000024"
            }
        },
        "chartCommonStyle": {
            "backgroundColorSelect": True,
            "innerPadding": 12,
            "borderRadius": 5,
            "backgroundColor": "rgba(255, 255, 255, 1)"
        },
        "filterStyle": {
            "horizontal": "left",
            "vertical": "top",
            "color": "#000000",
            "brColor": "#dcdfe6",
            "wordColor": "#606266",
            "innerBgColor": "#FFFFFF"
        },
        "tabStyle": {
            "headFontColor": "#000000",
            "headFontActiveColor": "#000000",
            "headBorderColor": "#FFFFFF",
            "headBorderActiveColor": "#1094E5"
        }
    }
}

# Re-fetch the chart view from canvasViewInfo to include it
# We need to re-send the canvasViewInfo because it was already saved
chart_views_payload = {}
for vid, vdata in existing_views.items():
    chart_views_payload[str(vid)] = vdata

update_payload = {
    "id": dashboard_id,
    "name": "DSP Report",
    "pid": 0,
    "type": "dashboard",
    "busiFlag": "dashboard",
    "componentData": existing_comp,
    "canvasStyleData": json.dumps(canvas_style, separators=(',', ':')),
    "canvasViewInfo": chart_views_payload,
    "checkVersion": str(cur_version),
    "version": cur_version + 1,
    "contentId": cur_data.get('contentId', '0'),
    "status": 0,
    "mobileLayout": False,
    "selfWatermarkStatus": False,
    "extFlag": 0,
}

print(f"\n=== Updating canvasStyleData ===")
r2 = requests.post(f'{base}/de2api/dataVisualization/updateCanvas',
                   headers=headers, json=update_payload, timeout=60)
print(f"HTTP Status: {r2.status_code}")

if r2.status_code == 200:
    resp = r2.json()
    print(f"Code: {resp.get('code')}, Msg: {resp.get('msg')}")
    
    if resp.get('code') == 0:
        # Publish
        pub = requests.post(f'{base}/de2api/dataVisualization/updatePublishStatus',
                           headers=headers,
                           json={"id": dashboard_id, "type": "dashboard",
                                 "busiFlag": "dashboard", "status": 1, "pid": 0},
                           timeout=30)
        print(f"Publish: {pub.status_code}")
        
        # Verify
        verify = requests.post(f'{base}/de2api/dataVisualization/findById', headers=headers,
                              json={"id": dashboard_id, "busiFlag": "dashboard", "resourceTable": "core"}, timeout=30)
        v_data = verify.json().get('data', {})
        v_views = v_data.get('canvasViewInfo', {})
        v_style = v_data.get('canvasStyleData', '')
        print(f"Views: {len(v_views)}")
        print(f"Style preview: {v_style[:200]}")
        print(f"\nDashboard updated: {base}/#/panel/index?dvId={dashboard_id}")
else:
    print(f"Error: {r2.text[:500]}")
