#! /usr/bin/env python3

import requests, json

githubAPI = "https://api.github.com/user/repos"

def createRepository(auth_token, name, visibility):
    headers = {
        "Authorization": f"token {auth_token}"
    }
    data = {
        "name": name,
        "private": visibility,
    }
    response = requests.post(githubAPI, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        return True
    return response.status_code


if __name__ == "__main__":
    pass