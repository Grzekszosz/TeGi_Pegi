from dotenv import load_dotenv
import os

load_dotenv()

print("URI:", os.getenv("NEO4J_URI"))
print("USER:", os.getenv("NEO4J_USERNAME"))
print("PWD:", os.getenv("NEO4J_PASSWORD"))
