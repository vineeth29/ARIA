"""Quick test — verify all provider API keys work."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from providers import SmartRouter

r = SmartRouter()
print(f"\nProviders ready: {r.count_ready()}/4")
for p in r.providers:
    status = "READY" if p.is_ready() else "NOT READY"
    print(f"  {p.name} ({p.model}): {status}")

# Quick test with Groq
print("\n--- Testing Groq (quick ping) ---")
try:
    reply = r.providers[0].stream_response(
        [{"role": "user", "content": "Say hello in 5 words."}],
        system_prompt="You are a helpful assistant. Reply briefly."
    )
    print(f"\n[SUCCESS] Groq works!")
except Exception as e:
    print(f"\n[FAILED] Groq: {e}")
