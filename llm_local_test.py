import time
import llm

print('Loaded llm module')
# avoid attempting to download large local transformer models during tests
llm_obj = None
print('Local transformer pipeline available: False (skipped)')
prompt = 'Introduce yourself briefly.'
print('\n=== generate_insight ===')
try:
    out = llm.generate_insight(llm_obj, prompt)
    print(out)
except Exception as e:
    print('generate_insight error:', e)

print('\n=== generate_insight_stream ===')
try:
    for chunk in llm.generate_insight_stream(llm_obj, prompt):
        print('CHUNK:', chunk)
        time.sleep(0.1)
except Exception as e:
    print('stream error:', e)
