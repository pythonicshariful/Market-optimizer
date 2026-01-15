# File: llm.py
import os
import json
import requests

# Import configuration
try:
    from config import get_gemini_api_key, GEMINI_MODEL, OPENAI_API_KEY, OPENAI_MODEL
    # Set environment variables from config if not already set
    if not os.environ.get('GEMINI_API_KEY'):
        key = get_gemini_api_key()
        if key:
            os.environ['GEMINI_API_KEY'] = key
    if not os.environ.get('GEMINI_MODEL'):
        os.environ['GEMINI_MODEL'] = GEMINI_MODEL
    if not os.environ.get('OPENAI_API_KEY') and OPENAI_API_KEY:
        os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    if not os.environ.get('OPENAI_MODEL'):
        os.environ['OPENAI_MODEL'] = OPENAI_MODEL
except ImportError:
    # Fallback: Load from .env file manually
    def _load_local_env(path=None):
        # Search for a .env file in this directory and up to 4 parents
        start = os.path.abspath(os.path.dirname(__file__))
        candidates = []
        cur = start
        for _ in range(5):
            candidates.append(os.path.join(cur, '.env'))
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        if path:
            candidates.insert(0, os.path.abspath(path))

        for p in candidates:
            if not os.path.exists(p):
                continue
            try:
                with open(p, 'r', encoding='utf-8') as fh:
                    for raw in fh:
                        line = raw.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' not in line:
                            continue
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and k not in os.environ:
                            os.environ[k] = v
                return
            except Exception:
                continue
    
    _load_local_env()


def load_llm():
    """Try to construct a lightweight local pipeline; return None if unavailable.

    Prefer using an external API (OpenAI) when `OPENAI_API_KEY` is set —
    `generate_insight` will choose the best available backend.
    """
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        model_name = "EleutherAI/gpt-neo-125M"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        return pipeline('text-generation', model=model, tokenizer=tokenizer)
    except Exception:
        return None



def _generate_with_openai(prompt, model_name=None):
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY not set')
    model_name = model_name or os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    system = (
        "You are a senior retail business analyst advising a product manager. "
        "Be professional, helpful and clear. Start with a one-line summary, then provide up to 3 concise recommendations, "
        "and finish with 1 suggested next action the user can take. Reference any dashboard context if provided. "
        "Keep language plain, use numbered or bullet lists where helpful, and be concise (two to five paragraphs)."
    )
    payload = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': float(os.environ.get('LLM_TEMPERATURE', 0.25)),
        'max_tokens': int(os.environ.get('LLM_MAX_TOKENS', 512)),
        'top_p': float(os.environ.get('LLM_TOP_P', 0.95))
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Extract assistant message
    out = data['choices'][0]['message']['content']
    return _polish_answer(out)


