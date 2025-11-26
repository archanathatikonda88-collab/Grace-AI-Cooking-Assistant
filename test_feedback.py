import requests
import json

def test_feedback_endpoint():
    try:
        # Test feedback submission
        response = requests.post('http://127.0.0.1:8000/api/recipe-feedback',
                                json={
                                    'recipe_id': 1,
                                    'rating': 5,
                                    'comment': 'Great recipe! Very tasty.',
                                    'recipe_name': 'Chicken Tikka Masala'
                                })
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Feedback Response:")
            print(json.dumps(data, indent=2))
            print("✅ Feedback submission working!")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_feedback_endpoint()