import requests


resp = requests.get('myproject.com')
print(resp)
print(resp.text)
