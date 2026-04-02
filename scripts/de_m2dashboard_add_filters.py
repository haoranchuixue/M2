"""
Add Time Range label + Source dropdown to ReportCenter DSP dashboard (gray DataEase).

Dashboard: ReportCenter - DSP Report (panel id in PANEL_ID).
- Renames date filter title to "Time Range" (YYYY-MM-DD range, existing behavior).
- Adds a second query component: text dropdown on dataset field `country`, titled "Source".
  (ReportCenter reference uses "Source"; dataset has no `source` column — use `country` or
  rebind in DataEase UI to e.g. first_ssp when that field is in the dataset.)

Run: python de_m2dashboard_add_filters.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.sync_api import sync_playwright
import requests
import json
import time
import copy

base = 'http://47.236.78.123:8100'
PANEL_ID = '1236081407923720192'
DATASET_GROUP_ID = '1236079082777743360'
# From canvas chart xAxis (de_dump_country_field.py); change to another dimension if needed.
SOURCE_FIELD = {
    'id': '1774870683869',
    'originName': 'country',
    'name': 'Country',
    'deType': 0,
    'type': 'VARCHAR',
}


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


def build_source_condition():
    cid = str(int(time.time() * 1000) + 7)
    fid = SOURCE_FIELD['id']
    ds = DATASET_GROUP_ID
    return {
        'id': cid,
        'name': 'Source',
        'showError': True,
        'timeGranularity': 'date',
        'timeGranularityMultiple': 'datetimerange',
        'field': {
            'id': fid,
            'type': SOURCE_FIELD['type'],
            'name': SOURCE_FIELD['name'],
            'deType': SOURCE_FIELD['deType'],
        },
        'displayId': fid,
        'sortId': '',
        'sort': 'asc',
        'defaultMapValue': [],
        'mapValue': [],
        'conditionType': 0,
        'conditionValueOperatorF': 'eq',
        'conditionValueF': '',
        'conditionValueOperatorS': 'like',
        'conditionValueS': '',
        'defaultConditionValueOperatorF': 'eq',
        'defaultConditionValueF': '',
        'defaultConditionValueOperatorS': 'like',
        'defaultConditionValueS': '',
        'timeType': 'fixed',
        'relativeToCurrent': 'custom',
        'required': False,
        'timeNum': 0,
        'relativeToCurrentType': 'date',
        'around': 'f',
        'parametersStart': None,
        'parametersEnd': None,
        'arbitraryTime': None,
        'timeNumRange': 0,
        'relativeToCurrentTypeRange': 'date',
        'aroundRange': 'f',
        'arbitraryTimeRange': None,
        'auto': False,
        'defaultValue': '',
        'selectValue': '',
        'optionValueSource': 0,
        'valueSource': [],
        'dataset': {'id': ds, 'name': '', 'fields': []},
        'visible': True,
        'defaultValueCheck': False,
        'multiple': False,
        'displayType': '0',
        'checkedFields': [ds],
        'parameters': [],
        'parametersCheck': False,
        'parametersList': [],
        'checkedFieldsMap': {
            ds: [{
                'datasetId': ds,
                'id': fid,
                'originName': SOURCE_FIELD['originName'],
                'name': SOURCE_FIELD['name'],
                'deType': SOURCE_FIELD['deType'],
                'groupType': 'd',
                'checked': True,
            },
            ],
        },
    }


def main():
    token = get_fresh_token()
    headers = {'x-de-token': token, 'Content-Type': 'application/json'}

    r = requests.post(
        f'{base}/de2api/dataVisualization/findById',
        headers=headers,
        json={'id': PANEL_ID, 'busiFlag': 'dataV', 'resourceTable': 'snapshot'},
        timeout=30,
    )
    dv = r.json().get('data') or {}
    cur_version = dv.get('version') or 1
    cvi = copy.deepcopy(dv.get('canvasViewInfo') or {})
    comps = dv.get('componentData', '[]')
    if isinstance(comps, str):
        comps = json.loads(comps)
    old_canvas = dv.get('canvasStyleData', '{}')
    if isinstance(old_canvas, str):
        old_canvas = json.loads(old_canvas)

    print(f'Version {cur_version}, components: {len(comps)}')

    date_q = None
    chart_c = None
    for c in comps:
        if c.get('component') == 'VQuery':
            date_q = c
        elif c.get('component') == 'UserView':
            chart_c = c

    if not date_q:
        print('ERROR: No VQuery found')
        return
    pv = date_q.get('propValue')
    if isinstance(pv, dict):
        pv['title'] = 'Time Range'
        date_q['name'] = 'Time Range'
        date_q['label'] = 'Time Range'
    elif isinstance(pv, list):
        for row in pv:
            if row.get('displayType') in ('7', '1') or row.get('timeGranularityMultiple'):
                row['name'] = 'Time Range'

    source_id = str(int(time.time() * 1000) + 3)
    source_comp = {
        'animations': [],
        'canvasId': date_q.get('canvasId') or 'canvas-main',
        'events': {},
        'groupStyle': {},
        'isLock': False,
        'isShow': True,
        'collapseName': ['position', 'background', 'style'],
        'linkage': {'duration': 0},
        'component': 'VQuery',
        'name': 'Source',
        'label': 'Source',
        'propValue': [build_source_condition()],
        'icon': '',
        'innerType': 'VQuery',
        'editing': False,
        'x': 20,
        'y': date_q.get('y', 1),
        'sizeX': 18,
        'sizeY': date_q.get('sizeY', 2),
        'style': {
            'rotate': 0,
            'opacity': 1,
            'width': 400,
            'height': 50,
            'left': 420,
            'top': date_q.get('style', {}).get('top', 10),
        },
        'matrixStyle': {},
        'commonBackground': copy.deepcopy(date_q.get('commonBackground', {})),
        'state': 'ready',
        'render': 'custom',
        'id': source_id,
        '_dragId': 0,
        'show': True,
        'mobileSelected': False,
        'mobileStyle': {'style': {'width': 375, 'height': 50, 'left': 0, 'top': 0}},
        'sourceViewId': None,
        'linkageFilters': [],
        'canvasActive': False,
        'maintainRadio': False,
        'aspectRatio': 1,
        'actionSelection': {'linkageActive': 'custom'},
    }

    # Layout: Time Range left, Source right; chart below
    if chart_c:
        chart_c['y'] = max(chart_c.get('y', 3), 4)

    new_comps = [date_q, source_comp]
    if chart_c:
        new_comps.append(chart_c)
    for c in comps:
        if c.get('component') not in ('VQuery', 'UserView'):
            new_comps.append(c)

    compact_comp = json.dumps(new_comps, separators=(',', ':'), ensure_ascii=False)
    compact_style = json.dumps(old_canvas, separators=(',', ':'))

    update_payload = {
        'id': PANEL_ID,
        'name': dv.get('name') or 'ReportCenter - DSP Report',
        'pid': dv.get('pid') or 0,
        'type': 'dataV',
        'busiFlag': 'dataV',
        'componentData': compact_comp,
        'canvasStyleData': compact_style,
        'canvasViewInfo': cvi,
        'checkVersion': str(cur_version),
        'version': cur_version + 1,
        'contentId': str(dv.get('contentId', '0')),
        'status': dv.get('status', 0),
        'mobileLayout': dv.get('mobileLayout', False),
        'selfWatermarkStatus': dv.get('selfWatermarkStatus', False),
        'extFlag': dv.get('extFlag', 0),
    }

    r2 = requests.post(
        f'{base}/de2api/dataVisualization/updateCanvas',
        headers=headers,
        json=update_payload,
        timeout=60,
    )
    print('updateCanvas', r2.status_code, r2.text[:400])
    if r2.status_code == 200 and r2.json().get('code') == 0:
        requests.post(
            f'{base}/de2api/dataVisualization/updatePublishStatus',
            headers=headers,
            json={'id': PANEL_ID, 'type': 'dataV', 'busiFlag': 'dataV', 'status': 1, 'pid': 0},
            timeout=30,
        )
        print('Published OK')
    print(f'Preview: {base}/#/preview/{PANEL_ID}')


if __name__ == '__main__':
    main()
