import requests
import re

base = 'http://47.236.78.123:8100'
url = f'{base}/assets/chunk/ConfigGlobal.vue_vue_type_script_setup_true_lang-0.0.0-dataease.js'
r = requests.get(url, timeout=30)
js = r.text
print(f"Size: {len(js)}")

# Find login-related code
# Look around the localLogin reference
idx = js.find('localLogin')
if idx >= 0:
    # Get wider context
    start = max(0, idx - 2000)
    end = min(len(js), idx + 2000)
    print(f"\n=== Around localLogin ({idx}) ===")
    print(js[start:end])

# Search for encryption code
for pat in ['rsaEncrypt', 'encrypt(', 'dekey', 'symmetricKey', 'setDekey', 'getDekey']:
    for m in re.finditer(re.escape(pat), js):
        start = max(0, m.start() - 300)
        end = min(len(js), m.end() + 300)
        print(f"\n=== {pat} at {m.start()} ===")
        print(js[start:end])
        break
