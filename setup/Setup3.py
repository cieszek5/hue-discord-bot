import requests
import os


access_token = "Access Token" #Put there the Acces Token, the same as in Setup2.py file.



url = "https://api.meethue.com/route/api"


headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}


data = {
    "devicetype": "discord_bot"
}


response = requests.post(url, headers=headers, json=data)


if response.status_code == 200:
    print("Success!")
    print("Response:", response.json())
else:
    print(f"There was an error. Response : {response.status_code}")
    print("Response:", response.text)