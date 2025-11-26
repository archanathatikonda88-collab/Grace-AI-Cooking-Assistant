import sys
import os
sys.path.append(os.path.dirname(__file__))

# Simple test to verify difficulty card generation
from app import suggest_recipes
import json

# Mock Flask request for testing
class MockRequest:
    def __init__(self, data):
        self.json = data

# Test easy difficulty
print("=== Testing EASY difficulty ===")
test_request = MockRequest({
    'ingredients': 'chicken',
    'difficulty': 'easy',
    'cuisine': 'international'
})

# Temporarily replace Flask request with our mock
import app
original_request = app.request
app.request = test_request

try:
    result = suggest_recipes()
    if hasattr(result, 'get_json'):
        data = result.get_json()
    else:
        # For direct returns
        data = result
    
    print("Cards returned:", len(data.get('cards', [])))
    for i, card in enumerate(data.get('cards', [])[:2]):
        print(f"Card {i+1}:")
        print(f"  Name: {card.get('name')}")
        print(f"  Difficulty: {card.get('difficulty', 'NOT FOUND')}")
        print(f"  Short: {card.get('short', '')[:60]}...")
        print()

except Exception as e:
    print("Error:", str(e))
finally:
    app.request = original_request

print("\n=== Testing COMPLEX difficulty ===")
test_request = MockRequest({
    'ingredients': 'beef, wine',
    'difficulty': 'complex',
    'cuisine': 'french'
})

app.request = test_request

try:
    result = suggest_recipes()
    if hasattr(result, 'get_json'):
        data = result.get_json()
    else:
        data = result
    
    print("Cards returned:", len(data.get('cards', [])))
    for i, card in enumerate(data.get('cards', [])[:2]):
        print(f"Card {i+1}:")
        print(f"  Name: {card.get('name')}")
        print(f"  Difficulty: {card.get('difficulty', 'NOT FOUND')}")
        print(f"  Short: {card.get('short', '')[:60]}...")
        print()

except Exception as e:
    print("Error:", str(e))
finally:
    app.request = original_request