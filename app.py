#test
from dotenv import load_dotenv
import os
load_dotenv(".env")

from agent import run_business_query

if __name__ == "__main__":
    question = "Ilu senior Java developerów mamy dostępnych w Q3 2025?"
    answer = run_business_query(question)
    print("PYTANIE:", question)
    print("ODPOWIEDŹ:", answer)
