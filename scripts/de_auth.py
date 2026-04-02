import requests
import json

base = 'http://47.236.78.123:8100'

# First get the symmetric key
r = requests.get(f'{base}/de2api/symmetricKey', timeout=5)
print('symmetricKey status:', r.status_code)
print('symmetricKey response:', r.text[:500])

# Also check dekey
r2 = requests.get(f'{base}/de2api/dekey', timeout=5)
print('\ndekey status:', r2.status_code)
print('dekey response:', r2.text[:200])

# Try model endpoint
r3 = requests.get(f'{base}/de2api/model', timeout=5)
print('\nmodel status:', r3.status_code)
print('model response:', r3.text[:200])

# Try with AES encryption using the symmetric key
sym_key = None
if r.status_code == 200:
    data = r.json()
    if data.get('code') == 0:
        sym_key = data.get('data')
        print(f'\nSymmetric key: {sym_key}')

if sym_key:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    import base64
    
    # Try AES-ECB encryption
    key_bytes = sym_key.encode('utf-8')
    # Pad or truncate key to 16 bytes
    if len(key_bytes) < 16:
        key_bytes = key_bytes.ljust(16, b'\0')
    elif len(key_bytes) > 16:
        key_bytes = key_bytes[:16]
    
    cipher = AES.new(key_bytes, AES.MODE_ECB)
    pwd_padded = pad(b'DataEase@123456', AES.block_size)
    encrypted = cipher.encrypt(pwd_padded)
    encrypted_b64 = base64.b64encode(encrypted).decode()
    print(f'\nAES encrypted pwd: {encrypted_b64}')
    
    # Try login
    payload = {'name': 'admin', 'pwd': encrypted_b64}
    r4 = requests.post(f'{base}/de2api/login/localLogin', json=payload, timeout=10)
    print(f'\nLogin status: {r4.status_code}')
    print(f'Login response: {r4.text[:500]}')
