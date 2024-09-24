import requests
import os


access_token ="Access Token" #Put there the Acces Token from the previous setup file. Not the Refresh Token.



url = "https://api.meethue.com/route/api/0/config"


headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}


data = {
    "linkbutton": True
}


response = requests.put(url, headers=headers, json=data)


if response.status_code == 200:
    print("Success!")
    print("Response:", response.json())
else:
    print(f"There was an error. Status Code: {response.status_code}")
    print("Response:", response.text)