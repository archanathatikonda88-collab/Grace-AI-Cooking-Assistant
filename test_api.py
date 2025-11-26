import requests
import json

# Test the suggest endpoint
url = "http://127.0.0.1:8000/suggest"
data = {
    "ingredients": "chicken",
    "cuisine": "indian", 
    "difficulty": "easy"
}

try:
    print(f"Testing {url} with data: {data}")
    response = requests.post(url, json=data, timeout=10)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        if result.get('cards'):
            print(f"Number of recipes: {len(result['cards'])}")
            for i, recipe in enumerate(result['cards']):
                print(f"Recipe {i+1}: {recipe.get('name')} - {recipe.get('description')}")
                print(f"  Image: {recipe.get('image_url')}")
                print(f"  Ingredients: {len(recipe.get('ingredients', []))} items")
                print(f"  Instructions: {len(recipe.get('instructions', []))} steps")
        else:
            print("No recipe cards returned")
            print(f"Full response: {result}")
    else:
        print(f"Error Response: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")