def _generate_with_gemini(prompt, model_name=None):
    """Call a Gemini-compatible endpoint.

    Behaviors:
    - If `GEMINI_API_URL` is set, POST JSON {"prompt": prompt} to it.
    - Otherwise attempt a Google Generative API endpoint using `GEMINI_MODEL` or a sensible default.
    The function attempts several common response shapes and returns the assistant text.
    """
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set')

    custom_url = os.environ.get('GEMINI_API_URL')
    headers = {'Content-Type': 'application/json'}
    use_bearer = key.startswith('ya29.') or key.lower().startswith('oauth') or os.environ.get('GEMINI_USE_BEARER', '').lower() == 'true'
    if use_bearer:
        headers['Authorization'] = f'Bearer {key}'

    # Compose a gentle system prefix to improve response quality and structure
    system = (
        "You are a senior retail business analyst. Answer professionally and helpfully: start with a one-line summary, "
        "then list up to 3 actionable recommendations, and finish with a clear next step. Keep answers concise and structured."
    )
    composed_prompt = system + "\n\nUser: " + prompt + "\n\nAssistant:"
    body = {'prompt': composed_prompt}

    # Helper to extract text from common response shapes
    def _pick_text(obj):
        if not obj:
            return None
        if isinstance(obj, dict):
            if 'candidates' in obj and obj['candidates']:
                c = obj['candidates'][0]
                return c.get('content') or c.get('output') or c.get('text')
            if 'output' in obj and isinstance(obj['output'], list) and obj['output']:
                first = obj['output'][0]
                if isinstance(first, dict):
                    return first.get('content') or first.get('text')
            if 'outputs' in obj and isinstance(obj['outputs'], list) and obj['outputs']:
                first = obj['outputs'][0]
                if isinstance(first, dict):
                    return first.get('content') or first.get('text')
            if 'response' in obj and isinstance(obj['response'], str):
                return obj['response']
        if isinstance(obj, str):
            return obj
        return None

    import requests

    # 1) custom URL
    if custom_url:
        url = custom_url
        params = {}
        if not use_bearer:
            params['key'] = key
        resp = requests.post(url, headers=headers, params=params, json=body, timeout=30)
        resp.raise_for_status()
        j = resp.json()
        txt = _pick_text(j)
        if txt:
            return _polish_answer(txt)

    # 1b) If google.genai client is available, prefer it (works with plain API keys)
    try:
        from google.genai import Client as GenAIClient  # type: ignore
        try:
            model_name = model_name or os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')
            client = GenAIClient(api_key=key)
            # Use composed prompt so the model follows the system guidance
            resp = client.models.generate_content(model=model_name, contents=composed_prompt)
            # Prefer .text if present, else try common attributes
            if hasattr(resp, 'text') and resp.text:
                return _polish_answer(resp.text)
            if hasattr(resp, 'output'):
                # attempt to extract text from output structure
                try:
                    out = getattr(resp, 'output')
                    if isinstance(out, (list, tuple)) and out:
                        first = out[0]
                        if isinstance(first, dict):
                            return first.get('content') or first.get('text') or str(first)
                except Exception:
                    pass
            # fallback to str(resp)
            return str(resp)
        except Exception:
            # if client fails, fall through to HTTP attempts
            pass
    except Exception:
        # google.genai not installed; continue with HTTP
        pass

    # 2) try known Google Generative Language endpoints
    # Allow GEMINI_MODEL to be comma-separated list; try each model in order
    # Try gemini-2.5-flash-lite first, then fall back to gemini-2.0-flash
    raw_models = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite,gemini-2.0-flash')
    model_list = [m.strip() for m in raw_models.split(',') if m.strip()]
    # endpoints to try for each model (include v1, v1beta2, and generativeai v1)
    endpoint_templates = [
        'https://generativelanguage.googleapis.com/v1beta2/models/{model}:generate',
        'https://generativelanguage.googleapis.com/v1/models/{model}:generate',
        'https://generativeai.googleapis.com/v1/models/{model}:generate',
    ]

    last_err = None
    for model in model_list:
        for tpl in endpoint_templates:
            url_try = tpl.format(model=model)
            try:
                params = {}
                if not use_bearer:
                    params['key'] = key
                payload = {'prompt': {'text': composed_prompt}, 'temperature': float(os.environ.get('LLM_TEMPERATURE', 0.25)), 'maxOutputTokens': int(os.environ.get('LLM_MAX_TOKENS', 512))}
                resp = requests.post(url_try, headers=headers, params=params, json=payload, timeout=30)
                # Log non-200 responses for debugging
                if resp.status_code != 200:
                    try:
                        body = resp.text
                    except Exception:
                        body = '<unreadable body>'
                    last_err = (resp.status_code, url_try, body)
                    continue
                j = resp.json()
                txt = _pick_text(j)
                if txt:
                    return _polish_answer(txt)
            except Exception as e:
                last_err = e
                continue
    # If we reach here, record helpful error
    if last_err:
        raise RuntimeError(f'Gemini API request failed or returned no usable text: {last_err}')


def generate_insight(llm, prompt, lang='en'):
    """Generate an insight string.

    Priority: OpenAI API (if API key present) -> local `llm` pipeline -> dummy response.
    """
    # 1) OpenAI API if configured
    try:
        # Prefer Gemini if available (user said they added Gemini API)
        if os.environ.get('GEMINI_API_KEY'):
            try:
                return _generate_with_gemini(prompt)
            except Exception:
                # fall through to OpenAI or local
                pass
        if os.environ.get('OPENAI_API_KEY'):
            return _generate_with_openai(prompt)
    except Exception:
        # If API call fails, fall back to other methods
        pass

    # 2) Local transformers pipeline if available
    if llm is not None:
        try:
            out = llm(prompt, max_new_tokens=200)
            # pipeline text-generation returns a list of dicts with 'generated_text'
            text = out[0].get('generated_text') if isinstance(out, list) else str(out)
            return text
        except Exception:
            pass

    # 3) Dummy fallback
    return f"(Assistant offline) Short answer: {prompt[:200]}"


