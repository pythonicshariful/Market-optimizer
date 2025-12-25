import os
import sys

# minimal .env loader (project root)
def load_dotenv_simple(path=None):
    start = os.path.abspath(os.path.dirname(__file__))
    candidates = [os.path.join(start, '.env')]
    for p in candidates:
        if os.path.exists(p):
            with open(p, 'r', encoding='utf-8') as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=',1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_dotenv_simple()
key = os.environ.get('GEMINI_API_KEY')
if not key:
    print('GEMINI_API_KEY not found in env or .env')
    sys.exit(1)

try:
    from google.genai import Client
except Exception as e:
    print('google.genai import failed:', e)
    sys.exit(1)

model = os.environ.get('GEMINI_MODEL','gemini-2.5-flash-lite')
system = (
    "You are a senior retail business analyst advising a product manager. "
    "Be professional, helpful and clear. Start with a one-line summary, then provide up to 3 concise recommendations, "
    "and finish with 1 suggested next action the user can take. Reference any dashboard context if provided."
)
prompt = system + "\n\nUser: Introduce yourself briefly.\n\nAssistant:"

client = Client(api_key=key)
try:
    resp = client.models.generate_content(model=model, contents=prompt)
    if hasattr(resp, 'text') and resp.text:
        print('MODEL TEXT:\n')
        print(resp.text)
    else:
        print('MODEL RESPONSE (repr):')
        print(repr(resp))
except Exception as e:
    print('call failed:', e)
