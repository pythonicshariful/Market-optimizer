import traceback
import os
# Ensure project .env is loaded by importing llm (it now has a loader)
try:
    import llm
except Exception as e:
    print('Failed to import llm:', e)
    traceback.print_exc()
    raise SystemExit(1)

prompt = 'Please introduce yourself briefly and confirm which model you used to answer.'
try:
    print('GEMINI_API_KEY (at import time)=', os.environ.get('GEMINI_API_KEY'))
    resp = llm._generate_with_gemini(prompt)
    print('\n--- GEMINI RESPONSE ---\n')
    print(resp)
except Exception as e:
    print('\n--- ERROR WHEN CALLING _generate_with_gemini ---\n')
    print(repr(e))
    traceback.print_exc()
