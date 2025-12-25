import requests
import time

url = 'http://127.0.0.1:5000/api/chat'
# wait for server up to ~15s
for i in range(15):
    try:
        resp = requests.post(url, json={'prompt':'Introduce yourself briefly.'}, timeout=30)
        print('CHAT STATUS', resp.status_code)
        print(resp.text)
        break
    except Exception as e:
        print('waiting for server...', i, str(e))
        time.sleep(1)
else:
    print('server did not respond to /api/chat')

# streaming endpoint
url2 = 'http://127.0.0.1:5000/api/chat/stream'
try:
    r = requests.post(url2, json={'prompt':'Introduce yourself briefly.'}, stream=True, timeout=60)
    print('STREAM STATUS', r.status_code)
    for line in r.iter_lines(decode_unicode=True):
        if line:
            print('STREAM CHUNK:', line)
except Exception as e:
    print('STREAM ERR', e)
