import requests
import re

base = 'http://47.236.78.123:8100'

# Get the main JS
r = requests.get(f'{base}/js/index-0.0.0-dataease.js', timeout=10)
chunks = re.findall(r'"([^"]*\.js)"', r.text)

# The login form handling is likely in a separate lazy-loaded chunk
# Let me also check the CSS for login-related paths
# First, let me look at the main entry for route definitions to find the login route chunk
js = r.text
# Find route chunks
route_matches = re.findall(r'path:\s*"(/[^"]*login[^"]*)"', js, re.IGNORECASE)
print(f"Login routes: {route_matches}")

# Look for lazy-loaded login components
login_imports = re.findall(r'["\']([^"\']*login[^"\']*\.js)["\']', js, re.IGNORECASE)
print(f"Login imports: {login_imports}")

# Broader search - find all dynamic imports
all_imports = re.findall(r'import\(["\']([^"\']+)["\']', js)
print(f"\nDynamic imports ({len(all_imports)}):")
for imp in all_imports[:50]:
    print(f"  {imp}")

# Search for the login component in all chunks
print("\n\nSearching for login form in all chunks...")
for chunk in chunks:
    url = f'{base}/{chunk.lstrip("./")}'
    try:
        r2 = requests.get(url, timeout=5)
        js2 = r2.text
        if 'loginForm' in js2 or ('pwd' in js2 and 'encrypt' in js2.lower()):
            print(f"\n  FOUND in {chunk} (size={len(js2)})")
            # Show context around password/encrypt
            for pat in ['loginForm', 'encrypt', '.pwd', 'rsaEncrypt']:
                for m in re.finditer(pat, js2, re.IGNORECASE):
                    start = max(0, m.start() - 300)
                    end = min(len(js2), m.end() + 300)
                    print(f"    [{pat} at {m.start()}]: {js2[start:end]}")
                    break
    except:
        pass
