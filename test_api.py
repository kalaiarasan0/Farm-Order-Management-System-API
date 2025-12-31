import urllib.request
import urllib.error

url = "http://localhost:8000/api/v1/track/animals/list?limit=50&offset=0"
headers = {"accept": "application/json"}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.getcode()}")
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode())
except Exception as e:
    print(f"Error: {e}")
