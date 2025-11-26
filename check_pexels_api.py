#!/usr/bin/env python3
"""
Pexels API Status Checker for Grace's Cooking Chatbot
This script checks your Pexels API key status, usage limits, and tests image fetching
"""

import requests
import json
import os
from datetime import datetime

# Load API key from environment
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')  # Load from environment variable
PEXELS_API_URL = "https://api.pexels.com/v1/search"

def check_pexels_api_status():
    """Check Pexels API key status and limits"""
    
    print("🔍 PEXELS API STATUS CHECKER")
    print("=" * 50)
    
    if not PEXELS_API_KEY or PEXELS_API_KEY == 'YOUR_PEXELS_API_KEY_HERE':
        print("❌ ERROR: No valid Pexels API key found!")
        return False
    
    print(f"✅ API Key found: {PEXELS_API_KEY[:20]}...{PEXELS_API_KEY[-8:]}")
    
    # Test API with a simple search
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    
    # Test searches to check functionality
    test_searches = [
        "chicken curry",
        "pasta dish", 
        "fish cooking",
        "rice food",
        "indian food"
    ]
    
    print(f"\n🧪 TESTING API WITH {len(test_searches)} SEARCHES:")
    print("-" * 50)
    
    successful_searches = 0
    failed_searches = 0
    
    for i, search_term in enumerate(test_searches, 1):
        try:
            print(f"\n{i}. Testing search: '{search_term}'")
            
            params = {
                'query': search_term,
                'per_page': 1
            }
            
            response = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=10)
            
            # Check response headers for rate limit info
            remaining_requests = response.headers.get('X-Ratelimit-Remaining')
            total_limit = response.headers.get('X-Ratelimit-Limit') 
            reset_time = response.headers.get('X-Ratelimit-Reset')
            
            print(f"   Status Code: {response.status_code}")
            
            if remaining_requests:
                print(f"   📊 Remaining Requests: {remaining_requests}")
            if total_limit:
                print(f"   📈 Total Limit: {total_limit}")
            if reset_time:
                reset_date = datetime.fromtimestamp(int(reset_time))
                print(f"   🔄 Reset Time: {reset_date}")
            
            if response.status_code == 200:
                data = response.json()
                photos = data.get('photos', [])
                
                if photos:
                    photo = photos[0]
                    image_url = photo.get('src', {}).get('medium', 'No URL')
                    photographer = photo.get('photographer', 'Unknown')
                    
                    print(f"   ✅ SUCCESS: Found image")
                    print(f"   📸 Photographer: {photographer}")
                    print(f"   🔗 URL: {image_url[:60]}...")
                    successful_searches += 1
                else:
                    print(f"   ⚠️  No images found for '{search_term}'")
                    failed_searches += 1
                    
            elif response.status_code == 429:
                print(f"   🚫 RATE LIMIT EXCEEDED!")
                print(f"   💡 You've hit your API request limit")
                failed_searches += 1
                break
                
            elif response.status_code == 401:
                print(f"   ❌ UNAUTHORIZED - Invalid API key")
                failed_searches += 1
                break
                
            else:
                print(f"   ❌ ERROR: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   📝 Error: {error_data}")
                except:
                    print(f"   📝 Raw response: {response.text[:100]}...")
                failed_searches += 1
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ TIMEOUT: Request took too long")
            failed_searches += 1
            
        except Exception as e:
            print(f"   💥 EXCEPTION: {str(e)}")
            failed_searches += 1
    
    # Summary
    print(f"\n📋 SUMMARY:")
    print("=" * 50)
    print(f"✅ Successful searches: {successful_searches}")
    print(f"❌ Failed searches: {failed_searches}")
    print(f"📊 Success rate: {(successful_searches/(successful_searches+failed_searches)*100):.1f}%")
    
    if successful_searches > 0:
        print(f"\n🎉 Your Pexels API is working!")
        print(f"💡 If recipes aren't showing images, check:")
        print(f"   1. Recipe names might be too specific")
        print(f"   2. Fallback system should still work")
        print(f"   3. Check browser console for errors")
    else:
        print(f"\n🚨 API Issues Detected!")
        print(f"💡 Possible causes:")
        print(f"   1. Rate limit exceeded (200 requests/hour for free)")
        print(f"   2. Invalid API key")
        print(f"   3. Network connectivity issues")
    
    return successful_searches > 0

def check_recipe_specific_searches():
    """Test searches that your chatbot would actually use"""
    
    print(f"\n🍳 TESTING RECIPE-SPECIFIC SEARCHES:")
    print("=" * 50)
    
    recipe_tests = [
        "Fish Pulusu",           # Exotic recipe name
        "Chicken Biryani",       # Popular Indian dish  
        "Vegetable Curry",       # Generic vegetable dish
        "Paneer Butter Masala",  # Specific Indian dish
        "Pasta Carbonara"        # Italian dish
    ]
    
    headers = {'Authorization': PEXELS_API_KEY}
    
    for recipe in recipe_tests:
        print(f"\n🔍 Testing recipe: '{recipe}'")
        
        # Test multiple search strategies (like your enhanced function)
        search_variations = [
            recipe,                          # Exact name
            f"{recipe} dish",               # Name + dish
            recipe.split()[0] + " cooking", # First ingredient + cooking
            recipe.split()[0] + " food"     # First ingredient + food  
        ]
        
        found_image = False
        for variation in search_variations:
            try:
                params = {'query': variation, 'per_page': 1}
                response = requests.get(PEXELS_API_URL, headers=headers, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('photos'):
                        print(f"   ✅ Found with: '{variation}'")
                        photo = data['photos'][0]
                        print(f"   📸 URL: {photo['src']['medium'][:50]}...")
                        found_image = True
                        break
                        
            except Exception as e:
                continue
        
        if not found_image:
            print(f"   ❌ No images found for any variation of '{recipe}'")

if __name__ == "__main__":
    success = check_pexels_api_status()
    
    if success:
        check_recipe_specific_searches()
        
        print(f"\n🔧 TROUBLESHOOTING TIPS:")
        print("=" * 50)
        print("1. Free Pexels accounts have 200 requests/hour limit")
        print("2. If limit exceeded, images will use local fallbacks")
        print("3. Clear browser cache and try again")
        print("4. Check network connectivity")
        print("5. Restart Flask server after any changes")
        
    print(f"\n🌟 For more Pexels API info: https://www.pexels.com/api/documentation/")