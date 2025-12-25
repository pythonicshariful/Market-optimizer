import requests
import sys

url = 'http://127.0.0.1:5000/api/chat/stream?product=clothing&include_context=true'
prompt = 'Give a short, actionable pricing recommendation for clothing with one clear next step.'

try:
    r = requests.post(url, json={'prompt': prompt}, stream=True, timeout=120)
    print('status:', r.status_code, file=sys.stderr)
    if r.status_code != 200:
        print(r.text)
        sys.exit(1)
    for chunk in r.iter_content(chunk_size=None):
        if chunk:
            try:
                sys.stdout.write(chunk.decode('utf-8'))
            except Exception:
                sys.stdout.write(chunk.decode('latin-1'))
            sys.stdout.flush()
except Exception as e:
    print('ERROR', e)
    raise
