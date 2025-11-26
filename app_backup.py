from flask import Flask, render_template, request, jsonify
import requests
import hashlib
import time
from werkzeug.utils import secure_filename
import random
import os
from datetime import datetime
import json
import os as _os

# Load environment variables FIRST before using them
try:
    from dotenv import load_dotenv
    # Load .env file from project root
    load_dotenv()
    print("[DEBUG] Loaded environment variables from .env file")
except Exception as e:
    print(f"[DEBUG] Could not load .env file: {e}")

# Pexels API configuration - loaded AFTER .env file
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY') or 'YOUR_PEXELS_API_KEY_HERE'  # Get from https://www.pexels.com/api/
PEXELS_API_URL = 'https://api.pexels.com/v1/search'

# Debug API key loading
if PEXELS_API_KEY and PEXELS_API_KEY != 'YOUR_PEXELS_API_KEY_HERE':
    print(f"[DEBUG] Pexels API key loaded: {PEXELS_API_KEY[:20]}...{PEXELS_API_KEY[-8:]}")
else:
    print("[DEBUG] Pexels API key not configured - using local fallbacks only")

app = Flask(__name__)
# Development: disable static file caching so browsers request fresh files while
# we're iterating. This prevents 304 responses from stale caches during testing.
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
# Enable debug and template auto-reload when running locally
app.config['TEMPLATES_AUTO_RELOAD'] = True


# Helper: validate if a recipe matches the requested difficulty level
def validate_recipe_difficulty(recipe, requested_difficulty):
    """
    Validate if a recipe matches the requested difficulty based on ingredient count and instruction complexity.
    
    Difficulty levels:
    - easy: 3-6 ingredients, 3-5 steps
    - moderate: 6-10 ingredients, 6-8 steps  
    - complex: 10+ ingredients, 8+ steps
    """
    if not requested_difficulty:
        return True
        
    ingredients = recipe.get('ingredients', [])
    instructions = recipe.get('instructions', '')
    
    # Count ingredients
    ingredient_count = len(ingredients) if isinstance(ingredients, list) else 0
    
    # Count instruction steps (split by common separators and filter non-empty)
    if isinstance(instructions, str):
        # Split by periods, newlines, or numbered steps
        steps = [step.strip() for step in instructions.replace('\n', '.').split('.') if step.strip()]
        # Filter out very short steps (likely incomplete splits) - more lenient filter
        steps = [step for step in steps if len(step) > 5]
        step_count = len(steps)
    else:
        step_count = 0
    
    requested_difficulty = requested_difficulty.lower()
    
    if requested_difficulty == 'easy':
        return 3 <= ingredient_count <= 6 and 3 <= step_count <= 5
    elif requested_difficulty == 'moderate':
        return 6 <= ingredient_count <= 10 and 6 <= step_count <= 8
    elif requested_difficulty == 'complex':
        return ingredient_count >= 10 and step_count >= 8
    
    return True  # Default: allow if difficulty not recognized

# Helper: extract main ingredients for better image searches
def extract_main_ingredient(recipe_data):
    """Extract the main ingredient from a recipe for better image searches."""
    try:
        ingredients = recipe_data.get('ingredients', [])
        if not ingredients:
            return recipe_data.get('name', '')
        
        # Priority list of main ingredients that make good image searches
        priority_ingredients = [
            'chicken', 'beef', 'pork', 'fish', 'salmon', 'shrimp', 'prawns',
            'paneer', 'tofu', 'egg', 'eggs',
            'pasta', 'spaghetti', 'noodles', 'rice', 'quinoa', 'bread',
            'chickpeas', 'lentils', 'beans',
            'tomato', 'broccoli', 'spinach', 'potato', 'carrot'
        ]
        
        # Look through ingredients for priority items
        for ingredient in ingredients:
            ingredient_lower = ingredient.lower()
            for priority in priority_ingredients:
                if priority in ingredient_lower:
                    return priority
        
        # If no priority ingredient found, extract the first substantial ingredient
        for ingredient in ingredients:
            # Remove quantities and common words
            clean_ingredient = ingredient.lower()
            # Remove common measurement words
            for word in ['cups', 'cup', 'tbsp', 'tsp', 'oz', 'g', 'kg', 'ml', 'l', 'cloves', 'pieces']:
                clean_ingredient = clean_ingredient.replace(word, '')
            # Remove numbers and common descriptors
            clean_ingredient = ''.join(c for c in clean_ingredient if not c.isdigit())
            clean_ingredient = clean_ingredient.replace('(', '').replace(')', '').replace(',', '')
            
            # Get the main word
            words = clean_ingredient.split()
            for word in words:
                word = word.strip()
                if len(word) > 3 and word not in ['fresh', 'dried', 'cooked', 'chopped', 'sliced', 'diced']:
                    return word
        
        # Fallback to recipe name
        return recipe_data.get('name', '')
    except Exception:
        return recipe_data.get('name', '')

# Helper: try searching Pexels for a relevant image based on main ingredient
def fetch_ingredient_image(recipe_data, cuisine_hint=''):
    """Fetch an image from Pexels based on the main ingredient of the recipe."""
    try:
        main_ingredient = extract_main_ingredient(recipe_data)
        recipe_name = recipe_data.get('name', '')
        
        # Create a targeted search query
        if main_ingredient and main_ingredient != recipe_name:
            query = f"{main_ingredient} {recipe_name}"
        else:
            query = recipe_name
            
        return fetch_fallback_image(query, cuisine_hint)
    except Exception:
        return fetch_fallback_image(recipe_data.get('name', ''), cuisine_hint)

# Helper: try searching Pexels for a relevant image and cache it locally.
def fetch_fallback_image(name_hint, cuisine_hint=''):
    try:
        query = (name_hint or cuisine_hint or '').strip()
        if not query:
            return '/static/images/quinoa_salad.jpg'
        # map certain dish names to better Pexels search queries (plated food, rice dishes)
        qmap = {
            'biryani': 'biryani rice plate',
            'goat biryani': 'goat biryani rice plate',
            'mutton biryani': 'mutton biryani rice plate',
            'pulav': 'pulav rice plate',
            'pulao': 'pulao rice plate',
            'pilaf': 'rice pilaf plate',
            'korma': 'korma curry plate'
        }
        qkey = query.lower()
        for k in qmap:
            if k in qkey:
                query = qmap[k]
                break
        images_dir = os.path.join(app.root_path, 'static', 'images')
        os.makedirs(images_dir, exist_ok=True)
        # load PEXELS key from env or .env
        PEXELS_KEY = _os.environ.get('PEXELS_API_KEY')
        if not PEXELS_KEY:
            possible = [os.path.join(app.root_path, '.env'), os.path.join(app.root_path, 'data', '.env')]
            for p in possible:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as fh:
                        for line in fh:
                            if line.strip().startswith('PEXELS_API_KEY'):
                                parts = line.split('=', 1)
                                if len(parts) > 1:
                                    PEXELS_KEY = parts[1].strip().strip('"').strip("'")
                                    _os.environ['PEXELS_API_KEY'] = PEXELS_KEY
                                    break
                if PEXELS_KEY:
                    break
        if not PEXELS_KEY:
            return '/static/images/quinoa_salad.jpg'
        headers = {'Authorization': PEXELS_KEY}
        params = {'query': query, 'per_page': 1}
        r = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params, timeout=8)
        if r.status_code != 200:
            return '/static/images/quinoa_salad.jpg'
        j = r.json()
        photos = j.get('photos') or []
        if not photos:
            return '/static/images/quinoa_salad.jpg'
        photo = photos[0]
        src = photo.get('src', {}).get('medium') or photo.get('src', {}).get('original')
        if not src:
            return '/static/images/quinoa_salad.jpg'
        # download and store
        safe = secure_filename((name_hint or query).lower().replace(' ', '_'))
        filename = safe + '_pexels.jpg'
        dest = os.path.join(images_dir, filename)
        if os.path.exists(dest) and os.path.getsize(dest) > 200:
            return '/static/images/' + filename
        try:
            resp = requests.get(src, timeout=8)
            if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('image'):
                with open(dest, 'wb') as fh:
                    fh.write(resp.content)
                return '/static/images/' + filename
        except Exception:
            return '/static/images/quinoa_salad.jpg'
    except Exception:
        return '/static/images/quinoa_salad.jpg'


# In-memory store for AI-generated recipes so details can be fetched by id
AI_RECIPES = {}

