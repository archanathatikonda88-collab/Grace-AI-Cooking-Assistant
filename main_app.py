from flask import Flask, render_template, request, jsonify, send_from_directory
import openai
import os
import requests
import time
import random
import json
from datetime import datetime

app = Flask(__name__)

# Configuration
openai.api_key = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', 'your-pexels-api-key-here')

# Enhanced food image mapping for local fallbacks
FOOD_IMAGE_MAPPING = {
    'chicken': 'chicken_curry_pexels.jpg',
    'beef': 'beef_tacos_pexels.jpg',
    'pasta': 'broccoli_and_garlic_pasta_pexels.jpg',
    'broccoli': 'broccoli_stir-fry_pexels.jpg',
    'tacos': 'black_bean_tacos_pexels.jpg',
    'curry': 'chicken_curry_pexels.jpg',
    'rice': 'broccoli_indian_chicken_and_broccoli_rice_bowl_pexels.jpg',
    'salad': 'spaghetti.jpg',  # Changed from quinoa_salad.jpg
    'soup': 'spaghetti.jpg',
    'bread': 'spaghetti.jpg',
    'fish': 'spaghetti.jpg',
    'vegetables': 'broccoli_stir-fry_pexels.jpg',
    'potatoes': 'aloo_jeera_cumin_potatoes_pexels.jpg',
    'default': 'spaghetti.jpg'  # Safe default
}

def fetch_pexels_image(query):
    """Fetch image from Pexels API with error handling"""
    try:
        headers = {
            'Authorization': PEXELS_API_KEY
        }
        
        # Clean and optimize search query
        search_query = f"food {query.lower()}"
        url = f"https://api.pexels.com/v1/search?query={search_query}&per_page=5&size=medium"
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                # Get a random photo from results
                photo = random.choice(data['photos'])
                return photo['src']['medium']
        
        return None
        
    except Exception as e:
        print(f"Pexels API error: {e}")
        return None

def get_local_food_image_fallback(ingredients):
    """Get local fallback image based on ingredients"""
    try:
        # Convert ingredients to lowercase for matching
        ingredients_lower = [ing.lower() for ing in ingredients]
        
        # Try to find a matching image
        for ingredient in ingredients_lower:
            for key, image in FOOD_IMAGE_MAPPING.items():
                if key in ingredient:
                    return f"static/images/{image}"
        
        # If no match found, return default
        return f"static/images/{FOOD_IMAGE_MAPPING['default']}"
        
    except Exception as e:
        print(f"Local fallback error: {e}")
        return f"static/images/{FOOD_IMAGE_MAPPING['default']}"

def validate_and_score_recipe(recipe_text, ingredients):
    """Enhanced recipe validation with scoring system"""
    try:
        score = 0
        recipe_lower = recipe_text.lower()
        ingredients_lower = [ing.lower() for ing in ingredients]
        
        # Check ingredient usage (high priority)
        for ingredient in ingredients_lower:
            if ingredient in recipe_lower:
                score += 30
        
        # Check recipe structure
        if 'ingredients:' in recipe_lower or 'ingredients' in recipe_lower:
            score += 15
        if 'instructions:' in recipe_lower or 'directions:' in recipe_lower or 'steps:' in recipe_lower:
            score += 15
        if 'cook' in recipe_lower or 'bake' in recipe_lower or 'fry' in recipe_lower:
            score += 10
        
        # Length check (reasonable recipe length)
        if 100 <= len(recipe_text) <= 2000:
            score += 10
        
        return score >= 30  # Lowered threshold for more lenient validation
        
    except Exception as e:
        print(f"Recipe validation error: {e}")
        return True  # Default to accepting recipe if validation fails

def get_enhanced_recipes(ingredients):
    """Get recipes with enhanced validation and guaranteed results"""
    try:
        # Create a detailed prompt for better results
        prompt = f"""Create 3 delicious recipes using these ingredients: {', '.join(ingredients)}

Please provide exactly 3 recipes in this format:

**Recipe 1: [Recipe Name]**
Ingredients:
- [ingredient list including the provided ingredients]

Instructions:
1. [step by step cooking instructions]

**Recipe 2: [Recipe Name]**
Ingredients:
- [ingredient list including the provided ingredients]

Instructions:
1. [step by step cooking instructions]

**Recipe 3: [Recipe Name]**
Ingredients:
- [ingredient list including the provided ingredients]

Instructions:
1. [step by step cooking instructions]

Make sure each recipe:
- Uses at least 2 of the provided ingredients: {', '.join(ingredients)}
- Has clear, easy-to-follow instructions
- Is practical and delicious
- Has an appropriate cooking difficulty level"""

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful cooking assistant that creates practical, delicious recipes. Always provide exactly 3 complete recipes using the requested ingredients."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        
        recipe_text = response.choices[0].message.content.strip()
        
        # Validate the response
        if validate_and_score_recipe(recipe_text, ingredients):
            return recipe_text
        else:
            # Fallback: create simple recipes
            return create_fallback_recipes(ingredients)
            
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return create_fallback_recipes(ingredients)

