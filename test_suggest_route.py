import requests
import json

def test_suggest_route():
    try:
        # Test suggest endpoint
        response = requests.post('http://127.0.0.1:8000/suggest', 
                                json={
                                    'ingredients': 'chicken, tomato, onion',
                                    'cuisine': 'italian',
                                    'difficulty': 'easy'
                                })
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Suggest Route Response:")
            print(json.dumps(data, indent=2))
            
            if data.get('success') and 'cards' in data:
                cards = data['cards']
                print(f"\n✅ Found {len(cards)} recipe cards")
                
                if cards:
                    first_recipe = cards[0]
                    required_fields = ['name', 'description', 'image_url', 'ingredients', 'instructions', 'difficulty', 'cuisine', 'cooking_time']
                    missing_fields = [field for field in required_fields if field not in first_recipe]
                    if missing_fields:
                        print(f"Missing fields in first recipe: {missing_fields}")
                    else:
                        print("✅ First recipe has all required fields!")
            else:
                print("❌ No cards found in response")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_suggest_route()