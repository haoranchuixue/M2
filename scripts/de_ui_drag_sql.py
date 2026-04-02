"""Create SQL dataset via DataEase UI - drag '自定义SQL' to center area."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
    save_reqs = []
    save_resps = []
    def handle_req(req):
        if 'datasetTree/save' in req.url and req.method == 'POST':
            save_reqs.append({'url': req.url, 'body': req.post_data})
    def handle_resp(resp):
        if 'datasetTree/save' in resp.url:
            try:
                save_resps.append({'url': resp.url, 'status': resp.status, 'body': resp.json()})
            except:
                save_resps.append({'url': resp.url, 'status': resp.status, 'body': None})
    page.on('request', handle_req)
    page.on('response', handle_resp)
    
    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)
    print("Logged in")
    
    page.goto(f'{base}/#/dataset-form?pid=1236043392912330752', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Select starrocks
    ds_select = page.query_selector('.ed-select:has-text("请选择数据源")')
    if ds_select:
        ds_select.click()
        time.sleep(2)
        sr = page.query_selector('.ed-select-dropdown__item:has-text("starrocks")')
        if sr:
            sr.click()
            time.sleep(3)
            page.wait_for_load_state('networkidle', timeout=10000)
    print("Selected starrocks")
    
    # Get center area coordinates
    center_area = page.query_selector('.dataset-db, .container')
    if center_area:
        center_box = center_area.bounding_box()
        target_x = center_box['x'] + center_box['width'] / 2
        target_y = center_box['y'] + center_box['height'] / 2
        print(f"Center area: ({target_x:.0f}, {target_y:.0f})")
    else:
        target_x = 800
        target_y = 400
    
    # Find "自定义SQL" element
    sql_el = page.query_selector('text="自定义SQL"')
    if sql_el:
        sql_box = sql_el.bounding_box()
        source_x = sql_box['x'] + sql_box['width'] / 2
        source_y = sql_box['y'] + sql_box['height'] / 2
        print(f"SQL element: ({source_x:.0f}, {source_y:.0f})")
        
        # Try drag and drop
        print("Dragging '自定义SQL' to center...")
        page.mouse.move(source_x, source_y)
        page.mouse.down()
        time.sleep(0.5)
        
        # Move slowly to center
        steps = 10
        for i in range(steps + 1):
            x = source_x + (target_x - source_x) * i / steps
            y = source_y + (target_y - source_y) * i / steps
            page.mouse.move(x, y)
            time.sleep(0.05)
        
        time.sleep(0.5)
        page.mouse.up()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)
        
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_drag_result.png')
        
        # Check if SQL editor appeared
        # Look for CodeMirror, textarea, or any visible drawer/dialog
        cm = page.query_selector('.CodeMirror:visible, .cm-editor:visible')
        ta = page.query_selector('textarea:visible')
        drawer = page.query_selector('.ed-drawer:visible, .sql-drawer-fullscreen:visible')
        
        if cm:
            print("CodeMirror editor found!")
            cm.click()
            page.keyboard.type(sql_query, delay=10)
        elif ta:
            print("Textarea found!")
            ta.fill(sql_query)
        elif drawer:
            print("Drawer found!")
            # Look inside the drawer for editor
            editors = drawer.query_selector_all('textarea, .CodeMirror, .cm-editor, [contenteditable]')
            print(f"  Editors in drawer: {len(editors)}")
        else:
            print("No SQL editor visible after drag")
            
            # Check if we need a different approach - maybe the drag added a SQL node
            # and we need to click on it to open the editor
            sql_nodes = page.query_selector_all('[class*="sql-node"], [class*="SqlNode"]')
            print(f"SQL nodes: {len(sql_nodes)}")
            
            # Check what's in the center area now
            center_text = page.evaluate("""() => {
                const center = document.querySelector('.container.dataset-db');
                return center ? center.innerText.substring(0, 500) : 'no center';
            }""")
            print(f"Center area text: {center_text[:300]}")
    
    browser.close()
    print("\nDone!")
