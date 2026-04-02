"""Intercept the findById response for both tea and DSP dashboards."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
tea_id = '985192741891870720'
dsp_id = '1236050016221663232'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Login
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    
    # Capture findById responses
    captured = {}
    def on_response(response):
        if 'findById' in response.url and '/de2api/' in response.url:
            try:
                body = response.json()
                if body.get('code') == 0 and body.get('data'):
                    d = body['data']
                    name = d.get('name', '?')
                    captured[name] = d
                    print(f"\nCaptured findById for: {name}")
                    print(f"  type: {d.get('type')}")
                    print(f"  version: {d.get('version')}")
                    
                    # Compare key fields
                    comp_data = d.get('componentData', '[]')
                    if isinstance(comp_data, str):
                        comps = json.loads(comp_data)
                    else:
                        comps = comp_data or []
                    print(f"  componentData type: {type(comp_data).__name__}, parsed components: {len(comps)}")
                    
                    cvi = d.get('canvasViewInfo')
                    print(f"  canvasViewInfo type: {type(cvi).__name__}, views: {len(cvi) if cvi else 0}")
                    
                    csd = d.get('canvasStyleData')
                    print(f"  canvasStyleData type: {type(csd).__name__}")
                    if isinstance(csd, str):
                        css = json.loads(csd)
                        print(f"  canvasStyleData keys: {sorted(css.keys())}")
                    elif isinstance(csd, dict):
                        print(f"  canvasStyleData keys: {sorted(csd.keys())}")
                    
                    # Save raw response
                    with open(f'd:/Projects/m2/scripts/findById_{name.replace(" ","_")}.json', 'w', encoding='utf-8') as f:
                        json.dump(d, f, indent=2, ensure_ascii=False)
                    print(f"  Saved to findById_{name.replace(' ','_')}.json")
            except Exception as e:
                print(f"Error parsing findById: {e}")
    
    page.on('response', on_response)
    
    # Load tea dashboard
    print("=== Loading Tea Dashboard ===")
    page.goto(f'{base}/#/panel/index?dvId={tea_id}', timeout=60000)
    time.sleep(15)
    
    # Load DSP dashboard  
    print("\n=== Loading DSP Dashboard ===")
    page.goto(f'{base}/#/panel/index?dvId={dsp_id}', timeout=60000)
    time.sleep(15)
    
    browser.close()

# Now compare the saved responses
print("\n\n=== Comparing responses ===")
for name in ['连锁茶饮销售看板', 'DSP_Report']:
    fname = f'd:/Projects/m2/scripts/findById_{name}.json'
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"\n--- {name} ---")
        print(f"  Keys: {sorted(data.keys())}")
        print(f"  type: {data.get('type')}")
        print(f"  nodeType: {data.get('nodeType')}")
        
        comp_data = data.get('componentData', '[]')
        if isinstance(comp_data, str):
            comps = json.loads(comp_data)
        else:
            comps = comp_data or []
        print(f"  componentData is string: {isinstance(comp_data, str)}")
        print(f"  components: {len(comps)}")
        
        cvi = data.get('canvasViewInfo')
        print(f"  canvasViewInfo is dict: {isinstance(cvi, dict)}")
        print(f"  views: {len(cvi) if cvi else 0}")
        
        csd = data.get('canvasStyleData')
        print(f"  canvasStyleData is string: {isinstance(csd, str)}")
    except FileNotFoundError:
        print(f"  File not found: {fname}")
