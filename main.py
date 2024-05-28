#! /usr/bin/env python3

import requests, json, os, sys

githubREPO_API = "https://api.github.com/user/repos"

def createRepository(auth_token, name, private):
    headers = {
        "Authorization": f"token {auth_token}"
    }
    data = {
        "name": name,
        "private": private,
    }
    response = requests.post(githubREPO_API, headers=headers, data=json.dumps(data))
    if response.status_code == 201:
        return True
    return response
def deleteRepository(auth_token, user, repository):
    headers = {
        "Authorization": f"token {auth_token}"
    }
    response = requests.delete(f"https://api.github.com/repos/{user}/{repository}", headers=headers)
    if response.status_code == 204:
        return True
    return response
def cloneRepository(auth_token, user, repository):
    status = os.system(f"git clone https://{auth_token}@github.com/{user}/{repository}.git")
    return status


if __name__ == "__main__":
    pass