# Simple in-memory recipe "database" for prototype
RECIPES = [
    {
        "id": 1,
        "name": "Chana Masala",
        "cuisine": "Indian",
        "time": 30,
        "diet": "vegetarian",
        "difficulty": "moderate",
        "taste": "spicy",
        "image": "/static/images/chana_masala.jpg",
        "short": "Hearty chickpea curry with warming spices.",
        "ingredients": ["2 cups chickpeas (cooked)", "1 onion", "2 tomatoes", "ginger", "garlic", "cumin", "coriander", "garam masala"],
        "meal_types": ["lunch", "dinner"],
        "instructions": "Heat oil in pan. Sauté chopped onions until golden. Add ginger and garlic, cook 2 minutes. Add tomatoes and cook until soft. Add cumin, coriander and garam masala. Add chickpeas and simmer 15 minutes. Garnish with cilantro.",
        "nutrition": {"calories": 350, "protein": 15, "fat": 8, "carbs": 55}
    },
    {
        "id": 2,
        "name": "Paneer Butter Masala",
        "cuisine": "Indian",
        "time": 25,
        "diet": "vegetarian",
        "difficulty": "easy",
        "taste": "savory",
        "image": "/static/images/paneer_butter_masala.jpg",
        "short": "Creamy tomato gravy with soft paneer cubes.",
        "ingredients": ["200g paneer", "tomato puree", "cream", "butter", "onion"],
        "meal_types": ["lunch", "dinner"],
        "instructions": "Heat butter in pan. Cook tomato puree until thick. Add cream and simmer. Add paneer cubes gently. Season with salt.",
        "nutrition": {"calories": 450, "protein": 20, "fat": 30, "carbs": 18}
    },
    {
        "id": 3,
        "name": "Spaghetti Aglio e Olio",
        "cuisine": "Italian",
        "time": 20,
        "diet": "vegetarian",
        "difficulty": "easy",
        "taste": "savory",
        "image": "/static/images/spaghetti.jpg",
        "short": "Simple garlic and olive oil spaghetti.",
        "ingredients": ["spaghetti", "garlic", "olive oil", "chili flakes"],
        "meal_types": ["lunch", "dinner"],
        "instructions": "Boil pasta until al dente. Heat olive oil in pan. Fry sliced garlic until golden. Add chili flakes. Toss with drained pasta.",
        "nutrition": {"calories": 520, "protein": 12, "fat": 18, "carbs": 72}
    },
    {
        "id": 4,
        "name": "Mediterranean Quinoa Salad",
        "cuisine": "Mediterranean",
        "time": 15,
        "diet": "vegan",
        "difficulty": "easy",
        "taste": "tangy",
        "image": "/static/images/quinoa_salad.jpg",
        "short": "Fresh quinoa salad with lemony dressing.",
        "ingredients": ["quinoa", "cucumber", "tomato", "lemon", "olive oil"],
        "meal_types": ["lunch", "snack"],
        "instructions": "Cook quinoa according to package directions. Dice cucumber and tomato. Mix lemon juice with olive oil. Combine all ingredients and chill.",
        "nutrition": {"calories": 320, "protein": 8, "fat": 10, "carbs": 45}
    }
    ,
    {
        "id": 5,
        "name": "Kung Pao Chicken",
        "cuisine": "Chinese",
        "time": 25,
        "diet": "none",
        "difficulty": "moderate",
        "taste": "spicy",
        "image": "/static/images/spaghetti.jpg",
        "short": "Stir-fried chicken with peanuts and chilies.",
        "ingredients": ["chicken thighs", "peanuts", "dried chilies", "soy sauce", "garlic", "ginger", "green onions", "cornstarch"],
        "meal_types": ["lunch", "dinner"],
        "instructions": "Cut chicken into cubes and coat with cornstarch. Heat oil in wok. Stir-fry chicken until golden. Add garlic and ginger, cook 1 minute. Add dried chilies and peanuts. Add soy sauce mixture. Stir-fry 2 minutes. Garnish with green onions.",
        "nutrition": {"calories": 480, "protein": 32, "fat": 22, "carbs": 28}
    },
    {
        "id": 6,
        "name": "Tacos al Pastor (Quick)",
        "cuisine": "Mexican",
        "time": 30,
        "diet": "none",
        "difficulty": "moderate",
        "taste": "savory",
        "image": "/static/images/quinoa_salad.jpg",
        "short": "Quick marinated pork tacos with pineapple.",
        "ingredients": ["pork shoulder", "pineapple", "corn tortillas", "white onion", "cilantro", "achiote paste", "orange juice"],
        "meal_types": ["lunch", "dinner"],
        "instructions": "Marinate sliced pork with achiote paste and orange juice for 30 minutes. Heat grill pan to high heat. Cook pork 3-4 minutes per side. Dice pineapple and char on grill. Warm tortillas on griddle. Slice pork thinly. Assemble tacos with pork, pineapple, diced onion and cilantro.",
        "nutrition": {"calories": 430, "protein": 26, "fat": 18, "carbs": 36}
    }
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/cache-image', methods=['POST'])
def cache_image():
    """Fetch an external image URL and save it under static/images with a hashed filename.
    Returns a JSON object with {'local': '/static/images/<file>'} on success or {'error': '...'}.
    """
    data = request.get_json() or {}
    url = data.get('url')
    name_hint = data.get('name') or data.get('title') or ''
    cuisine_hint = data.get('cuisine') or ''
    if not url or not (url.startswith('http') or url.startswith('https')):
        # if there's no valid url, try to resolve by name/cuisine using normalize_image_value
        if name_hint or cuisine_hint:
            local = fetch_fallback_image(name_hint, cuisine_hint)
            return jsonify({'local': local})
        return jsonify({'error': 'invalid_url'}), 400
    try:
        # create a deterministic filename from the URL
        h = hashlib.sha1(url.encode('utf-8')).hexdigest()[:16]
        ext = os.path.splitext(url.split('?')[0])[1] or '.jpg'
        fname = secure_filename(f'cached_{h}{ext}')
        dest = os.path.join(os.path.dirname(__file__), 'static', 'images', fname)
        # if file already exists and non-empty, reuse it
        if os.path.exists(dest) and os.path.getsize(dest) > 200:
            return jsonify({'local': '/static/images/' + fname})
        # fetch the remote image with a short timeout
        try:
            r = requests.get(url, stream=True, timeout=8)
        except Exception:
            r = None
        if not r or r.status_code != 200 or not r.headers.get('Content-Type','').startswith('image'):
            # fallback: try to resolve via our normalization (which will try Pexels/Unsplash)
            try:
                local = fetch_fallback_image(name_hint, cuisine_hint)
                return jsonify({'local': local})
            except Exception as e:
                return jsonify({'error': 'fetch_failed', 'detail': str(e)}), 502
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(8192):
                if chunk:
                    f.write(chunk)
        # small wait to ensure filesystem sync on some platforms
        time.sleep(0.05)
        return jsonify({'local': '/static/images/' + fname})
    except Exception as e:
        return jsonify({'error': 'exception', 'detail': str(e)}), 500


# Fallback recipe generation when main OpenAI query fails or returns no results
def try_fallback_recipe_generation(ingredients, cuisine=None, difficulty=None, tokens=None):
    """
    Fallback OpenAI recipe generation with a simpler, more flexible prompt
    that focuses on generating recipes using the given ingredients.
    """
    try:
        OPENAI_KEY = _os.environ.get('OPENAI_API_KEY')
        if not OPENAI_KEY:
            return jsonify({'cards': []})
        
        # Create a simpler, more focused prompt
        cuisine_hint = f" in {cuisine} style" if cuisine else ""
        difficulty_hint = f" Keep it {difficulty}." if difficulty else " Keep it simple and accessible."
        
        prompt_text = f"""Generate 1-3 simple recipe ideas using these ingredients: {ingredients}{cuisine_hint}.{difficulty_hint}
        
Focus on practical, achievable recipes that home cooks can make. Include common pantry ingredients as needed.

Return ONLY a JSON array with this exact format:
[
  {{
    "id": 1,
    "name": "Recipe Name",
    "cuisine": "{cuisine or 'International'}",
    "short": "Brief description",
    "image": "recipe_image.jpg",
    "ingredients": ["ingredient 1", "ingredient 2", "etc"],
    "instructions": "Step 1. Do this. Step 2. Do that. Step 3. Finish.",
    "difficulty": "{difficulty or 'easy'}"
  }}
]"""

        print(f"[DEBUG] Fallback generation prompt: {prompt_text[:200]}...")
        
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        
        model_to_use = os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo'
        
        resp = client.chat.completions.create(
            model=model_to_use,
            messages=[{'role': 'user', 'content': prompt_text}],
            max_tokens=600,
            temperature=0.7
        )
        
        text = resp.choices[0].message.content
        print(f"[DEBUG] Fallback OpenAI response: {text[:200]}...")
        
        # Extract JSON array from response
        import re as _re
        m = _re.search(r"(\[\s*\{.*?\}\s*\])", text, _re.S)
        if m:
            raw = m.group(1)
            items = json.loads(raw)
            if isinstance(items, list) and items:
                cards = []
                for i, item in enumerate(items[:3]):
                    # Ensure required fields
                    if not item.get('name'):
                        item['name'] = f"Recipe with {ingredients}"
                    if not item.get('short'):
                        item['short'] = f"A delicious recipe using {ingredients}"
                    if not item.get('difficulty'):
                        item['difficulty'] = difficulty or 'easy'
                    if not item.get('cuisine'):
                        item['cuisine'] = cuisine or 'International'
                    
                    # Generate a proper image using Pexels API
                    image_path = fetch_pexels_image(item.get('name', ''), fallback_query=ingredients)
                    
                    # Store full recipe data
                    ai_id = item.get('id') or (2000 + i)
                    AI_RECIPES[ai_id] = item
                    
                    card = {
                        'id': ai_id,
                        'name': item['name'],
                        'image': image_path,
                        'short': item['short'][:140],
                        'matched_tokens': tokens or []
                    }
                    cards.append(card)
                
                print(f"[DEBUG] Fallback generation successful: {len(cards)} recipes")
                return jsonify({'cards': cards})
        
        print("[DEBUG] Fallback generation failed - no valid JSON found")
        return jsonify({'cards': []})
        
    except Exception as e:
        print(f"[DEBUG] Fallback generation error: {str(e)}")
        return jsonify({'cards': []})

def get_fallback_image_for_recipe(recipe, ingredients):
    """Get a fallback image for a recipe based on ingredients and recipe name"""
    try:
        # Extract main ingredient for image search
        name_lower = (recipe.get('name') or '').lower()
        ingredients_lower = ingredients.lower()
        
        # Map common ingredients/dishes to existing images
        image_mappings = {
            'chicken': 'chicken_curry_pexels.jpg',
            'paneer': 'paneer_butter_masala_pexels.jpg', 
            'egg': 'egg_scrambled_pexels.jpg',
            'rice': 'rice_vegetable_pulao_pexels.jpg',
            'pasta': 'pasta_penne_pexels.jpg',
            'potato': 'potato_vegetable_curry_pexels.jpg',
            'tomato': 'tomato_basil_pasta_pexels.jpg',
            'onion': 'onion_rings_pexels.jpg',
            'vegetable': 'vegetable_stir_fry_pexels.jpg',
            'lentil': 'lentil_soup_pexels.jpg',
            'quinoa': 'quinoa_salad.jpg'
        }
        
        # Check if any key ingredient matches our available images
        for ingredient, image in image_mappings.items():
            if ingredient in ingredients_lower or ingredient in name_lower:
                # Verify the image file exists
                image_path = os.path.join(app.root_path, 'static', 'images', image)
                if os.path.exists(image_path):
                    return f'/static/images/{image}'
        
        # Default fallback
        return '/static/images/quinoa_salad.jpg'
        
    except Exception:
        return '/static/images/quinoa_salad.jpg'

def fetch_pexels_image(recipe_name, fallback_query=None):
    """
    Fetch a high-quality food image from Pexels API with enhanced fallback logic
    
    Strategy:
    1. Search for exact recipe name (e.g., "Fish Pulusu")
    2. If no results, extract main ingredient and search (e.g., "Fish dish" or "Fish cooking") 
    3. If still no results, use generic food categories
    4. Always return an image - never leave blank
    
    Args:
        recipe_name (str): Name of the recipe to search for
        fallback_query (str): Additional fallback search term (usually ingredients)
    
    Returns:
        str: Image URL from Pexels or guaranteed local fallback path
    """
    def try_pexels_search(query, context=""):
        """Helper function to search Pexels with a given query"""
        try:
            headers = {'Authorization': PEXELS_API_KEY}
            params = {
                'query': query,
                'per_page': 1,
                'size': 'medium'
            }
            
            response = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=8)
            
            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', [])
                
                if photos:
                    photo = photos[0]
                    image_url = photo.get('src', {}).get('medium', '')
                    
                    if image_url:
                        print(f"[SUCCESS] Found Pexels image {context}: '{query}' -> {image_url[:60]}...")
                        return image_url
                        
            print(f"[DEBUG] No Pexels results {context}: '{query}'")
            return None
            
        except Exception as e:
            print(f"[ERROR] Pexels search failed {context}: {str(e)}")
            return None
    
    # Skip API calls if no key configured
    if not PEXELS_API_KEY or PEXELS_API_KEY == 'YOUR_PEXELS_API_KEY_HERE':
        print(f"[DEBUG] Pexels API key not configured, using local fallback")
        return get_local_food_image_fallback(recipe_name)
    
    print(f"[DEBUG] Starting image search for recipe: '{recipe_name}'")
    
    # Step 1: Try exact recipe name
    clean_recipe = recipe_name.strip().lower()
    result = try_pexels_search(clean_recipe, "(exact recipe name)")
    if result:
        return result
    
    # Step 2: Try recipe name with "dish" added
    result = try_pexels_search(f"{clean_recipe} dish", "(recipe + dish)")
    if result:
        return result
    
    # Step 3: Extract main ingredient and search
    # Common ingredient extraction patterns
    ingredient_keywords = [
        'fish', 'chicken', 'beef', 'pork', 'lamb', 'mutton', 'shrimp', 'prawn',
        'paneer', 'tofu', 'egg', 'potato', 'tomato', 'rice', 'pasta', 'noodles',
        'lentil', 'bean', 'chickpea', 'vegetable', 'mushroom', 'cheese'
    ]
    
    main_ingredient = None
    for ingredient in ingredient_keywords:
        if ingredient in clean_recipe:
            main_ingredient = ingredient
            break
    
    if main_ingredient:
        # Try ingredient with "cooking"
        result = try_pexels_search(f"{main_ingredient} cooking", "(ingredient + cooking)")
        if result:
            return result
            
        # Try ingredient with "dish"
        result = try_pexels_search(f"{main_ingredient} dish", "(ingredient + dish)")
        if result:
            return result
            
        # Try just the ingredient
        result = try_pexels_search(f"{main_ingredient} food", "(ingredient + food)")
        if result:
            return result
    
    # Step 4: Try fallback query if provided (usually ingredients list)
    if fallback_query and fallback_query.strip():
        clean_fallback = fallback_query.strip().lower()
        
        # Extract first ingredient from fallback
        fallback_words = clean_fallback.replace(',', ' ').split()
        for word in fallback_words:
            if len(word) > 3 and word in ingredient_keywords:
                result = try_pexels_search(f"{word} cooking", "(fallback ingredient)")
                if result:
                    return result
                break
    
    # Step 5: Generic food category fallbacks
    generic_searches = [
        "homemade food", "cooking food", "delicious meal", 
        "food dish", "kitchen cooking", "restaurant food"
    ]
    
    for generic in generic_searches:
        result = try_pexels_search(generic, "(generic food)")
        if result:
            return result
    
    print(f"[FALLBACK] All Pexels searches failed for '{recipe_name}', using local image")
    
    # Step 6: Guaranteed local fallback - never return empty
    return get_local_food_image_fallback(recipe_name)

