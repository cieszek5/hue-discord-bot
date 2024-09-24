import requests
import base64
import json

client_id = "Put here" #Client ID from Remote Hue API appids
client_secret = "Put here" #Secret from Remote Hue API appids
auth_code = "Put here" #Code from a searchbar

url = "https://api.meethue.com/v2/oauth2/token"
auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

headers = {
    "Authorization": f"Basic {auth_header}",
    "Content-Type": "application/x-www-form-urlencoded"
}

data = {
    "grant_type": "authorization_code",
    "code": auth_code
}

response = requests.post(url, headers=headers, data=data)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
print(f"Response Body: {json.dumps(response.json(), indent=2)}")

tokens = response.json()

if 'refresh_token' in tokens:
    print("\nRefresh Token:", tokens['refresh_token'])
else:
    print("\nNo refresh token found in the response. Please check the error message above.")