import time, requests, sys

def wait_up(url, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False

base = 'http://127.0.0.1:5000'
print('waiting for', base)
if not wait_up(base, timeout=30):
    print('server not up after timeout')
    sys.exit(1)

try:
    r = requests.post(base + '/api/chat', json={'prompt':'Introduce yourself briefly.'}, params={'include_context':'false'}, timeout=30)
    print('\n=== /api/chat ===')
    print('status', r.status_code)
    print(r.text)
except Exception as e:
    print('CHAT ERROR', e)

try:
    r = requests.post(base + '/api/chat/stream', json={'prompt':'Introduce yourself briefly.'}, params={'include_context':'false'}, stream=True, timeout=60)
    print('\n=== /api/chat/stream ===')
    print('status', r.status_code)
    for line in r.iter_lines(decode_unicode=True):
        if line:
            print('CHUNK:', line)
except Exception as e:
    print('STREAM ERROR', e)