def get_local_food_image_fallback(recipe_name):
    """
    Get a local food image based on recipe name/ingredients
    
    Args:
        recipe_name (str): Name of the recipe
    
    Returns:
        str: Local image path
    """
    try:
        recipe_lower = recipe_name.lower()
        
        # Enhanced mapping for better local fallbacks
        local_mappings = {
            # Indian dishes
            'curry': 'chicken_curry_pexels.jpg',
            'masala': 'paneer_butter_masala_pexels.jpg',
            'paneer': 'paneer_butter_masala_pexels.jpg',
            'chana': 'chana_masala.jpg',
            'chickpea': 'chana_masala.jpg',
            'biryani': 'rice_vegetable_pulao_pexels.jpg',
            'pulao': 'rice_vegetable_pulao_pexels.jpg',
            'rasam': 'tomato_tomato_rasam_pexels.jpg',
            
            # International dishes
            'pasta': 'pasta_penne_pexels.jpg',
            'spaghetti': 'pasta_penne_pexels.jpg',
            'noodles': 'pasta_penne_pexels.jpg',
            
            # Ingredients
            'chicken': 'chicken_curry_pexels.jpg',
            'beef': 'beef_beef_tacos_pexels.jpg',
            'fish': 'quinoa_salad.jpg',  # Generic fallback for fish
            'egg': 'quinoa_salad.jpg',
            'rice': 'rice_vegetable_pulao_pexels.jpg',
            'potato': 'potato_vegetable_curry_pexels.jpg',
            'tomato': 'tomato_tomato_rasam_pexels.jpg',
            'vegetable': 'vegetable_stir_fry_pexels.jpg',
            'salad': 'quinoa_salad.jpg',
            'soup': 'quinoa_salad.jpg',
            'lentil': 'quinoa_salad.jpg'
        }
        
        # Check for matches in recipe name
        for keyword, image in local_mappings.items():
            if keyword in recipe_lower:
                image_path = os.path.join(app.root_path, 'static', 'images', image)
                if os.path.exists(image_path):
                    print(f"[DEBUG] Using local fallback image for '{recipe_name}': {image}")
                    return f'/static/images/{image}'
        
        # Final fallback - check if spaghetti image exists, otherwise create default
        spaghetti_path = '/static/images/spaghetti.jpg'
        full_path = os.path.join(app.root_path, 'static', 'images', 'spaghetti.jpg')
        
        if os.path.exists(full_path):
            print(f"[DEBUG] Using default fallback: spaghetti.jpg")
            return spaghetti_path
        else:
            # Create default cooking image path - this should always exist
            return '/static/images/default_cooking.jpg'
        
    except Exception as e:
        print(f"[ERROR] Local fallback error: {str(e)}")
        return '/static/images/spaghetti.jpg'  # Ultimate fallback

