"""Find the correct edit URL for a dashboard by clicking the edit icon."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import json
import time

base = 'http://47.236.78.123:8100'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    
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
    
    # Navigate to dashboard page
    page.click('text="仪表板"')
    time.sleep(3)
    page.wait_for_load_state('networkidle', timeout=15000)
    
    # Find all <a> elements or clickable elements on the page
    # Hover over DSP Report to see the edit icon
    dsp = page.locator('.tree-node-name:has-text("DSP Report"), .node-name:has-text("DSP Report")').first
    try:
        dsp.hover()
        time.sleep(1)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_hover_01.png')
        print("Hovered over DSP Report")
    except:
        print("Failed to hover with tree-node-name selector, trying generic")
    
    # Try to find the item another way
    # From the screenshot, the tree structure has icons appearing on hover
    all_items = page.query_selector_all('[class*="tree"] [class*="node"]')
    print(f"\nTree nodes: {len(all_items)}")
    for item in all_items[:20]:
        txt = item.inner_text()[:40].strip()
        cls = item.get_attribute('class') or ''
        print(f"  class='{cls[:60]}', text='{txt}'")
    
    # Try another selector - from the previous screenshot, DSP Report shows as selected with icons
    # Let me try to hover over the DSP Report text directly
    dsp2 = page.locator('text="DSP Report"').first
    bbox = dsp2.bounding_box()
    print(f"\nDSP Report bbox: {bbox}")
    
    if bbox:
        # Hover slightly to the right of the text (where the edit icon should be)
        page.mouse.move(bbox['x'] + bbox['width'] + 20, bbox['y'] + bbox['height'] / 2)
        time.sleep(1)
        page.screenshot(path='d:\\Projects\\m2\\scripts\\dash_hover_02.png')
    
    # Find all elements that could be the edit button
    # Look for <svg>, <i>, or elements with edit-related classes
    svgs = page.query_selector_all('svg')
    print(f"\nSVG elements: {len(svgs)}")
    
    # Look for link-like elements with edit/编辑
    links = page.query_selector_all('a[href*="edit"], a[href*="dvCanvas"]')
    print(f"Edit links: {len(links)}")
    for l in links:
        href = l.get_attribute('href')
        print(f"  href={href}")
    
    # Try to capture navigation when clicking the edit icon
    # First, let me look at the HTML structure around DSP Report
    html = page.evaluate("""() => {
        const el = document.querySelector('.tree-list') || document.querySelector('[class*="aside"]');
        if (el) return el.innerHTML.substring(0, 3000);
        return document.body.innerHTML.substring(0, 3000);
    }""")
    print(f"\nHTML around sidebar: {html[:2000]}")
    
    browser.close()

print("Done.")
