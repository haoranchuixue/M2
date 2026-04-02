import requests
import re

base = 'http://47.236.78.123:8100'

# Get the main JS
r = requests.get(f'{base}/js/index-0.0.0-dataease.js', timeout=10)
chunks = re.findall(r'"([^"]*\.js)"', r.text)

# Search specifically for the chunk that handles login form
for chunk in chunks:
    url = f'{base}/{chunk.lstrip("./")}'
    try:
        r2 = requests.get(url, timeout=10)
        js = r2.text
        
        # Look for the login handler function
        if 'loginForm' in js or 'handleLogin' in js or ('pwd' in js and 'dekey' in js):
            print(f"\n{'='*60}")
            print(f"FOUND in {chunk} (size={len(js)})")
            print(f"{'='*60}")
            
            # Find the login-related section
            for pat in ['loginForm', 'handleLogin', 'getDekey', '.pwd', 'login/localLogin']:
                for m in re.finditer(re.escape(pat), js):
                    start = max(0, m.start() - 500)
                    end = min(len(js), m.end() + 500)
                    print(f"\n  [{pat} at {m.start()}]:")
                    print(f"  {js[start:end]}")
                    break
    except Exception as e:
        pass
