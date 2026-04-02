"""Create SQL dataset via DataEase UI - try HTML5 drag events and alternative approaches."""
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
    def handle_req(req):
        if 'datasetTree/save' in req.url and req.method == 'POST':
            save_reqs.append({'url': req.url, 'body': req.post_data})
    page.on('request', handle_req)
    
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
    
    # Use Playwright's drag_to method
    sql_el = page.query_selector('text="自定义SQL"')
    
    # Find the drop target - the placeholder area in the center
    drop_area = page.query_selector('.dataset-db .sql-result, .dataset-db .ed-empty, [class*="drag-area"]')
    if not drop_area:
        # Try the center placeholder image/text
        drop_area = page.evaluate("""() => {
            const els = document.querySelectorAll('p, div');
            for (const el of els) {
                if (el.textContent?.includes('拖拽到这里创建数据集') && el.offsetParent) {
                    return true;
                }
            }
            return false;
        }""")
        drop_target = page.query_selector('text="拖拽到这里创建数据集"')
    else:
        drop_target = drop_area
    
    if sql_el and drop_target:
        print("Attempting Playwright drag_to...")
        try:
            sql_el.drag_to(drop_target, timeout=10000)
            time.sleep(3)
            page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_drag2_result.png')
        except Exception as e:
            print(f"drag_to failed: {e}")
    
    # Alternative: Use JavaScript to simulate HTML5 drag events
    print("\nTrying JS drag simulation...")
    result = page.evaluate("""() => {
        const source = document.querySelector('[class*="tree-node"][data-key]');
        // Find the SQL custom node - it's the first tree node
        const treeNodes = document.querySelectorAll('.ed-tree-node');
        let sqlNode = null;
        for (const node of treeNodes) {
            if (node.textContent?.includes('自定义SQL')) {
                sqlNode = node;
                break;
            }
        }
        
        if (!sqlNode) return 'SQL node not found';
        
        const target = document.querySelector('.dataset-db');
        if (!target) return 'Drop target not found';
        
        // Create and dispatch drag events
        const dataTransfer = new DataTransfer();
        dataTransfer.setData('text/plain', 'sql');
        
        const dragstart = new DragEvent('dragstart', {
            bubbles: true, cancelable: true, dataTransfer
        });
        sqlNode.dispatchEvent(dragstart);
        
        const dragenter = new DragEvent('dragenter', {
            bubbles: true, cancelable: true, dataTransfer
        });
        target.dispatchEvent(dragenter);
        
        const dragover = new DragEvent('dragover', {
            bubbles: true, cancelable: true, dataTransfer
        });
        target.dispatchEvent(dragover);
        
        const drop = new DragEvent('drop', {
            bubbles: true, cancelable: true, dataTransfer
        });
        target.dispatchEvent(drop);
        
        const dragend = new DragEvent('dragend', {
            bubbles: true, cancelable: true, dataTransfer
        });
        sqlNode.dispatchEvent(dragend);
        
        return 'Events dispatched';
    }""")
    print(f"JS drag result: {result}")
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=10000)
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_sql_drag2_js.png')
    
    # Check if anything changed
    center_text = page.evaluate("() => document.querySelector('.dataset-db')?.innerText?.substring(0, 300) || 'no center'")
    print(f"Center after JS drag: {center_text[:200]}")
    
    # Alternative approach: Use the Vue event bus or direct component method
    # In DataEase Vue app, the dataset form likely has a method like addTable() or addSql()
    # Let's try to call it directly via Vue devtools
    print("\nTrying Vue component approach...")
    vue_result = page.evaluate("""() => {
        // Try to access Vue component instance
        const app = document.querySelector('.de-dataset-form');
        if (!app) return 'no app';
        const vueInstance = app.__vue_app__ || app.__vue__ || app._vnode;
        if (!vueInstance) return 'no vue instance';
        return 'found vue: ' + typeof vueInstance;
    }""")
    print(f"Vue result: {vue_result}")
    
    # Try accessing through __vueParentComponent
    vue_result2 = page.evaluate("""() => {
        const el = document.querySelector('[data-v-251c3cbc]');
        if (!el) return 'no element';
        const vm = el.__vueParentComponent;
        if (!vm) return 'no vm';
        const ctx = vm.ctx;
        if (!ctx) return 'no ctx';
        const methods = Object.keys(ctx).filter(k => typeof ctx[k] === 'function');
        return 'methods: ' + methods.join(', ');
    }""")
    print(f"Vue methods: {vue_result2}")
    
    browser.close()
    print("\nDone!")