def get_emergency_fallback_recipes(ingredients='chicken'):
    """
    Emergency fallback recipes that are always returned when all other systems fail.
    Ensures Grace never shows an error message to users.
    """
    print(f'[DEBUG] Using emergency fallback recipes for ingredients: {ingredients}')
    
    try:
        # Log the emergency fallback usage
        try:
            os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
            with open(os.path.join(app.root_path, 'data', 'recipe_requests.log'), 'a', encoding='utf-8') as f:
                f.write(f'{datetime.utcnow().isoformat()}Z -- EMERGENCY_FALLBACK -- ingredients: {ingredients}\n')
        except Exception:
            pass
        
        # Create ingredient-specific emergency recipes
        ingredients_lower = ingredients.lower() if ingredients else 'chicken'
        
        if 'chicken' in ingredients_lower:
            fallback_recipes = [
                {
                    'id': 9001,
                    'name': 'Simple Chicken Stir Fry',
                    'image': '/static/images/chicken_stir_fry_pexels.jpg',
                    'short': 'Quick and easy chicken stir fry with vegetables. Ready in 15 minutes.'
                },
                {
                    'id': 9002, 
                    'name': 'Chicken Rice Bowl',
                    'image': '/static/images/chicken_rice_bowl_pexels.jpg',
                    'short': 'Nutritious chicken and rice bowl with simple seasonings.'
                }
            ]
        elif 'pasta' in ingredients_lower:
            fallback_recipes = [
                {
                    'id': 9003,
                    'name': 'Classic Spaghetti',
                    'image': '/static/images/spaghetti.jpg', 
                    'short': 'Traditional spaghetti with tomato sauce and herbs.'
                },
                {
                    'id': 9004,
                    'name': 'Pasta Aglio e Olio',
                    'image': '/static/images/aglio_e_olio_pasta_pexels.jpg',
                    'short': 'Simple Italian pasta with garlic and olive oil.'
                }
            ]
        elif 'rice' in ingredients_lower:
            fallback_recipes = [
                {
                    'id': 9005,
                    'name': 'Vegetable Rice',
                    'image': '/static/images/rice_vegetable_pulao_pexels.jpg',
                    'short': 'Healthy vegetable rice with mixed spices.'
                },
                {
                    'id': 9006,
                    'name': 'Simple Fried Rice', 
                    'image': '/static/images/fried_rice_pexels.jpg',
                    'short': 'Quick fried rice with vegetables and soy sauce.'
                }
            ]
        elif any(veg in ingredients_lower for veg in ['vegetable', 'broccoli', 'carrot', 'potato']):
            fallback_recipes = [
                {
                    'id': 9007,
                    'name': 'Mixed Vegetable Curry',
                    'image': '/static/images/vegetable_curry_pexels.jpg',
                    'short': 'Hearty vegetable curry with aromatic spices.'
                },
                {
                    'id': 9008,
                    'name': 'Vegetable Stir Fry',
                    'image': '/static/images/vegetable_stir_fry_pexels.jpg',
                    'short': 'Colorful mixed vegetables stir-fried to perfection.'
                }
            ]
        else:
            # Generic fallback for any ingredient
            fallback_recipes = [
                {
                    'id': 9009,
                    'name': 'Quick & Easy Recipe',
                    'image': '/static/images/quinoa_salad.jpg',
                    'short': f'A delicious recipe using {ingredients} with simple preparation.'
                },
                {
                    'id': 9010,
                    'name': 'Healthy Bowl',
                    'image': '/static/images/healthy_bowl_pexels.jpg', 
                    'short': f'Nutritious bowl featuring {ingredients} and fresh ingredients.'
                }
            ]
        
        # Ensure image paths exist, use quinoa_salad.jpg as ultimate fallback
        for recipe in fallback_recipes:
            image_path = recipe['image']
            if not image_path.startswith(('/static/', 'http')):
                recipe['image'] = '/static/images/quinoa_salad.jpg'
            elif image_path.startswith('/static/'):
                # Check if file exists, use fallback if not
                full_path = os.path.join(app.root_path, image_path.lstrip('/'))
                if not os.path.exists(full_path):
                    recipe['image'] = '/static/images/quinoa_salad.jpg'
        
        return jsonify({'cards': fallback_recipes[:2]})  # Return 2 fallback recipes
        
    except Exception as e:
        print(f'[ERROR] Emergency fallback failed: {str(e)}')
        # Ultimate last resort - basic recipe cards
        return jsonify({
            'cards': [
                {
                    'id': 9999,
                    'name': 'Simple Recipe',
                    'image': '/static/images/quinoa_salad.jpg',
                    'short': 'A basic recipe you can make with available ingredients.'
                }
            ]
        })

