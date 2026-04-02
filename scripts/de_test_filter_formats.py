"""Test different customFilter formats to find one that DataEase accepts."""
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

def make_chart(custom_filter):
    return {
        'id': str(int(time.time() * 1000)),
        'title': 'test',
        'sceneId': '0', 'tableId': str(DS_ID),
        'type': 'table-normal', 'render': 'antv',
        'resultCount': 5, 'resultMode': 'custom',
        'xAxis': [{
            'id': date_field['id'], 'datasourceId': date_field.get('datasourceId'),
            'datasetTableId': date_field.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
            'originName': date_field['originName'], 'name': 'Date',
            'dataeaseName': date_field.get('dataeaseName'), 'fieldShortName': date_field.get('fieldShortName'),
            'groupType': 'd', 'type': date_field['type'], 'deType': date_field.get('deType', 0),
            'deExtractType': date_field.get('deExtractType', 0), 'extField': 0,
            'checked': True, 'chartType': 'table-normal', 'sort': 'none',
            'filter': [], 'hide': False, 'agg': False,
        }],
        'xAxisExt': [],
        'yAxis': [{
            'id': req_field['id'], 'datasourceId': req_field.get('datasourceId'),
            'datasetTableId': req_field.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
            'originName': req_field['originName'], 'name': 'Request',
            'dataeaseName': req_field.get('dataeaseName'), 'fieldShortName': req_field.get('fieldShortName'),
            'groupType': 'q', 'type': req_field['type'], 'deType': req_field.get('deType', 0),
            'deExtractType': req_field.get('deExtractType', 0), 'extField': 0,
            'checked': True, 'chartType': 'table-normal', 'sort': 'none',
            'summary': 'sum', 'filter': [], 'hide': False, 'agg': False,
        }],
        'yAxisExt': [],
        'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
        'extColor': [], 'sortPriority': [],
        'customAttr': {
            'basicStyle': {'tableBorderColor': '#E6E7E4', 'tableColumnMode': 'adapt',
                           'tablePageMode': 'pull', 'tablePageSize': 20, 'tableLayoutMode': 'grid'},
            'tableHeader': {'tableHeaderAlign': 'left', 'tableHeaderBgColor': '#F5F6F7',
                            'tableHeaderFontColor': '#333333', 'tableTitleFontSize': 12,
                            'tableTitleHeight': 36, 'tableHeaderSort': True},
            'tableCell': {'tableFontColor': '#333333', 'tableItemAlign': 'left',
                          'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
                          'tableItemHeight': 36, 'enableTableCrossBG': True, 'tableItemSubBgColor': '#F8F8F9'},
            'misc': {'showName': True}, 'label': {'show': False}, 'tooltip': {'show': True},
        },
        'customStyle': {'text': {'show': True, 'fontSize': '14', 'isBolder': True, 'color': '#333333'}},
        'customFilter': custom_filter,
        'drillFields': [],
        'senior': {'functionCfg': {'sliderShow': False}, 'scrollCfg': {'open': False}},
        'dataFrom': 'dataset', 'datasetMode': 0,
        'drill': False,
    }

filter_formats = {
    'format1_logic_items': {
        'logic': 'and',
        'items': [{
            'fieldId': date_field['id'],
            'filterType': 0,
            'term': 'eq',
            'value': '2026-03-31',
        }]
    },
    'format2_field_filter': {
        'logic': 'and',
        'items': [{
            'fieldId': date_field['id'],
            'filterType': 1,
            'term': 'between',
            'value': ['2026-03-31 00:00:00', '2026-03-31 23:59:59'],
        }]
    },
    'format3_component_style': {
        'filter_001': {
            'componentId': 'filter_001',
            'fieldId': date_field['id'],
            'operator': 'between',
            'value': ['2026-03-31', '2026-03-31'],
            'isTree': False,
        }
    },
    'format4_items_with_field_obj': {
        'logic': 'and',
        'items': [{
            'fieldId': date_field['id'],
            'field': {
                'id': date_field['id'],
                'originName': 'create_date',
                'name': 'Date',
                'deType': 1,
                'groupType': 'd',
                'datasetGroupId': str(DS_ID),
            },
            'filterType': 0,
            'term': 'eq',
            'value': '2026-03-31',
        }]
    },
    'format5_empty_filter_with_xaxis_filter': 'SPECIAL',
}

for name, cf in filter_formats.items():
    print(f'\n=== Testing {name} ===')
    if cf == 'SPECIAL':
        chart = make_chart({})
        chart['xAxis'][0]['filter'] = [{
            'fieldId': date_field['id'],
            'term': 'eq',
            'value': '2026-03-31',
        }]
    else:
        chart = make_chart(cf)
    
    try:
        t0 = time.time()
        r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart, timeout=60)
        t1 = time.time()
        print(f'  Time: {t1-t0:.1f}s  Status: {r2.status_code}')
        resp = r2.json()
        print(f'  Code: {resp.get("code")}')
        if resp.get('code') == 0:
            data = resp.get('data') or {}
            rows = data.get('tableRow', [])
            flds = data.get('fields', [])
            print(f'  Rows: {len(rows)}  Fields: {len(flds)}')
            if rows:
                print(f'  Sample: {json.dumps(rows[0], ensure_ascii=False)[:300]}')
        else:
            print(f'  Msg: {str(resp.get("msg",""))[:300]}')
    except requests.exceptions.ReadTimeout:
        print(f'  TIMEOUT after 60s (no filter effect)')
    except Exception as e:
        print(f'  Exception: {type(e).__name__}: {str(e)[:200]}')

print('\nDone')
