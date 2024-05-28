#! /usr/bin/env python3

import requests, json, os, sys
from pathlib import Path
from datetime import date
from optparse import OptionParser
from colorama import Fore, Back, Style
from time import strftime, localtime, sleep, time

status_color = {
    '+': Fore.GREEN,
    '-': Fore.RED,
    '*': Fore.YELLOW,
    ':': Fore.CYAN,
    ' ': Fore.WHITE
}

def display(status, data, start='', end='\n'):
    print(f"{start}{status_color[status]}[{status}] {Fore.BLUE}[{date.today()} {strftime('%H:%M:%S', localtime())}] {status_color[status]}{Style.BRIGHT}{data}{Fore.RESET}{Style.RESET_ALL}", end=end)

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
    status = os.system(f"git clone https://{auth_token}@github.com/{user}/{repository}.git .repositories/{repository}")
    return status

def makeFolders():
    cwd = Path.cwd()
    temporary_repository_folder = cwd / ".repositories"
    temporary_repository_folder.mkdir(exist_ok=True)
    user_config_folder = cwd / "configs"
    user_config_folder.mkdir(exist_ok=True) 

if __name__ == "__main__":
    makeFolders()