def generate_insight_stream(llm, prompt):
    """Yield incremental text chunks from the best available streaming backend.

    Order: Gemini streaming -> OpenAI streaming -> fallback single response.
    """
    # Prefer a client-backed (non-streaming) Gemini call when available so
    # the chat UI receives a response even if streaming endpoints are not
    # available for the key. This yields a single chunk with the full text.
    try:
        if os.environ.get('GEMINI_API_KEY'):
            try:
                txt = _generate_with_gemini(prompt)
                yield txt
                return
            except Exception:
                # Fall through to streaming attempts
                pass
    except Exception:
        pass

    try:
        if os.environ.get('OPENAI_API_KEY'):
            for chunk in _stream_openai(prompt):
                yield chunk
            return
    except Exception:
        pass

    yield generate_insight(llm, prompt)


def _stream_openai(prompt, model_name=None):
    key = os.environ.get('OPENAI_API_KEY')
    if not key:
        raise RuntimeError('OPENAI_API_KEY not set')
    model_name = model_name or os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    system = (
        "You are a senior retail business analyst. Provide a brief summary, up to 3 recommendations, and one next step. "
        "Keep the tone professional and helpful; prefer numbered recommendations when useful."
    )
    payload = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': prompt}
        ],
        'temperature': float(os.environ.get('LLM_TEMPERATURE', 0.25)),
        'stream': True
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=60)
    resp.raise_for_status()
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        line = raw.lstrip()
        if line.startswith('data:'):
            data = line[len('data:'):].strip()
            if data == '[DONE]':
                break
            try:
                j = json.loads(data)
                for ch in j.get('choices', []):
                    delta = ch.get('delta', {})
                    content = delta.get('content')
                    if content:
                        yield content
            except Exception:
                yield data


def _stream_gemini(prompt, model_name=None):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise RuntimeError('GEMINI_API_KEY not set')
    custom_url = os.environ.get('GEMINI_API_URL')
    headers = {'Content-Type': 'application/json'}
    use_bearer = key.startswith('ya29.') or key.lower().startswith('oauth') or os.environ.get('GEMINI_USE_BEARER', '').lower() == 'true'
    if use_bearer:
        headers['Authorization'] = f'Bearer {key}'
    params = {}
    if not use_bearer:
        params['key'] = key

    body = {'prompt': prompt}
    urls = []
    if custom_url:
        urls.append(custom_url)
    # Use model name without extra 'models/' prefix; construct endpoints accordingly
    model_name = model_name or os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
    urls.extend([
        f'https://generativelanguage.googleapis.com/v1beta2/models/{model_name}:generate',
        f'https://generativeai.googleapis.com/v1/models/{model_name}:generate'
    ])

    # Prefer google.genai client streaming when available (yield full text as single chunk)
    try:
        from google.genai import Client as GenAIClient  # type: ignore
        try:
            model_name = model_name or os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash-lite')
            client = GenAIClient(api_key=key)
            resp = client.models.generate_content(model=model_name, contents=prompt)
            text = None
            if hasattr(resp, 'text') and resp.text:
                text = resp.text
            else:
                try:
                    j = resp
                    # attempt to extract text-like fields
                    if isinstance(j, dict):
                        text = j.get('text') or j.get('content')
                except Exception:
                    text = str(resp)
            if text:
                yield text
                return
        except Exception:
            pass
    except Exception:
        pass

    for url in urls:
        try:
            r = requests.post(url, headers=headers, params=params, json=body, stream=True, timeout=60)
            r.raise_for_status()
            for chunk in r.iter_lines(decode_unicode=True):
                if not chunk:
                    continue
                try:
                    j = json.loads(chunk)
                    if isinstance(j, dict):
                        txt = j.get('text') or j.get('output') or j.get('content')
                        if not txt and 'candidates' in j and j['candidates']:
                            cand = j['candidates'][0]
                            txt = cand.get('content') or cand.get('output') or cand.get('text')
                        if txt:
                            yield txt
                        else:
                            yield chunk
                    else:
                        yield chunk
                except Exception:
                    yield chunk
            break
        except Exception:
            continue
    return


def _polish_answer(text: str) -> str:
    """Lightly clean and structure model output for better readability."""
    if not text:
        return ''
    try:
        t = str(text).strip()
        # remove multiple blank lines and trailing spaces
        lines = [ln.rstrip() for ln in t.splitlines() if ln.strip()]
        t = '\n'.join(lines)
        # if very short, add a gentle suggestion to elicit more detail
        if len(t) < 40:
            t = t + "\n\nRecommendation: provide more context or ask for examples to get a fuller answer."
        return t
    except Exception:
        return str(text).strip()