@app.route('/suggest', methods=['POST'])
@app.route('/api/recipes', methods=['POST'])
def suggest_recipes():
    try:
        data = request.json or {}
        ingredients = data.get('ingredients', '')
        broaden = data.get('broaden', False)
        cuisine = (data.get('cuisine') or '').strip().lower()
        diet = (data.get('diet') or '').strip().lower()
        difficulty = (data.get('difficulty') or '').strip().lower()
        taste = (data.get('taste') or '').strip().lower()
        
        # Enhanced logging for debugging
        print(f'\n[DEBUG] suggest_recipes called via {request.path}')
        print(f'[DEBUG] Request data: {data}')
        print(f'[DEBUG] Processed - ingredients: "{ingredients}", cuisine: "{cuisine}", difficulty: "{difficulty}"')
        
        # Log to file for persistent debugging
        try:
            os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
            with open(os.path.join(app.root_path, 'data', 'recipe_requests.log'), 'a', encoding='utf-8') as f:
                f.write(f'{datetime.utcnow().isoformat()}Z -- REQUEST -- {request.path} -- {json.dumps(data)}\n')
        except Exception as log_err:
            print(f'[DEBUG] Failed to log request: {log_err}')
    
        
        # Continue with rest of function logic...
        # Basic filtering by attributes (cuisine/diet/difficulty/taste)
        import re

    # helper: token-in-text used for both OpenAI validation and local matching
    def token_in_text(tok, text):
        # consider simple variants (singular/plural) without external libs
        variants = set()
        variants.add(tok)
        variants.add(tok + 's')
        variants.add(tok + 'es')
        # y -> ies and reverse
        if tok.endswith('y'):
            variants.add(tok[:-1] + 'ies')
        if tok.endswith('ies'):
            variants.add(tok[:-3] + 'y')
        # if token looks plural, add singular guess
        if tok.endswith('s') and len(tok) > 1:
            variants.add(tok[:-1])
            if tok.endswith('es'):
                variants.add(tok[:-2])

        for v in variants:
            if re.search(r"\b" + re.escape(v) + r"\b", text):
                return True
        return False

    # A more robust matcher that removes punctuation and normalizes whitespace
    def normalized_contains(tok, text):
        try:
            _nt = re.sub(r"[^a-z0-9\s]", ' ', (text or '').lower())
            return bool(re.search(r"\b" + re.escape(tok.lower()) + r"\b", _nt))
        except Exception:
            return False

    # Normalize image values returned by AI to point to our static images when possible.
    def normalize_image_value(img_val, cuisine=None, name_hint=None):
        try:
            if not img_val:
                 return '/static/images/quinoa_salad.jpg'
              # Use the recipe name as a hint when fetching a fallback image so
              # Pexels/Unsplash queries are specific to this dish and avoid
              # returning the same generic photo for multiple cards.
            img_val = (img_val or '').strip()
            # If AI returned a full URL, accept it
            if img_val.lower().startswith('http://') or img_val.lower().startswith('https://'):
                 return img_val
              # prefer using the recipe name as the query when attempting
              # to fetch a fallback image so results are dish-specific
            # If already a static path, use as-is (ensure it begins with /)
            if img_val.startswith('/'):
                static_rel = img_val.lstrip('/')
                static_file = os.path.join(app.root_path, static_rel)
                if os.path.exists(static_file):
                    return '/' + static_rel.replace('\\', '/')
            # Otherwise treat it as a filename; sanitize and try to find a match in static/images
            images_dir = os.path.join(app.root_path, 'static', 'images')
            base = os.path.basename(img_val).lower()
            # normalize name (remove spaces)
            base_norm = os.path.splitext(base)[0].replace(' ', '_')
            # scan images dir for best match
            try:
                files = os.listdir(images_dir)
            except Exception:
                files = []
            # quick keyword-based mapping to common images
            try:
                k = base_norm
                if 'salad' in k:
                    if 'quinoa_salad.jpg' in files:
                        return '/static/images/quinoa_salad.jpg'
                if 'paneer' in k:
                    if 'paneer_butter_masala.jpg' in files:
                        return '/static/images/paneer_butter_masala.jpg'
                if 'chana' in k or 'chickpea' in k or 'chickpeas' in k:
                    if 'chana_masala.jpg' in files:
                        return '/static/images/chana_masala.jpg'
                if 'lentil' in k or 'soup' in k:
                    if 'quinoa_salad.jpg' in files:
                        return '/static/images/quinoa_salad.jpg'
                if 'spaghetti' in k or 'pasta' in k:
                    if 'spaghetti.jpg' in files:
                        return '/static/images/spaghetti.jpg'
            except Exception:
                pass
            for f in files:
                name_noext = os.path.splitext(f)[0].lower().replace(' ', '_')
                if name_noext == base_norm:
                    return '/static/images/' + f
            # fuzzy match: pick the file with the highest similarity
            try:
                import difflib
                scores = []
                for f in files:
                    name_noext = os.path.splitext(f)[0].lower().replace(' ', '_')
                    ratio = difflib.SequenceMatcher(None, base_norm, name_noext).ratio()
                    scores.append((ratio, f))
                if scores:
                    scores.sort(reverse=True)
                    best_ratio, best_file = scores[0]
                    # accept best match only if similarity reasonable
                    if best_ratio > 0.5:
                        return '/static/images/' + best_file
            except Exception:
                pass
            # try common extensions if basename had no ext
            if '.' not in base:
                for ext in ('.jpg', '.jpeg', '.png', '.webp'):
                    candidate = base + ext
                    if candidate in files:
                        return '/static/images/' + candidate
            # if no match, try a cuisine-based fallback if provided
            try:
                if cuisine:
                    c = str(cuisine).strip().lower()
                    if 'indian' in c:
                        # prefer paneer or chana images for Indian
                        for pref in ('paneer_butter_masala.jpg', 'chana_masala.jpg'):
                            if pref in files:
                                return '/static/images/' + pref
                    if 'ital' in c or 'italian' in c:
                        if 'spaghetti.jpg' in files:
                            return '/static/images/spaghetti.jpg'
                    if 'mediterr' in c or 'med' in c:
                        if 'quinoa_salad.jpg' in files:
                            return '/static/images/quinoa_salad.jpg'
                    if 'mex' in c or 'mexican' in c:
                        if 'quinoa_salad.jpg' in files:
                            return '/static/images/quinoa_salad.jpg'
                    if 'chin' in c or 'chinese' in c:
                        if 'spaghetti.jpg' in files:
                            return '/static/images/spaghetti.jpg'
            except Exception:
                pass
            # if still no match, try to fetch a relevant image from Unsplash Source using name_hint or base_norm
            query = name_hint or base_norm
            if query:
                try:
                    import requests
                    from urllib.parse import quote_plus
                    q = quote_plus(query)
                    unsplash_url = f'https://source.unsplash.com/600x400/?{q}'
                    # attempt to download the image (will follow redirect to an image)
                    resp = requests.get(unsplash_url, timeout=8)
                    if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('image'):
                        # save to static/images with a safe filename
                        safe_name = base_norm if base_norm else quote_plus(query).lower()
                        filename = safe_name + '.jpg'
                        # ensure uniqueness
                        dest = os.path.join(images_dir, filename)
                        # if file exists, reuse; otherwise write
                        if not os.path.exists(dest):
                            try:
                                with open(dest, 'wb') as fh:
                                    fh.write(resp.content)
                            except Exception:
                                pass
                        if os.path.exists(dest):
                            return '/static/images/' + os.path.basename(dest)
                except Exception:
                    pass

            # If Unsplash didn't find anything, try Pexels (if API key present)
            try:
                PEXELS_KEY = _os.environ.get('PEXELS_API_KEY')
                if not PEXELS_KEY:
                    possible = [os.path.join(app.root_path, '.env'), os.path.join(app.root_path, 'data', '.env')]
                    for p in possible:
                        if os.path.exists(p):
                            with open(p, 'r', encoding='utf-8') as fh:
                                for line in fh:
                                    if line.strip().startswith('PEXELS_API_KEY'):
                                        parts = line.split('=', 1)
                                        if len(parts) > 1:
                                            PEXELS_KEY = parts[1].strip().strip('"').strip("'")
                                            _os.environ['PEXELS_API_KEY'] = PEXELS_KEY
                                            break
                        if PEXELS_KEY:
                            break
                if PEXELS_KEY and query:
                    try:
                        import requests
                        from urllib.parse import quote_plus
                        headers = {'Authorization': PEXELS_KEY}
                        params = {'query': query, 'per_page': 1}
                        r = requests.get('https://api.pexels.com/v1/search', headers=headers, params=params, timeout=8)
                        if r.status_code == 200:
                            j = r.json()
                            photos = j.get('photos') or []
                            if photos:
                                photo = photos[0]
                                src = photo.get('src', {}).get('medium') or photo.get('src', {}).get('original')
                                if src:
                                    # download and cache
                                    try:
                                        resp = requests.get(src, timeout=8)
                                        if resp.status_code == 200 and resp.headers.get('Content-Type','').startswith('image'):
                                            safe_name = base_norm if base_norm else quote_plus(query).lower()
                                            filename = safe_name + '_pexels.jpg'
                                            dest = os.path.join(images_dir, filename)
                                            if not os.path.exists(dest):
                                                with open(dest, 'wb') as fh:
                                                    fh.write(resp.content)
                                            if os.path.exists(dest):
                                                return '/static/images/' + os.path.basename(dest)
                                    except Exception:
                                        pass
                    except Exception:
                        pass
            except Exception:
                pass
            # final fallback: neutral image
            return '/static/images/quinoa_salad.jpg'
        except Exception:
            return '/static/images/quinoa_salad.jpg'

    # Ensure every returned card has a usable image path (absolute static path or http url)
    def ensure_image_path(img, name_hint=None, cuisine_hint=None):
        try:
            if not img:
                return '/static/images/quinoa_salad.jpg'
            if isinstance(img, str) and (img.startswith('/') or img.lower().startswith('http')):
                return img
            # try to normalize using existing helper with name hint
            resolved = normalize_image_value(img, cuisine_hint, name_hint)
            if resolved and (resolved.startswith('/') or resolved.lower().startswith('http')):
                return resolved
            # fallback: keyword map using name_hint
            if name_hint:
                nk = name_hint.lower()
                images_dir = os.path.join(app.root_path, 'static', 'images')
                files = os.listdir(images_dir) if os.path.exists(images_dir) else []
                if 'paneer' in nk and 'paneer_butter_masala.jpg' in files:
                    return '/static/images/paneer_butter_masala.jpg'
                if 'chana' in nk or 'chickpea' in nk or 'chickpeas' in nk:
                    if 'chana_masala.jpg' in files:
                        return '/static/images/chana_masala.jpg'
                if 'lentil' in nk or 'soup' in nk:
                    if 'quinoa_salad.jpg' in files:
                        return '/static/images/quinoa_salad.jpg'
                if 'spaghetti' in nk or 'pasta' in nk:
                    if 'spaghetti.jpg' in files:
                        return '/static/images/spaghetti.jpg'
            return '/static/images/quinoa_salad.jpg'
        except Exception:
            return '/static/images/quinoa_salad.jpg'

    # compute ingredient tokens early so OpenAI validation can use them
    tokens = []
    if ingredients:
        tokens = [t.strip() for t in re.split(r"\W+", ingredients.lower()) if t.strip()]
    print('    [DEBUG] tokens:', tokens)

    # Reload .env (if present) so updates to .env are picked up at request time.
    try:
        from dotenv import load_dotenv as _load_dotenv
        _load_dotenv()
        dotenv_data_path = os.path.join(os.path.dirname(__file__), 'data', '.env')
        if os.path.exists(dotenv_data_path):
            _load_dotenv(dotenv_data_path)
    except Exception:
        pass

    # If OPENAI_API_KEY is present, try to ask OpenAI for recipe suggestions first.
    OPENAI_KEY = _os.environ.get('OPENAI_API_KEY')
    # If not in environment, try to read from common .env files (project root or data/.env)
    if not OPENAI_KEY:
        try:
            possible = [os.path.join(app.root_path, '.env'), os.path.join(app.root_path, 'data', '.env')]
            for p in possible:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as fh:
                        for line in fh:
                            if line.strip().startswith('OPENAI_API_KEY'):
                                parts = line.split('=', 1)
                                if len(parts) > 1:
                                    OPENAI_KEY = parts[1].strip().strip('\"').strip("\'")
                                    # also set in os.environ so later imports can see it
                                    _os.environ['OPENAI_API_KEY'] = OPENAI_KEY
                                    break
                if OPENAI_KEY:
                    break
        except Exception:
            pass
    # debug: print whether OPENAI key is present (masked) to aid diagnosis
    if OPENAI_KEY:
        print('[DEBUG] OPENAI_API_KEY present, loaded and masked:', OPENAI_KEY[:6] + '...' + OPENAI_KEY[-4:])
    else:
        print('[DEBUG] OPENAI_API_KEY not found in environment')
    if OPENAI_KEY:
        try:
            # Compose prompt
            prompt = {
                'ingredients': ingredients,
                'cuisine': cuisine,
                'diet': diet,
                'difficulty': difficulty,
                'meal': data.get('meal'),
                'broaden': bool(broaden)
            }
            system = (
                "You are a helpful cooking assistant. Respond ONLY with a JSON array (no explanatory text). "
                "Return up to 3 recipe objects. Each object should include the fields:"
                " id (number), name (string), cuisine (string), short (string), image (string; optional),"
                " ingredients (array of strings), instructions (string), nutrition (object with calories, protein, fat, carbs), difficulty (string)."
                " IMPORTANT: Follow these difficulty guidelines strictly:"
                " - For 'easy': Use 3-6 ingredients max and 3-5 simple steps. Keep instructions concise."
                " - For 'moderate': Use 6-10 ingredients and 6-8 detailed steps. Include more cooking techniques."
                " - For 'complex': Use 10+ ingredients and 8+ comprehensive steps. Include advanced techniques and timing."
                " Always include the difficulty field matching the requested difficulty level."
            )
            user = f"Suggest recipes for this criteria: {json.dumps(prompt)}. Return only JSON array."

            # prefer a modern ChatCompletion model but allow environment to pick; fallback if unknown
            # choose model: prefer OPENAI_MODEL env var, otherwise fall back to a safe default
            model_to_use = os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo'

            # Use the modern v1 OpenAI SDK client only (strict OpenAI-only behavior)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=OPENAI_KEY)
                resp = client.chat.completions.create(
                    model=model_to_use,
                    messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
                    max_tokens=800,
                    temperature=0.6
                )
                # robust extraction from v1-like response
                try:
                    text = resp.choices[0].message.content
                except Exception:
                    try:
                        text = resp.choices[0].message[0].content
                    except Exception:
                        text = str(resp)
                print('[DEBUG] OpenAI assistant text snippet:', (text or '')[:300])
                # Also persist the full assistant text to a debug log for inspection
                try:
                    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
                    with open(os.path.join(app.root_path, 'data', 'openai_responses.log'), 'a', encoding='utf-8') as _of:
                        _of.write(datetime.utcnow().isoformat() + 'Z -- ' + (text or '').replace('\n', ' ') + '\n---\n')
                except Exception as _e:
                    print('[DEBUG] Failed to write OpenAI assistant text to log:', str(_e))
            except Exception as e_v1:
                print('[DEBUG] OpenAI v1 client call failed or skipped:', str(e_v1))
                # Strict OpenAI-only: return empty on failure
                return jsonify({'cards': []})

            # extract the first JSON array found in the assistant response using regex
            import re as _re
            m = _re.search(r"(\[\s*\{.*?\}\s*\])", text, _re.S)
            if m:
                raw = m.group(1)
                try:
                    items = json.loads(raw)
                    if isinstance(items, list) and items:
                        # validate returned items against filters - more lenient approach
                        def item_matches_filters(it):
                            try:
                                # More lenient filtering: prefer exact matches but don't reject everything
                                score = 0  # scoring system for better matching
                                reasons = []
                                
                                if not bool(broaden):
                                    # cuisine: prefer exact match but don't reject if no match
                                    if cuisine and it.get('cuisine'):
                                        if it.get('cuisine', '').strip().lower() == cuisine:
                                            score += 2  # exact cuisine match bonus
                                        else:
                                            score -= 1  # slight penalty for cuisine mismatch
                                            reasons.append(f"cuisine mismatch ({it.get('cuisine')!r} != {cuisine!r})")
                                    
                                    # difficulty: prefer matching but allow near matches
                                    if difficulty:
                                        # First check if difficulty field matches exactly
                                        if it.get('difficulty') and it.get('difficulty', '').strip().lower() == difficulty:
                                            score += 2  # exact difficulty match bonus
                                        else:
                                            # Check complexity requirements more leniently
                                            if validate_recipe_difficulty(it, difficulty):
                                                score += 1  # complexity requirements met
                                            else:
                                                score -= 1  # slight penalty for complexity mismatch
                                                reasons.append(f"doesn't meet {difficulty} complexity requirements")
                                    
                                    # diet: only enforce when both sides specify diet
                                    if diet and diet != 'none' and it.get('diet'):
                                        if diet in (it.get('diet','') or '').lower():
                                            score += 1  # diet match bonus
                                        else:
                                            score -= 1  # diet mismatch penalty
                                            reasons.append(f"diet mismatch ({it.get('diet')!r} does not include {diet!r})")
                                    
                                    # meal: check meal_types array if present
                                    if data.get('meal') and it.get('meal_types'):
                                        sel = data.get('meal').lower()
                                        mts = [m.lower() for m in (it.get('meal_types') or [])]
                                        if mts and sel in mts:
                                            score += 1  # meal type match bonus
                                        else:
                                            score -= 1  # meal type mismatch penalty
                                            reasons.append(f"meal_types do not include {sel}")
                                
                                # Accept items with score >= -2 (allow some mismatches but not total mismatches)
                                if score >= -2:
                                    if reasons:
                                        print(f"[DEBUG] OpenAI item '{it.get('name')}' accepted with score {score}: {', '.join(reasons)}")
                                    else:
                                        print(f"[DEBUG] OpenAI item '{it.get('name')}' accepted with score {score}: perfect match")
                                    return True
                                else:
                                    print(f"[DEBUG] OpenAI item '{it.get('name')}' rejected with score {score}: {', '.join(reasons)}")
                                    return False
                                    
                            except Exception as e:
                                print(f"[DEBUG] Error in item_matches_filters: {e}")
                                return True  # If error, accept the item rather than reject it

                        accepted = []
                        scored_items = []  # for sorting by score if needed
                        for it in items[:6]:
                            if item_matches_filters(it):
                                # compute matched tokens for the item
                                mt = []
                                if tokens:
                                    txt_fields = ' '.join([it.get('name',''), it.get('short','')] + (it.get('ingredients') or [])).lower()
                                    print(f"[DEBUG] OpenAI item '{it.get('name')}' txt_fields: {txt_fields}")
                                    # also append debug to log file
                                    try:
                                        with open(os.path.join(app.root_path, 'data', 'openai_responses.log'), 'a', encoding='utf-8') as _of2:
                                            _of2.write(datetime.utcnow().isoformat() + 'Z -- ITEM_DEBUG -- ' + it.get('name','') + ' -- ' + txt_fields + '\n')
                                    except Exception:
                                        pass
                                    for tok in tokens:
                                        res = token_in_text(tok, txt_fields)
                                        if not res:
                                            # fallback to a normalized check (remove punctuation/newlines)
                                            res = normalized_contains(tok, txt_fields)
                                        print(f"[DEBUG] checking token '{tok}' in item '{it.get('name')}': {res}")
                                        if res:
                                            mt.append(tok)
                                
                                # More lenient ingredient matching: require at least one token match OR accept if no ingredient tokens provided
                                if tokens and not mt and not broaden:
                                    print(f"[DEBUG] OpenAI item '{it.get('name')}' has no matched ingredient tokens but accepting due to lenient filtering")
                                    # Continue processing instead of rejecting - maybe it's a related recipe
                                
                                # Always try to get a good image, use Pexels API first
                                raw_img = it.get('image') or ''
                                # If AI provided an absolute URL, keep it as-is
                                if isinstance(raw_img, str) and (raw_img.lower().startswith('http://') or raw_img.lower().startswith('https://')):
                                    normalized_img = raw_img
                                else:
                                    # Use Pexels API to get a high-quality food image
                                    normalized_img = fetch_pexels_image(it.get('name', ''), fallback_query=ingredients)
                                
                                # Final safety check - ensure we always have a valid image path
                                if not normalized_img or not (normalized_img.startswith('/') or normalized_img.lower().startswith('http')):
                                    normalized_img = '/static/images/quinoa_salad.jpg'
                                
                                # Save the full AI item so we can return detail later when card is clicked
                                ai_id = it.get('id') or random.randint(1000, 9999)
                                AI_RECIPES[ai_id] = it
                                card = {
                                    'id': ai_id,
                                    'name': it.get('name', 'Recipe'),
                                    'image': normalized_img,
                                    'short': (it.get('short') or '')[:140],
                                    'matched_tokens': mt
                                }
                                print(f"[DEBUG] OpenAI item accepted: name={it.get('name')}, cuisine={it.get('cuisine')}, matched_tokens={mt}")
                                accepted.append(card)

                        if accepted:
                            # ensure images are usable paths/URLs for frontend
                            for c in accepted:
                                try:
                                    img = c.get('image') or ''
                                    # If we already have a good path or URL, keep it
                                    if img and (img.startswith('/') or img.lower().startswith('http')):
                                        continue
                                    # Otherwise use fallback
                                    c['image'] = '/static/images/quinoa_salad.jpg'
                                except Exception:
                                    c['image'] = '/static/images/quinoa_salad.jpg'
                            print('[DEBUG] OpenAI returned items and passed filter validation; using them')
                            return jsonify({'cards': accepted[:3]})
                        else:
                            print('[DEBUG] OpenAI returned items but none passed validation; trying fallback generation')
                            # FALLBACK: Try a simpler prompt focused just on ingredients
                            return try_fallback_recipe_generation(ingredients, cuisine, difficulty, tokens)
                except Exception as e:
                    print('[DEBUG] Failed to parse JSON from OpenAI response:', str(e))
                    # Try fallback generation instead of returning empty
                    return try_fallback_recipe_generation(ingredients, cuisine, difficulty, tokens)
            else:
                print('[DEBUG] No JSON array found in OpenAI response; trying fallback generation')
                return try_fallback_recipe_generation(ingredients, cuisine, difficulty, tokens)
        except Exception as e:
            print('[DEBUG] OpenAI call failed or skipped:', str(e))
            # Try fallback generation instead of returning empty
            return try_fallback_recipe_generation(ingredients, cuisine, difficulty, tokens)

    # Local matching is only run when there is no OpenAI API key present.
    if not OPENAI_KEY:
        candidates = []
        for r in RECIPES:
            print('  [DEBUG] evaluating recipe', r['name'])
            # strict cuisine filter unless user explicitly asked to broaden
            if cuisine and not broaden and cuisine not in ('', 'something else', 'other') and r['cuisine'].lower() != cuisine:
                print('    [DEBUG] cuisine mismatch -> skip')
                continue
            # diet filter (ignore if user said 'none' or left blank)
            if diet and not broaden and diet != 'none' and diet not in r['diet'].lower():
                print('    [DEBUG] diet mismatch -> skip')
                continue
            # difficulty filter (validate complexity requirements)
            if difficulty and not broaden:
                if not validate_recipe_difficulty(r, difficulty):
                    print(f'    [DEBUG] difficulty complexity mismatch -> skip (requested: {difficulty})')
                    continue
            if taste and not broaden and r['taste'].lower() != taste:
                print('    [DEBUG] taste mismatch -> skip')
                continue
            # meal type filter
            if data.get('meal') and not broaden:
                sel_meal = data.get('meal').lower()
                if 'meal_types' in r and sel_meal not in [m.lower() for m in r.get('meal_types', [])]:
                    print(f"    [DEBUG] meal type {sel_meal} not in recipe meal_types -> skip")
                    continue
            # compute ingredient match score (only check recipe ingredients for strictness)
            if tokens:
                match_count = 0
                matched_tokens = []
                for tok in tokens:
                    found = False
                    for ing in r.get('ingredients', []):
                        if token_in_text(tok, ing.lower()):
                            found = True
                            break
                    if found:
                        match_count += 1
                        matched_tokens.append(tok)
                        print(f"    [DEBUG] token '{tok}' matched in ingredient for {r['name']}")
                    else:
                        print(f"    [DEBUG] token '{tok}' NOT matched in ingredients for {r['name']}")
                candidates.append((r, match_count, matched_tokens))
            else:
                # no ingredient constraints -> candidate with score 0 and no matched tokens
                candidates.append((r, 0, []))

        # prefer exact matches where all tokens are found in recipe ingredients
        # build helpers mapping from recipe -> matched_tokens
        exact_matches = [item[0] for item in candidates if tokens and (len(item) > 1 and item[1] == len(tokens))]
        if exact_matches:
            selected = exact_matches[:3]
            # collect matched tokens for exact matches from candidates
            selected_mtokens = {}
            for item in candidates:
                r = item[0]
                mt = item[2] if len(item) > 2 else []
                if r in selected:
                    selected_mtokens[r['id']] = mt
            print('[DEBUG] exact ingredient matches found:', [r['name'] for r in selected])
        else:
            # if no exact matches, return best partial matches (score>0) ordered by coverage
            partials = [item for item in candidates if (len(item) > 1 and item[1] > 0)]
            partials.sort(key=lambda x: x[1], reverse=True)
            selected = [item[0] for item in partials[:3]]
            selected_mtokens = {item[0]['id']: (item[2] if len(item) > 2 else []) for item in partials[:3]}
            if selected:
                print('[DEBUG] returning partial matches ordered by coverage:', [r['name'] for r in selected])
            else:
                # If no partials found under the strict filters, optionally try a relaxed ingredient-only search
                # Only run the relaxed search when the user requested broaden=True; otherwise avoid returning
                # unrelated recipes that match ingredients but not other filters.
                relaxed = []
                if broaden:
                    for r in RECIPES:
                        match_count = 0
                        matched_tokens = []
                        for tok in tokens:
                            for ing in r.get('ingredients', []):
                                if token_in_text(tok, ing.lower()):
                                    match_count += 1
                                    matched_tokens.append(tok)
                                    break
                        if match_count > 0:
                            relaxed.append((r, match_count, matched_tokens))
                    relaxed.sort(key=lambda x: x[1], reverse=True)
                    if relaxed:
                        selected = [item[0] for item in relaxed[:3]]
                        selected_mtokens = {item[0]['id']: (item[2] if len(item) > 2 else []) for item in relaxed[:3]}
                        print('[DEBUG] relaxed ingredient-only matches (broaden):', [r['name'] for r in selected])
                else:
                    # no partial matches by ingredient tokens
                    # Fallback 1: match tokens in recipe name/short (helpful when user typed dish names)
                    name_matches = []
                    if tokens:
                        for item in candidates:
                            r = item[0]
                            name_short = ' '.join([r.get('name', ''), r.get('short', '')]).lower()
                            for tok in tokens:
                                if re.search(r"\b" + re.escape(tok) + r"\b", name_short):
                                    name_matches.append(r)
                                    break
                    if name_matches:
                        selected = name_matches[:3]
                        # for name matches, matched tokens are whichever tokens matched name/short
                        selected_mtokens = {}
                        for r in selected:
                            matched = []
                            name_short = ' '.join([r.get('name', ''), r.get('short', '')]).lower()
                            for tok in tokens:
                                if re.search(r"\b" + re.escape(tok) + r"\b", name_short):
                                    matched.append(tok)
                            selected_mtokens[r['id']] = matched
                        print('[DEBUG] fallback matched by name/short:', [r['name'] for r in selected])
                    else:
                        # Fallback 2: return top recipes in the chosen cuisine if any, otherwise top recipes overall
                        cuisine_candidates = [item[0] for item in candidates if (not cuisine) or item[0]['cuisine'].lower() == cuisine]
                        if cuisine_candidates:
                            selected = cuisine_candidates[:3]
                            selected_mtokens = {r['id']: [] for r in selected}
                            print('[DEBUG] fallback top cuisine recipes:', [r['name'] for r in selected])
                        else:
                            # final fallback: return top recipes from RECIPES
                            selected = RECIPES[:3]
                            selected_mtokens = {r['id']: [] for r in selected}
                            print('[DEBUG] final fallback to top recipes:', [r['name'] for r in selected])
    # If the user provided ingredient tokens but we still have no selected recipes,
    # return an empty result set rather than falling back to top recipes. This
    # avoids showing unrelated default cards which confuse users.
    if tokens and (not selected):
        print('[DEBUG] no matches for provided ingredients; returning empty cards')
        return jsonify({'cards': []})

    # build cards with matched tokens info (recompute per-card to be deterministic)
    cards = []
    for r in selected:
        card = {k: r[k] for k in ('id', 'name', 'image', 'short')}
        matched = []
        if tokens:
            # check ingredients first
            for tok in tokens:
                found = False
                for ing in r.get('ingredients', []):
                    if token_in_text(tok, ing.lower()):
                        matched.append(tok)
                        found = True
                        break
                if not found:
                    # also check name/short as fallback
                    name_short = ' '.join([r.get('name', ''), r.get('short', '')]).lower()
                    if re.search(r"\b" + re.escape(tok) + r"\b", name_short):
                        matched.append(tok)
        card['matched_tokens'] = matched
        # Prefer existing local image for this recipe; only fetch a fallback if none exists
        try:
            img = r.get('image') or ''
            # Keep absolute URLs
            if isinstance(img, str) and (img.lower().startswith('http://') or img.lower().startswith('https://')):
                card['image'] = img
            elif isinstance(img, str) and img.startswith('/'):
                candidate = os.path.join(app.root_path, img.lstrip('/'))
                if os.path.exists(candidate) and os.path.getsize(candidate) > 100:
                    card['image'] = img
                else:
                    card['image'] = fetch_ingredient_image(r, r.get('cuisine'))
            else:
                # No valid provided image; fetch based on main ingredient
                card['image'] = fetch_ingredient_image(r, r.get('cuisine'))
        except Exception:
            card['image'] = '/static/images/quinoa_salad.jpg'
        cards.append(card)
    print('[DEBUG] returning cards:', cards)
    return jsonify({'cards': cards})
    
    except Exception as e:
        # Comprehensive error handling - log the error and return fallback recipes
        print(f'\n[ERROR] Critical error in suggest_recipes: {str(e)}')
        print(f'[ERROR] Error type: {type(e).__name__}')
        import traceback
        print(f'[ERROR] Full traceback: {traceback.format_exc()}')
        
        # Log error to file for debugging
        try:
            os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
            with open(os.path.join(app.root_path, 'data', 'recipe_requests.log'), 'a', encoding='utf-8') as f:
                f.write(f'{datetime.utcnow().isoformat()}Z -- ERROR -- {str(e)} -- {json.dumps(data)}\n')
        except Exception:
            pass  # Don't let logging errors break the response
        
        # Always return fallback recipes - never show error message to user
        ingredients_param = data.get('ingredients', 'chicken') if 'data' in locals() else 'chicken'
        return get_emergency_fallback_recipes(ingredients_param)


