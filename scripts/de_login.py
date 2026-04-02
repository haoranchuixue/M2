import requests
import re
import json
import base64

# Get the DataEase frontend page to find JS files
r = requests.get('http://47.236.78.123:8100/', timeout=10)
print('Status:', r.status_code)

# Look for script tags
scripts = re.findall(r'src="([^"]+\.js)"', r.text)
print('JS files:', scripts[:10])
print()
print('Page content (first 3000):')
print(r.text[:3000])
