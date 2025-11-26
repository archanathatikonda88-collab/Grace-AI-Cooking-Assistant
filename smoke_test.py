import requests

BASE = 'http://127.0.0.1:5000'

def main():
    try:
        r = requests.get(BASE + '/')
        print('/', r.status_code)
        r = requests.post(BASE + '/api/recipes', json={})
        print('/api/recipes', r.status_code, r.json())
        r = requests.get(BASE + '/api/recipe/1')
        print('/api/recipe/1', r.status_code, r.json())
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    main()
