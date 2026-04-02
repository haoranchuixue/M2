"""Create SQL dataset via DataEase UI - double-click '自定义SQL' to open SQL editor."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'
sql_query = "SELECT * FROM dsp_report WHERE create_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    save_reqs = []
    save_resps = []
    def handle_req(req):
        if 'datasetTree' in req.url and req.method == 'POST':
            save_reqs.append({'url': req.url, 'body': req.post_data})
    def handle_resp(resp):
        if 'datasetTree' in resp.url and resp.status == 200:
            try:
                save_resps.append({'url': resp.url, 'body': resp.json()})
            except:
                pass
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
    
    # Go to dataset form
    page.goto(f'{base}/#/dataset-form?pid=1236043392912330752', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Select starrocks datasource
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
    
    # Find and double-click "自定义SQL"
    sql_el = page.query_selector('text="自定义SQL"')
    if sql_el:
        print("Found '自定义SQL', double-clicking...")
        sql_el.dblclick()
        time.sleep(3)
        page.wait_for_load_state('networkidle', timeout=10000)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_editor.png')
        
        # Check for SQL editor dialog/overlay
        sql_drawer = page.query_selector('.sql-drawer-fullscreen, [class*="sql-drawer"], [class*="code-mirror"], [class*="editor"]')
        if sql_drawer and sql_drawer.is_visible():
            print("SQL editor is visible!")
        
        # Look for a textarea or code editor
        editors = page.query_selector_all('textarea, .CodeMirror, [class*="code-mirror"], .cm-editor, [contenteditable="true"]')
        print(f"Editor elements: {len(editors)}")
        for i, ed in enumerate(editors):
            vis = ed.is_visible()
            cls = ed.get_attribute('class') or ''
            tag = ed.evaluate("el => el.tagName")
            print(f"  [{i}] <{tag}> visible={vis}, class='{cls[:80]}'")
        
        # Check what dialog appeared
        dialogs = page.evaluate("""() => {
            const overlays = document.querySelectorAll('.ed-overlay, .ed-dialog, [class*="drawer"]');
            return Array.from(overlays).filter(o => o.offsetParent !== null || o.style.display !== 'none').map(o => ({
                class: o.className?.substring(0, 200) || '',
                visible: o.offsetParent !== null,
                style_display: o.style.display,
                children_text: o.textContent?.substring(0, 200) || ''
            }));
        }""")
        print(f"\nVisible overlays/dialogs: {len(dialogs)}")
        for d in dialogs:
            print(f"  class='{d['class'][:100]}' visible={d['visible']} display={d['style_display']}")
            print(f"  text: {d['children_text'][:200]}")
        
        # Also look for the CodeMirror element which DataEase uses for SQL editing
        cm = page.query_selector('.CodeMirror, .cm-editor')
        if cm:
            print("\nFound CodeMirror editor!")
            # Type SQL into CodeMirror
            cm.click()
            time.sleep(0.5)
            page.keyboard.type(sql_query)
            time.sleep(1)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_typed.png')
        else:
            # Try finding a textarea
            ta = page.query_selector('textarea:visible')
            if ta:
                print("Found textarea, filling SQL...")
                ta.fill(sql_query)
                time.sleep(1)
            else:
                # Try contenteditable div
                ce = page.query_selector('[contenteditable="true"]:visible')
                if ce:
                    print("Found contenteditable, typing SQL...")
                    ce.click()
                    page.keyboard.type(sql_query)
                    time.sleep(1)
                else:
                    print("No editor found! Looking at full page...")
                    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_no_editor.png')
    else:
        print("'自定义SQL' element not found!")
    
    # Look for "运行" (Run) button
    run_btn = page.query_selector('button:has-text("运行")')
    if run_btn and run_btn.is_visible():
        print("\nClicking '运行' (Run)...")
        run_btn.click()
        time.sleep(10)
        page.wait_for_load_state('networkidle', timeout=30000)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_result.png')
    
    # Look for "确定" (OK/Confirm) button
    ok_btn = page.query_selector('button:has-text("确定"), button:has-text("确认")')
    if ok_btn and ok_btn.is_visible():
        print("Clicking '确定'...")
        ok_btn.click()
        time.sleep(3)
    
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_after_ok.png')
    
    # Rename the dataset
    name_el = page.query_selector('.dataset-name')
    if name_el:
        name_el.click()
        time.sleep(1)
        name_input = page.query_selector('input.dataset-name, .dataset-name input')
        if name_input:
            name_input.fill('DSP Report (Filtered)')
            time.sleep(0.5)
    
    # Save the dataset
    save_btn = page.query_selector('button:has-text("保存并返回")')
    if save_btn and save_btn.is_visible():
        print("\nClicking '保存并返回'...")
        save_btn.click()
        time.sleep(5)
        page.wait_for_load_state('networkidle', timeout=15000)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_saved.png')
        print("Saved!")
    
    # Check captured API calls
    print(f"\nCaptured {len(save_reqs)} save requests")
    for sr in save_reqs:
        print(f"  URL: {sr['url']}")
        if sr['body']:
            body = json.loads(sr['body'])
            print(f"  Name: {body.get('name', 'N/A')}")
            info = body.get('info', '')
            if isinstance(info, str):
                try:
                    info_obj = json.loads(info)
                    if isinstance(info_obj, list) and len(info_obj) > 0:
                        ds = info_obj[0].get('currentDs', {})
                        print(f"  DS type: {ds.get('type')}")
                        ds_info = ds.get('info', '')
                        if isinstance(ds_info, str):
                            try:
                                ds_info_obj = json.loads(ds_info)
                                print(f"  SQL: {ds_info_obj.get('sql', '')[:200]}")
                            except:
                                pass
                except:
                    pass
    
    print(f"\nCaptured {len(save_resps)} save responses")
    for sr in save_resps:
        print(f"  URL: {sr['url']}")
        body = sr['body']
        print(f"  Code: {body.get('code')}, Data: {str(body.get('data', ''))[:200]}")
    
    browser.close()
    print("\nDone!")