@app.route('/api/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    # First check AI-generated recipes cache
    if recipe_id in AI_RECIPES:
        # return the AI-provided item (ensure minimal shaping matches local format)
        it = AI_RECIPES[recipe_id]
        shaped = {
            'id': recipe_id,
            'name': it.get('name'),
            'cuisine': it.get('cuisine'),
            'diet': it.get('diet'),
            'difficulty': it.get('difficulty'),
            'image': it.get('image'),
            'short': it.get('short'),
            'ingredients': it.get('ingredients') or [],
            'instructions': it.get('instructions') or '',
            'nutrition': it.get('nutrition') or {},
            'meal_types': it.get('meal_types') or []
        }
        return jsonify(shaped)
    r = next((x for x in RECIPES if x['id'] == recipe_id), None)
    if not r:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(r)


@app.route('/api/expand-recipe', methods=['POST'])
def expand_recipe():
    data = request.json or {}
    rid = data.get('id')
    if not rid:
        return jsonify({'error': 'missing_id'}), 400
    # find base recipe (AI or local)
    base = AI_RECIPES.get(rid)
    if not base:
        base = next((x for x in RECIPES if x.get('id') == rid), None)
    if not base:
        return jsonify({'error': 'not_found'}), 404

    # If we've already expanded this recipe, return cached expansion
    try:
        if isinstance(base, dict) and base.get('expanded'):
            return jsonify({'expanded': base.get('expanded')}), 200
    except Exception:
        pass

    # Ensure OpenAI key is available
    OPENAI_KEY = _os.environ.get('OPENAI_API_KEY')
    if not OPENAI_KEY:
        # try reading .env
        try:
            possible = [os.path.join(app.root_path, '.env'), os.path.join(app.root_path, 'data', '.env')]
            for p in possible:
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as fh:
                        for line in fh:
                            if line.strip().startswith('OPENAI_API_KEY'):
                                parts = line.split('=', 1)
                                if len(parts) > 1:
                                    OPENAI_KEY = parts[1].strip().strip('"').strip("'")
                                    _os.environ['OPENAI_API_KEY'] = OPENAI_KEY
                                    break
                if OPENAI_KEY:
                    break
        except Exception:
            pass
    if not OPENAI_KEY:
        return jsonify({'error': 'openai_key_missing'}), 400

    # Build prompt for expansion
    system = (
        "You are an expert chef and recipe writer. Given a recipe name, ingredients, and rough instructions, "
        "produce a JSON object with two fields: 'ingredients_detailed' (an array of ingredient lines with quantities and units, include oil and spice amounts), "
        "and 'instructions_detailed' (an ordered array of clear step-by-step instructions, with times where relevant). "
        "Be explicit about amounts (grams, cups, teaspoons, tablespoons) and keep the language simple and friendly. "
        "Return ONLY the JSON object, no extra commentary."
    )
    # Compose user content
    user_payload = {
        'name': base.get('name'),
        'cuisine': base.get('cuisine'),
        'short': base.get('short'),
        'ingredients': base.get('ingredients') or [],
        'instructions': base.get('instructions') or ''
    }
    user = f"Expand this recipe into detailed ingredients with quantities and step-by-step instructions: {json.dumps(user_payload)}"

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo',
            messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': user}],
            max_tokens=500,
            temperature=0.2,
        )
        try:
            text = resp.choices[0].message.content
        except Exception:
            text = str(resp)
        # extract first JSON object
        import re as _re
        m = _re.search(r"(\{[\s\S]*\})", text)
        if not m:
            return jsonify({'error': 'no_json_returned', 'raw': text}), 502
        raw = m.group(1)
        expanded = json.loads(raw)
        # cache in AI_RECIPES (if base is AI item) or attach to local mapping
        try:
            if rid in AI_RECIPES:
                AI_RECIPES[rid]['expanded'] = expanded
            else:
                # attach expanded to base recipe object for later retrieval
                if isinstance(base, dict):
                    base['expanded'] = expanded
        except Exception:
            pass
        return jsonify({'expanded': expanded}), 200
    except Exception as e:
        return jsonify({'error': 'openai_failed', 'detail': str(e)}), 502


