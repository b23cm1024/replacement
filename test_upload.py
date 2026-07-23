import urllib.request
import os

file_path = 'test_files/offer_letter.pdf'
with open(file_path, 'rb') as f:
    file_data = f.read()

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
headers = {
    'Content-Type': f'multipart/form-data; boundary={boundary}'
}

body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(file_path)}"\r\n'
    f'Content-Type: application/pdf\r\n\r\n'
).encode('utf-8') + file_data + f'\r\n--{boundary}--\r\n'.encode('utf-8')

req = urllib.request.Request('http://localhost:8000/upload', data=body, headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        print(resp.read().decode())
except Exception as e:
    import urllib.error
    if isinstance(e, urllib.error.HTTPError):
        print('HTTP ERROR:', e.code, e.read().decode())
    else:
        print('ERROR:', e)
