from dotenv import load_dotenv
import os
import sys

load_dotenv()

def fail(msg):
    print(f"[test_env] ERROR: {msg}")
    sys.exit(1)

if not os.getenv("NEO4J_URI"):
    fail("NEO4J_URI is not set")

if not os.getenv("OPENAI_API_KEY"):
    fail("OPENAI_API_KEY is not set")

if not os.getenv("NEO4J_USER"):
    fail("NEO4J_USER is not set")

if not os.getenv("NEO4J_PASSWORD"):
    fail("NEO4J_PASSWORD is not set")

if not os.getenv("NEO4J_DATABASE"):
    fail("NEO4J_DATABASE is not set")

if not os.getenv("AURA_INSTANCEID"):
    fail("AURA_INSTANCEID is not set")

print("[test_env] Environment OK")

sys.exit(0)
