"""Test table-info (detail table) with proper customAttr - should generate SELECT LIMIT without GROUP BY."""
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

def make_xaxis_field(f, name):
    return {
        'id': f['id'], 'datasourceId': f.get('datasourceId'),
        'datasetTableId': f.get('datasetTableId'), 'datasetGroupId': str(DS_ID),
        'originName': f['originName'], 'name': name,
        'dataeaseName': f.get('dataeaseName'), 'fieldShortName': f.get('fieldShortName'),
        'groupType': f.get('groupType', 'd'), 'type': f['type'], 'deType': f.get('deType', 0),
        'deExtractType': f.get('deExtractType', 0), 'extField': 0,
        'checked': True, 'chartType': 'table-info', 'sort': 'none',
        'filter': [], 'hide': False, 'agg': False,
    }

chart_view = {
    'id': str(int(time.time() * 1000)),
    'title': 'test',
    'sceneId': '0', 'tableId': str(DS_ID),
    'type': 'table-info', 'render': 'antv',
    'resultCount': 5, 'resultMode': 'custom',
    'xAxis': [
        make_xaxis_field(date_field, 'Date'),
        make_xaxis_field(req_field, 'Request'),
    ],
    'xAxisExt': [], 'yAxis': [], 'yAxisExt': [],
    'extStack': [], 'extBubble': [], 'extLabel': [], 'extTooltip': [],
    'extColor': [], 'sortPriority': [],
    'customAttr': {
        'basicStyle': {'tableBorderColor': '#E6E7E4', 'tableColumnMode': 'adapt',
                       'tablePageMode': 'pull', 'tablePageSize': 20, 'tableLayoutMode': 'grid',
                       'mapStyle': 'normal', 'areaBorderColor': '#303133', 'suspension': True,
                       'showZoom': True, 'alpha': 100, 'areaBaseColor': '#ffffff'},
        'tableHeader': {'tableHeaderAlign': 'left', 'tableHeaderBgColor': '#F5F6F7',
                        'tableHeaderFontColor': '#333333', 'tableTitleFontSize': 12,
                        'tableTitleHeight': 36, 'tableHeaderSort': True, 'showIndex': False,
                        'indexLabel': '序号'},
        'tableCell': {'tableFontColor': '#333333', 'tableItemAlign': 'left',
                      'tableItemBgColor': '#ffffff', 'tableItemFontSize': 12,
                      'tableItemHeight': 36, 'enableTableCrossBG': True, 'tableItemSubBgColor': '#F8F8F9'},
        'misc': {'showName': True, 'mapPitch': 0, 'nameFontColor': '#333333',
                 'nameFontSize': 18, 'nameFontWeight': 'normal'},
        'label': {'show': False}, 'tooltip': {'show': True},
    },
    'customStyle': {'text': {'show': True, 'fontSize': '14', 'isBolder': True, 'color': '#333333'}},
    'customFilter': {},
    'drillFields': [],
    'senior': {'functionCfg': {'sliderShow': False, 'emptyDataStrategy': 'breakLine'},
               'scrollCfg': {'open': False, 'row': 1, 'interval': 2000}},
    'dataFrom': 'dataset', 'datasetMode': 0,
    'drill': False,
}

print(f'Testing table-info with {len(chart_view["xAxis"])} xAxis fields, resultCount=5')
try:
    t0 = time.time()
    r2 = requests.post(f'{base}/de2api/chartData/getData', headers=headers, json=chart_view, timeout=120)
    t1 = time.time()
    print(f'Time: {t1-t0:.1f}s  Status: {r2.status_code}')
    resp = r2.json()
    print(f'Code: {resp.get("code")}')
    if resp.get('code') == 0:
        data = resp.get('data') or {}
        rows = data.get('tableRow', [])
        flds = data.get('fields', [])
        print(f'Rows: {len(rows)}  Fields: {len(flds)}')
        for row in rows[:3]:
            print(f'  {json.dumps(row, ensure_ascii=False)[:300]}')
    else:
        print(f'Msg: {str(resp.get("msg",""))[:500]}')
except requests.exceptions.ReadTimeout:
    print(f'TIMEOUT after 120s')
except Exception as e:
    print(f'Exception: {type(e).__name__}: {str(e)[:200]}')

# Also try to see if there's an API to get the generated SQL
print('\n=== Trying to get generated SQL ===')
for endpoint in ['chartData/previewSql', 'chartData/getPreviewSql', 'chart/getPreviewSql']:
    try:
        r3 = requests.post(f'{base}/de2api/{endpoint}', headers=headers, json=chart_view, timeout=10)
        print(f'{endpoint}: status={r3.status_code}')
        if r3.status_code == 200:
            body = r3.json()
            print(f'  code={body.get("code")}')
            if body.get('data'):
                print(f'  data: {str(body["data"])[:500]}')
    except Exception as e:
        print(f'{endpoint}: {type(e).__name__}')

print('\nDone')
