import requests
import json

def test_recipe_detail():
    try:
        # Test recipe detail endpoint
        response = requests.get('http://127.0.0.1:8000/api/recipe/1')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Recipe Detail Response:")
            print(json.dumps(data, indent=2))
            
            # Check if all required fields are present
            required_fields = ['name', 'description', 'image_url', 'ingredients', 'instructions', 'difficulty', 'cuisine', 'cooking_time']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"\nMissing fields: {missing_fields}")
            else:
                print("\n✅ All required fields present!")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_recipe_detail()