@app.route('/api/feedback', methods=['POST'])
def receive_feedback():
    data = request.json or {}
    # store feedback locally in a simple append-only log
    log_line = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'feedback': data
    }
    try:
        os.makedirs('data', exist_ok=True)
        with open(os.path.join('data', 'feedback.log'), 'a', encoding='utf-8') as f:
            f.write(str(log_line) + "\n")
        return jsonify({'status': 'ok'}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/feedback')
def feedback_admin():
    entries = []
    try:
        with open('data/feedback.log', 'r', encoding='utf-8') as f:
            for line in f:
                entries.append(line.strip())
    except FileNotFoundError:
        entries = []
    return render_template('feedback.html', entries=entries)


@app.route('/api/recipe-feedback', methods=['POST'])
def recipe_feedback():
    """Handle recipe feedback submissions"""
    try:
        data = request.json or {}
        rating = data.get('rating', 0)
        comment = data.get('comment', '')
        recipe_name = data.get('recipe', 'Unknown Recipe')
        timestamp = data.get('timestamp', '')
        
        # Log feedback to file
        feedback_entry = {
            'type': 'recipe_feedback',
            'recipe': recipe_name,
            'rating': rating,
            'comment': comment,
            'timestamp': timestamp
        }
        
        # Save to feedback log
        log_file = os.path.join('data', 'feedback.log')
        os.makedirs('data', exist_ok=True)
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')
        
        return jsonify({'status': 'success', 'message': 'Feedback received'})
        
    except Exception as e:
        print(f'Error saving recipe feedback: {e}')
        return jsonify({'status': 'error', 'message': 'Failed to save feedback'}), 500


if __name__ == '__main__':
    print("🍳 Starting Grace's Cooking Chatbot...")
    print("🌟 Grace chatbot running at http://127.0.0.1:8000")
    print("🔥 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Run the Flask app with proper configuration
    app.run(debug=True, host='127.0.0.1', port=8000, use_reloader=False)
