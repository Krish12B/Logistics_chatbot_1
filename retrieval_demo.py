"""Prints the exact context the chatbot would send to the LLM for a few questions.
No API key needed. Useful for checking that retrieval works."""
from chatbot import build_context
from database import init_database

init_database()
for question in [
    "What is the status of SHP-10001?",
    "Has SHP-10003 cleared customs?",
    "What is the delivery route for SHP-10001?",
    "What causes shipment delays?",
]:
    print("=" * 70)
    print("QUESTION:", question)
    print("-" * 70)
    print(build_context(question))
    print()
