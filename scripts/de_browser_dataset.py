"""
Use browser automation to open the new dataset in DataEase UI,
which should properly initialize the Calcite schema.
Then test the chart data.
"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests, time

base = 'http://47.236.78.123:8100'
NEW_DS_ID = '1236797659440877568'

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1600, 'height': 900})

    page.goto(f'{base}/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_load_state('networkidle', timeout=30000)
    page.wait_for_selector('input', timeout=10000)
    inputs = page.query_selector_all('input')
    inputs[0].fill('admin')
    inputs[1].fill('DataEase@123456')
    page.query_selector('button').click()
    time.sleep(5)
    page.wait_for_load_state('networkidle', timeout=30000)

    # Get token for API calls
    token_raw = page.evaluate("() => localStorage.getItem('user.token')")
    token_obj = json.loads(token_raw)
    jwt = json.loads(token_obj['v'])

    # Navigate to datasets
    page.goto(f'{base}/#/dataset/index', timeout=60000, wait_until='domcontentloaded')
    time.sleep(5)
    page.screenshot(path=r'd:\Projects\m2\scripts\ss_dataset_list.png')
    print('At dataset list')

    # Click on DSP Report folder
    dsp_folder = page.query_selector('text="DSP Report"')
    if dsp_folder:
        dsp_folder.click()
        time.sleep(2)

    # Click on DSP_Report_v2
    v2 = page.query_selector('text="DSP_Report_v2"')
    if v2:
        v2.click()
        time.sleep(5)
        page.screenshot(path=r'd:\Projects\m2\scripts\ss_dataset_v2.png')
        print('Opened DSP_Report_v2')

        # Wait for data preview
        time.sleep(10)
        page.screenshot(path=r'd:\Projects\m2\scripts\ss_dataset_preview.png')
        print('After waiting for preview')

        body = page.inner_text('body')
        if 'SQL ERROR' in body:
            idx = body.index('SQL ERROR')
            print(f'SQL ERROR: {body[idx:idx+200]}')
        elif 'Error' in body:
            idx = body.index('Error')
            print(f'Error: {body[max(0,idx-20):idx+200]}')

        # Check for table data
        tds = page.query_selector_all('td')
        if tds and len(tds) > 2:
            print(f'Table cells: {len(tds)}')
            for td in tds[:8]:
                print(f'  {td.text_content()[:50]}')
    else:
        print('DSP_Report_v2 not found')
        # List visible items
        all_text = page.inner_text('body')
        if 'DSP_Report' in all_text:
            print('Found DSP_Report text')
        elif 'DSP Report' in all_text:
            print('Found DSP Report text')

    page.screenshot(path=r'd:\Projects\m2\scripts\ss_dataset_final.png')

    # Now try API with token from browser session
    headers = {'x-de-token': jwt, 'Content-Type': 'application/json'}

    # Try fetching data preview
    r2 = requests.post(
        f'{base}/de2api/datasetData/previewData',
        headers=headers,
        json={'id': NEW_DS_ID},
        timeout=120,
    )
    print(f'\npreviewData: {r2.status_code} {r2.text[:500]}')

    browser.close()
    print('Done')
