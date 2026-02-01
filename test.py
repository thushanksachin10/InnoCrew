# test_cities.py
from whatsapp.webhook import handle_message

test_cases = [
    "START TRIP FROM Pune TO Agra",
    "start trip from pune to agra", 
    "Start Trip From Pune To Agra",
    "START TRIP FROM Pune to Agra",
    "start trip pune to agra",
    "plan trip pune to agra",
    "trip pune to agra",
    "START TRIP FROM Mumbai TO Delhi",
    "start trip from bangalore to chennai",
    "START TRIP FROM Kolkata TO Hyderabad"
]

print("🧪 Testing city combinations...")
for test in test_cases:
    print(f"\n{'='*60}")
    print(f"Input: {test}")
    response = handle_message(test, "+919999999999")
    print(f"Response: {response[:200]}...")