import requests

test_data = {"ingredients":"chicken, onion, tomato","cuisine":"","difficulty":"","broaden":False}
print('Requesting /get_recipes...')
resp = requests.post('http://127.0.0.1:8000/get_recipes', json=test_data, timeout=30)
print('Status', resp.status_code)
data = resp.json()
print('Keys:', list(data.keys()))
if 'recipes' in data:
    for r in data['recipes']:
        print('-', r.get('id'), r.get('name'), '->', r.get('image_url'))

if 'recipes' in data and data['recipes']:
    rid = data['recipes'][0]['id']
    print('\nRequesting detail for id', rid)
    d = requests.get(f'http://127.0.0.1:8000/api/recipe/{rid}', timeout=15)
    print('Detail status', d.status_code)
    print('Detail keys:', list(d.json().keys()))
    print('Detail image:', d.json().get('image'))
