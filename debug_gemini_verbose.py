import os, traceback, logging

# Enable verbose HTTP logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('urllib3').setLevel(logging.DEBUG)

print('Python executable:', os.sys.executable)
print('ENV GEMINI_API_KEY=', os.environ.get('GEMINI_API_KEY'))
print('ENV GEMINI_API_URL=', os.environ.get('GEMINI_API_URL'))
print('ENV GEMINI_USE_BEARER=', os.environ.get('GEMINI_USE_BEARER'))
print('ENV GEMINI_MODEL=', os.environ.get('GEMINI_MODEL'))

# Explicitly load .env from project root before importing llm (user requested explicit load)
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    print('Loading .env from', env_path)
    try:
        with open(env_path, 'r', encoding='utf-8') as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip(); v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)
    except Exception as e:
        print('Failed loading .env:', e)
else:
    print('.env not found at', env_path)

try:
    import llm
    print('Imported llm module')
except Exception as e:
    print('Failed to import llm:', repr(e))
    traceback.print_exc()
    raise

prompt = 'Please introduce yourself briefly and confirm which model you used to answer.'
print('\nCalling llm._generate_with_gemini(...)\n')
try:
    resp = llm._generate_with_gemini(prompt)
    print('\n--- GEMINI RESPONSE ---\n')
    print(resp)
except Exception as e:
    print('\n--- EXCEPTION FROM _generate_with_gemini ---\n')
    print(repr(e))
    traceback.print_exc()

print('\nNow trying streaming call llm._stream_gemini(...) to capture chunks:\n')
try:
    for chunk in llm._stream_gemini(prompt):
        print('CHUNK:', repr(chunk))
except Exception as e:
    print('\n--- EXCEPTION FROM _stream_gemini ---\n')
    print(repr(e))
    traceback.print_exc()
