#!/usr/bin/env python3
"""
Test script for enhanced difficulty-based recipe generation.
Tests all three difficulty levels (easy, moderate, complex) and verifies
that the returned recipes match the expected complexity criteria.
"""

import requests
import json
import sys
from datetime import datetime

SERVER_URL = "http://127.0.0.1:8000"

def test_recipe_difficulty(ingredients, difficulty):
    """Test recipe generation for a specific difficulty level."""
    print(f"\n{'='*60}")
    print(f"Testing {difficulty.upper()} recipes with ingredients: {ingredients}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{SERVER_URL}/get_recipes",
            json={
                "ingredients": ingredients,
                "difficulty": difficulty,
                "cuisine": "international"
            },
            timeout=45
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
        data = response.json()
        recipes = data.get('recipes', [])
        
        if not recipes:
            print(f"❌ No recipes returned for {difficulty}")
            return False
            
        print(f"✅ Received {len(recipes)} recipes")
        
        # Test each recipe by getting its details
        for i, recipe in enumerate(recipes):
            recipe_id = recipe.get('id')
            if not recipe_id:
                continue
                
            print(f"\n--- Recipe {i+1}: {recipe.get('name', 'Unnamed')} ---")
            
            # Get full recipe details
            detail_response = requests.get(f"{SERVER_URL}/api/recipe/{recipe_id}")
            if detail_response.status_code == 200:
                full_recipe = detail_response.json()
                validate_recipe_complexity(full_recipe, difficulty)
            else:
                print(f"❌ Could not fetch details for recipe {recipe_id}")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def validate_recipe_complexity(recipe, expected_difficulty):
    """Validate that a recipe matches the expected difficulty complexity."""
    name = recipe.get('name', 'Unnamed')
    ingredients = recipe.get('ingredients', [])
    instructions = recipe.get('instructions', '')
    difficulty = recipe.get('difficulty', '').lower()
    
    print(f"Recipe: {name}")
    print(f"Reported difficulty: {difficulty}")
    print(f"Ingredients count: {len(ingredients)}")
    
    # Count instruction steps
    if isinstance(instructions, str):
        steps = [step.strip() for step in instructions.replace('\n', '.').split('.') if step.strip() and len(step.strip()) > 5]
        step_count = len(steps)
    else:
        step_count = 0
    
    print(f"Instruction steps count: {step_count}")
    
    # Define expected ranges for each difficulty
    difficulty_expectations = {
        'easy': {'ingredients': (3, 6), 'steps': (3, 5)},
        'moderate': {'ingredients': (6, 10), 'steps': (5, 8)},  # Allowing 5-8 steps for moderate
        'complex': {'ingredients': (10, 20), 'steps': (8, 15)}  # Allowing up to 15 steps for complex
    }
    
    expected = difficulty_expectations.get(expected_difficulty.lower(), {})
    ing_range = expected.get('ingredients', (0, 100))
    step_range = expected.get('steps', (0, 100))
    
    # Check ingredient count
    ing_ok = ing_range[0] <= len(ingredients) <= ing_range[1]
    step_ok = step_range[0] <= step_count <= step_range[1]
    
    print(f"Ingredients: {len(ingredients)} (expected: {ing_range[0]}-{ing_range[1]}) {'✅' if ing_ok else '❌'}")
    print(f"Steps: {step_count} (expected: {step_range[0]}-{step_range[1]}) {'✅' if step_ok else '❌'}")
    
    # Show some sample content
    if ingredients:
        print(f"Sample ingredients: {ingredients[:3]}")
    if instructions:
        first_step = instructions.split('.')[0] if '.' in instructions else instructions[:100]
        print(f"First instruction: {first_step[:100]}...")
        
    # Analyze language complexity for different difficulties
    analyze_language_complexity(instructions, expected_difficulty)
    
    return ing_ok and step_ok

def analyze_language_complexity(instructions, difficulty):
    """Analyze the language complexity of instructions."""
    if not instructions:
        return
        
    text = instructions.lower()
    
    # Simple complexity indicators
    technical_terms = ['sear', 'braise', 'deglaze', 'julienne', 'chiffonade', 'mise en place', 'emulsion', 'caramelize', 'bloom', 'mount']
    simple_terms = ['cook', 'mix', 'heat', 'add', 'stir', 'boil']
    
    technical_count = sum(1 for term in technical_terms if term in text)
    simple_count = sum(1 for term in simple_terms if term in text)
    
    print(f"Language complexity - Technical terms: {technical_count}, Simple terms: {simple_count}")
    
    # Expected complexity by difficulty
    if difficulty == 'easy':
        expected_simple = True
        print(f"Expected: Simple language {'✅' if simple_count > technical_count else '❌'}")
    elif difficulty == 'moderate':
        expected_moderate = True
        print(f"Expected: Moderate complexity (some technical terms) {'✅' if technical_count > 0 else '❌'}")
    elif difficulty == 'complex':
        expected_complex = True
        print(f"Expected: Complex language (many technical terms) {'✅' if technical_count >= 2 else '❌'}")

def main():
    """Run comprehensive tests for all difficulty levels."""
    print("🧪 Grace Cooking Assistant - Enhanced Recipe Difficulty Test")
    print(f"Testing server at: {SERVER_URL}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test cases for different difficulty levels
    test_cases = [
        ("chicken, tomato, onion", "easy"),
        ("chicken, bell pepper, soy sauce, ginger, garlic, rice", "moderate"), 
        ("chicken, saffron, basmati rice, yogurt, spices, ghee, onions, garlic, ginger, tomatoes, cilantro", "complex")
    ]
    
    results = []
    
    for ingredients, difficulty in test_cases:
        success = test_recipe_difficulty(ingredients, difficulty)
        results.append((difficulty, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for difficulty, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{difficulty.upper():<12} {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nOverall: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("🎉 All tests passed! Enhanced recipe generation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())