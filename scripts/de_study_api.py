"""Study the DataEase API by examining JS source for save/update patterns."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

base = 'http://47.236.78.123:8100'

# Download the main JS file and search for canvas/chart save patterns
r = requests.get(f'{base}/js/index-0.0.0-dataease.js', timeout=60)
js_content = r.text
print(f"JS file size: {len(js_content)} chars")

# Search for updateCanvas related code
search_terms = ['updateCanvas', 'saveCanvas', 'canvasViewInfo', 'chartView', 'core_chart_view']
for term in search_terms:
    idx = js_content.find(term)
    if idx >= 0:
        context = js_content[max(0,idx-200):idx+300]
        print(f"\n=== Found '{term}' at offset {idx} ===")
        print(context)
        print("---")
    else:
        print(f"\n'{term}' not found in JS")
