#!/usr/bin/env python3
"""
Test script to verify image consistency across recipe endpoints
"""
import requests
import json

def test_image_consistency():
    print('=== TESTING IMAGE CONSISTENCY AFTER SERVER RESTART ===')

    # Test the suggest endpoint
    print('Testing /suggest endpoint...')
    try:
        suggest_resp = requests.post('http://127.0.0.1:8000/suggest', 
                                   json={'ingredients': 'pasta', 'cuisine': 'italian', 'difficulty': 'easy'})
        if suggest_resp.status_code == 200:
            suggest_data = suggest_resp.json()
            if suggest_data.get('cards'):
                card = suggest_data['cards'][0]
                print('Card details:')
                print('  Name:', card.get('name'))
                print('  Image:', card.get('image'))
                print('  Image_URL:', card.get('image_url'))
                print('  ID:', card.get('id'))
                
                # Test detail endpoint
                card_id = card.get('id')
                print(f'\nTesting /api/recipe/{card_id} endpoint...')
                detail_resp = requests.get(f'http://127.0.0.1:8000/api/recipe/{card_id}')
                if detail_resp.status_code == 200:
                    detail_data = detail_resp.json()
                    print('Detail details:')
                    print('  Name:', detail_data.get('name'))
                    print('  Image:', detail_data.get('image'))
                    print('  Image_URL:', detail_data.get('image_url'))
                    print('\nConsistency check:')
                    print('  Images match:', card.get('image') == detail_data.get('image'))
                    print('  Both have image_url:', bool(card.get('image_url')) and bool(detail_data.get('image_url')))
                    
                    # Additional checks
                    if card.get('image_url') is None:
                        print('  WARNING: Card missing image_url field!')
                    if detail_data.get('image_url') is None:
                        print('  WARNING: Detail missing image_url field!')
                        
                    return True
                else:
                    print(f'Detail endpoint failed: {detail_resp.status_code}')
                    return False
            else:
                print('No cards returned')
                return False
        else:
            print(f'Suggest endpoint failed: {suggest_resp.status_code}')
            return False
    except Exception as e:
        print(f'Error: {str(e)}')
        return False

if __name__ == '__main__':
    test_image_consistency()