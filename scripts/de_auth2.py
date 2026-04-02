import requests
import json
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

base = 'http://47.236.78.123:8100'

# Get symmetric key
r = requests.get(f'{base}/de2api/symmetricKey', timeout=5)
sym_key_b64 = r.json()['data']
print(f'Symmetric key (b64): {sym_key_b64}')

# Decode the base64 symmetric key to get raw bytes
sym_key_bytes = base64.b64decode(sym_key_b64)
print(f'Symmetric key bytes len: {len(sym_key_bytes)}')
print(f'Symmetric key hex: {sym_key_bytes.hex()}')

password = 'DataEase@123456'

# Try multiple AES approaches
approaches = []

# Approach 1: AES-ECB with PKCS7 padding, key from b64 decode
try:
    cipher = AES.new(sym_key_bytes, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    approaches.append(('ECB-b64key-PKCS7', base64.b64encode(encrypted).decode()))
except Exception as e:
    print(f'Approach 1 error: {e}')

# Approach 2: AES-ECB with PKCS7 padding, key as raw string (first 16 chars)
try:
    raw_key = sym_key_b64[:16].encode('utf-8')
    cipher = AES.new(raw_key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    approaches.append(('ECB-strkey16-PKCS7', base64.b64encode(encrypted).decode()))
except Exception as e:
    print(f'Approach 2 error: {e}')

# Approach 3: AES-CBC with zero IV, b64 decoded key
try:
    iv = b'\x00' * 16
    cipher = AES.new(sym_key_bytes, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    approaches.append(('CBC-b64key-zeroIV', base64.b64encode(encrypted).decode()))
except Exception as e:
    print(f'Approach 3 error: {e}')

# Approach 4: AES-CBC with key as IV
try:
    cipher = AES.new(sym_key_bytes, AES.MODE_CBC, sym_key_bytes)
    encrypted = cipher.encrypt(pad(password.encode('utf-8'), AES.block_size))
    approaches.append(('CBC-b64key-keyAsIV', base64.b64encode(encrypted).decode()))
except Exception as e:
    print(f'Approach 4 error: {e}')

# Try each approach
for name, enc_pwd in approaches:
    payload = {'name': 'admin', 'pwd': enc_pwd}
    r2 = requests.post(f'{base}/de2api/login/localLogin', json=payload, timeout=10)
    resp = r2.json()
    code = resp.get('code')
    msg = resp.get('msg', '')
    token = str(resp.get('data', ''))[:100] if resp.get('data') else 'None'
    print(f'\n{name}: code={code}, msg={msg[:100]}, token={token}')
