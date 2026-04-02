import requests
import re

base = 'http://47.236.78.123:8100'
url = f'{base}/assets/chunk/ConfigGlobal.vue_vue_type_script_setup_true_lang-0.0.0-dataease.js'
r = requests.get(url, timeout=30)
js = r.text

# Search for password encryption pattern - look for where Pm (localLogin) is called
# Search for the login form handling
patterns_to_search = ['pwd', 'password', 'rsaKey', 'Pm(', 'loginForm', 'handleLogin', 'aesEncrypt', 'symmetricKey']

for pat in patterns_to_search:
    matches = list(re.finditer(re.escape(pat), js))
    if matches:
        print(f"\n=== Pattern '{pat}' found {len(matches)} times ===")
        for m in matches[:2]:
            start = max(0, m.start() - 200)
            end = min(len(js), m.end() + 300)
            print(f"  [{m.start()}]: ...{js[start:end]}...")
