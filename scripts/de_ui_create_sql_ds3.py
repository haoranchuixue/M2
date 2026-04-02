"""Create SQL-type dataset via DataEase UI - navigate to dataset page properly."""
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
    
    # Capture all API calls
    api_calls = []
    def handle_response(response):
        url = response.url
        if '/de2api/' in url:
            api_calls.append({'url': url, 'status': response.status})
    page.on('response', handle_response)
    
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
    
    # Navigate directly to dataset page
    page.goto(f'{base}/#/data/dataset', timeout=30000, wait_until='domcontentloaded')
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    print(f"URL: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds3_page.png')
    
    # Find tree structure
    tree_html = page.evaluate("""() => {
        // Get all elements that could be tree nodes
        const nodes = document.querySelectorAll('[class*="tree-node"], [class*="custom-tree"]');
        let result = [];
        nodes.forEach((n, i) => {
            if (i < 20) {
                result.push(n.outerHTML.substring(0, 300));
            }
        });
        return result.join('\\n---\\n');
    }""")
    print(f"\nTree nodes:\n{tree_html[:3000]}")
    
    # Find DSP Report in the tree
    dsp_els = page.query_selector_all('span:has-text("DSP Report")')
    print(f"\nDSP Report elements: {len(dsp_els)}")
    
    if dsp_els:
        # Hover over the DSP Report group to reveal action icons
        dsp_el = dsp_els[0]
        dsp_el.hover()
        time.sleep(1)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds3_hover.png')
        
        # Check for icons that appear on hover
        hover_icons = page.query_selector_all('.ed-icon.hover-icon, [class*="hover-icon"]')
        print(f"Hover icons: {len(hover_icons)}")
        
        # Also check for tree node action buttons
        more_icons = page.query_selector_all('[class*="icon-more"], [class*="more"]')
        print(f"More icons: {len(more_icons)}")
        for i, mi in enumerate(more_icons[:5]):
            cls = mi.get_attribute('class') or ''
            vis = mi.is_visible()
            if vis:
                print(f"  [{i}] visible, class='{cls[:100]}'")
        
        # Try clicking the "more" or "+" icon near DSP Report
        # First find the tree-node container for DSP Report
        node_container = page.evaluate("""(el) => {
            let node = el.closest('[class*="tree-node"], [class*="folder"]');
            return node ? node.outerHTML.substring(0, 1000) : 'no container';
        }""", dsp_el)
        print(f"\nNode container:\n{node_container}")
        
        # Look for add/create icons within or near the container
        add_icons = page.evaluate("""(el) => {
            let container = el.closest('[class*="tree-node"], [class*="folder"]') || el.parentElement;
            let icons = container.querySelectorAll('[class*="icon"]');
            return Array.from(icons).map(i => ({
                class: i.className,
                tag: i.tagName,
                visible: i.offsetParent !== null,
                text: i.textContent?.substring(0, 30) || ''
            }));
        }""", dsp_el)
        print(f"\nIcons in container: {len(add_icons)}")
        for ic in add_icons:
            print(f"  <{ic['tag']}> class='{ic['class'][:80]}' visible={ic['visible']} text='{ic['text']}'")
    
    # Try direct URL for creating a new dataset
    # In DataEase, creating a SQL dataset might be at a specific URL
    page.goto(f'{base}/#/data/dataset/new', timeout=15000, wait_until='domcontentloaded')
    time.sleep(3)
    print(f"\nAfter /new URL: {page.url}")
    page.screenshot(path='d:\\Projects\\m2\\scripts\\ui_ds3_new.png')
    
    browser.close()
    print("\nDone!")
