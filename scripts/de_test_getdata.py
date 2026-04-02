"""Test getData API with different date filters to find a date with data."""
import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests

base = 'http://47.236.78.123:8100'
DS_ID = '1236046190513098752'

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

r = requests.post(f'{base}/de2api/datasetTree/details/{DS_ID}', headers=headers, json={}, timeout=30)
fields = r.json()['data']['allFields']
field_map = {f['originName']: f for f in fields}
date_field = field_map['create_date']
req_field = field_map['request_count']

print(f"date_field id: {date_field['id']}, deType: {date_field.get('deType')}")
print(f"req_field id: {req_field['id']}, deType: {req_field.get('deType')}")

# Try table-info (detail) with a single column and filter to check data existence
test_dates = ['2026-03-31', '2026-03-30', '2026-03-29', '2026-03-28', '2026-03-25']

for test_date in test_dates:
    chart_view = {
        'id': str(int(time.time() * 1000)),
        'title': 'test',
        'sceneId': '0', 'tableId': str(DS_ID),
        'type': 'table-info', 'render': 'antv',
        'resultCount': 5, 'resultMode': 'custom',
        'xAxis': [{
            'id': date_field['id'], 'datasourceId': date_field.get('datasourceId'),
            'datasetTableId': date_field.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
            'originName': date_field['originName'], 'name': 'Date',
            'dataeaseName': date_field.get('dataeaseName'), 'fieldShortName': date_field.get('fieldShortName'),
            'groupType': 'd', 'type': date_field['type'], 'deType': date_field.get('deType', 0),
            'deExtractType': date_field.get('deExtractType', 0), 'extField': 0,
            'checked': True, 'chartType': 'table-info', 'sort': 'none',
            'filter': [{
                'fieldId': date_field['id'],
                'term': 'eq',
                'value': test_date,
            }],
            'hide': False, 'agg': False,
        }],
        'xAxisExt': [], 'yAxis': [], 'yAxisExt': [],
        'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
        'extColor': [], 'sortPriority': [],
        'customAttr': {},
        'customStyle': {},
        'customFilter': {},
        'drillFields': [],
        'senior': {'functionCfg': {'sliderShow': False}, 'scrollCfg': {'open': False}},
        'dataFrom': 'dataset', 'datasetMode': 0,
    }

    print(f'\nTesting date={test_date} ...')
    try:
        r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=120)
        resp = r2.json()
        if resp.get('code') == 0:
            data = resp.get('data') or {}
            rows = data.get('tableRow', [])
            flds = data.get('fields', [])
            print(f'  OK! Rows: {len(rows)}  Fields: {len(flds)}')
            if rows:
                print(f'  Sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
        else:
            print(f'  Error: {str(resp.get("msg",""))[:200]}')
    except Exception as e:
        print(f'  Exception: {type(e).__name__}: {str(e)[:200]}')

print('\nDone')