def create_fallback_recipes(ingredients):
    """Create fallback recipes when API fails"""
    recipes = []
    
    base_recipes = [
        {
            "name": f"Simple {ingredients[0].title()} Stir-Fry",
            "instructions": [
                f"Heat oil in a large pan over medium-high heat",
                f"Add {ingredients[0]} and cook for 5-7 minutes",
                "Add your favorite seasonings and vegetables",
                "Stir-fry until tender and well combined",
                "Serve hot with rice or noodles"
            ]
        },
        {
            "name": f"Easy {ingredients[0].title()} Soup",
            "instructions": [
                f"In a large pot, sauté {ingredients[0]} until lightly browned",
                "Add broth and bring to a boil",
                "Add vegetables and seasonings",
                "Simmer for 15-20 minutes until tender",
                "Season to taste and serve hot"
            ]
        },
        {
            "name": f"Quick {ingredients[0].title()} Salad",
            "instructions": [
                f"Cook {ingredients[0]} until tender if needed",
                "Combine with fresh vegetables in a large bowl",
                "Add your favorite dressing",
                "Toss well and let marinate for 10 minutes",
                "Serve chilled or at room temperature"
            ]
        }
    ]
    
    result = ""
    for i, recipe in enumerate(base_recipes, 1):
        result += f"**Recipe {i}: {recipe['name']}**\n"
        result += f"Ingredients:\n"
        result += f"- {ingredients[0]}\n- Mixed vegetables\n- Seasoning to taste\n- Oil for cooking\n\n"
        result += f"Instructions:\n"
        for j, instruction in enumerate(recipe['instructions'], 1):
            result += f"{j}. {instruction}\n"
        result += "\n"
    
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_recipes', methods=['POST'])
def get_recipes():
    try:
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        
        if not ingredients:
            return jsonify({
                'success': False,
                'error': 'Please provide at least one ingredient'
            })
        
        # Get recipes from OpenAI
        recipe_text = get_enhanced_recipes(ingredients)
        
        # Parse recipes
        recipes = []
        recipe_blocks = recipe_text.split('**Recipe ')
        
        for block in recipe_blocks[1:]:  # Skip first empty block
            try:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                # Extract recipe name
                name_line = lines[0]
                if ':' in name_line:
                    recipe_name = name_line.split(':', 1)[1].strip('* ')
                else:
                    recipe_name = name_line.strip('* ')
                
                # Find ingredients and instructions
                ingredients_section = []
                instructions_section = []
                current_section = None
                
                for line in lines[1:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.lower().startswith('ingredients'):
                        current_section = 'ingredients'
                        continue
                    elif line.lower().startswith('instructions') or line.lower().startswith('directions'):
                        current_section = 'instructions'
                        continue
                    
                    if current_section == 'ingredients' and line.startswith('-'):
                        ingredients_section.append(line[1:].strip())
                    elif current_section == 'instructions':
                        if line and (line[0].isdigit() or line.startswith('-')):
                            # Remove numbering and formatting
                            instruction = line.lstrip('0123456789.- ').strip()
                            if instruction:
                                instructions_section.append(instruction)
                
                # Get image for this recipe
                image_url = fetch_pexels_image(recipe_name)
                if not image_url:
                    image_url = get_local_food_image_fallback(ingredients)
                
                if recipe_name and (ingredients_section or instructions_section):
                    recipes.append({
                        'name': recipe_name,
                        'ingredients': ingredients_section if ingredients_section else [f"Use {', '.join(ingredients)} as main ingredients"],
                        'instructions': instructions_section if instructions_section else ["Prepare ingredients according to your preference"],
                        'image': image_url,
                        'difficulty': random.choice(['Easy', 'Medium', 'Easy'])  # Bias toward Easy
                    })
            
            except Exception as e:
                print(f"Error parsing recipe block: {e}")
                continue
        
        # Ensure we have at least 1 recipe
        if not recipes:
            recipes = [{
                'name': f'Simple {ingredients[0].title()} Dish',
                'ingredients': ingredients + ['Salt', 'Pepper', 'Oil'],
                'instructions': [
                    f'Prepare {ingredients[0]} by cleaning and cutting as needed',
                    'Heat oil in a pan over medium heat',
                    f'Cook {ingredients[0]} until tender',
                    'Season with salt and pepper to taste',
                    'Serve hot and enjoy!'
                ],
                'image': get_local_food_image_fallback(ingredients),
                'difficulty': 'Easy'
            }]
        
        # Limit to 3 recipes maximum
        recipes = recipes[:3]
        
        return jsonify({
            'success': True,
            'recipes': recipes
        })
        
    except Exception as e:
        print(f"Error in get_recipes: {e}")
        return jsonify({
            'success': False,
            'error': 'An error occurred while generating recipes. Please try again.'
        })

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    try:
        data = request.get_json()
        feedback_data = {
            'feedback': data.get('feedback', ''),
            'rating': data.get('rating', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # Log feedback to file
        os.makedirs('data', exist_ok=True)
        with open('data/feedback.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_data) + '\n')
        
        return jsonify({
            'success': True,
            'message': 'Thank you for your feedback!'
        })
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit feedback'
        })

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    print("🍳 Starting Enhanced Cooking Chatbot on Port 5001...")
    print("🌟 Features: Image-only recipes, scroll-based feedback, Pexels integration")
    print("🔗 Access at: http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)