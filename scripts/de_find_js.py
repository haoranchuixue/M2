"""Find relevant JS chunk files in DataEase."""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import re

base = 'http://47.236.78.123:8100'

# Get the index HTML to find chunk references
r = requests.get(f'{base}/', timeout=30)
html = r.text

# Find all JS files referenced
js_files = re.findall(r'["\']([^"\']*\.js)["\']', html)
print(f"JS files in HTML: {len(js_files)}")
for f in js_files[:10]:
    print(f"  {f}")

# Get the main JS file and look for chunk references
r2 = requests.get(f'{base}/js/index-0.0.0-dataease.js', timeout=30)
main_js = r2.text

# Find dynamic imports / chunk references
chunks = re.findall(r'["\'](\./[^"\']*\.js)["\']', main_js)
print(f"\nChunk references: {len(chunks)}")

# Also search for updateCanvas in all chunks
# Let's first find the chunk that contains the save logic
search_terms = ['updateCanvas', 'canvasViewInfo', 'de2api/dataVisualization']
for term in search_terms:
    if term in main_js:
        idx = main_js.index(term)
        print(f"\n'{term}' at {idx}: {main_js[max(0,idx-100):idx+200]}")
    else:
        print(f"\n'{term}' not in main JS")

# Try to find the API module
api_patterns = re.findall(r'/de2api/[a-zA-Z/]+', main_js)
print(f"\nAPI endpoints in main JS: {len(set(api_patterns))}")
for p in sorted(set(api_patterns)):
    print(f"  {p}")
