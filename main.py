#! /usr/bin/env python3

import requests, json, os, sys, pickle, base64, string, random
from getpass import getpass
from pathlib import Path
from datetime import date
from optparse import OptionParser
from colorama import Fore, Back, Style
from time import strftime, localtime, sleep, time

from aes_256 import encrypt, decrypt, generate_key

status_color = {
    '+': Fore.GREEN,
    '-': Fore.RED,
    '*': Fore.YELLOW,
    ':': Fore.CYAN,
    ' ': Fore.WHITE
}

def display(status, data, start='', end='\n'):
    print(f"{start}{status_color[status]}[{status}] {Fore.BLUE}[{date.today()} {strftime('%H:%M:%S', localtime())}] {status_color[status]}{Style.BRIGHT}{data}{Fore.RESET}{Style.RESET_ALL}", end=end)

def get_arguments(*args):
    parser = OptionParser()
    for arg in args:
        parser.add_option(arg[0], arg[1], dest=arg[2], help=arg[3])
    return parser.parse_args()[0]

cwd = Path.cwd()
default_branch = "main"
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
def cloneRepository(auth_token, user, repository, folder=None):
    if folder == None:
        folder = f".repositories/{repository}"
    status = os.system(f"git clone https://{auth_token}@github.com/{user}/{repository}.git {folder}")
    return status

def generateRandom(length):
    letters = string.ascii_letters + "0123456789"
    return ''.join([random.choice(letters) for _ in range(length)])

def makeFolders():
    temporary_repository_folder = cwd / ".repositories"
    temporary_repository_folder.mkdir(exist_ok=True)
    user_config_folder = cwd / "configs"
    user_config_folder.mkdir(exist_ok=True) 

if __name__ == "__main__":
    makeFolders()
    arguments = get_arguments(('-u', "--user", "user", "Github Username"),
                              ('-b', "--branch", "branch", f"Branch of Github Repositories (Default={default_branch})"))
    if not arguments.user:
        display('-', f"Please Provide a Username")
        exit(0)
    if not arguments.branch:
        display(':', f"Branch Set to {Back.MAGENTA}{default_branch}{Back.RESET}")
        arguments.branch = default_branch
    try:
        with open("authentication_tokens.pickle", 'rb') as file:
            authentication_tokens = pickle.load(file)
    except FileNotFoundError:
        authentication_tokens = {}
    except:
        display('-', f"Error while Reading Authentication Tokens")
        exit(0)
    if arguments.user not in authentication_tokens.keys():
        auth_token = input(f"Enter Github API Authentication Token for {arguments.user} : ")
        github_password = getpass(f"Enter your Github Account Password for User {arguments.user} : ")
        config_repository_status = cloneRepository(auth_token, arguments.user, "storage_config", f"configs/{arguments.user}")
        salt = None
        if config_repository_status != 0:
            public_before_zip = getpass(f"Enter AES-Encryption Password before File Zipping for Public Files (Enter Empty for Autogeneration) : ")
            if public_before_zip == '':
                public_before_zip = generateRandom(50)
            public_zip = getpass(f"Enter Password for Public ZIP Files (Enter Empty for Autogeneration) : ")
            if public_zip == '':
                public_zip = generateRandom(50)
            public_after_zip = getpass(f"Enter AES-Encryption Password afer File Zipping for Public Files (Enter Empty for Autogeneration) : ")
            if public_after_zip == '':
                public_after_zip = generateRandom(50)
            private_before_zip = getpass(f"Enter AES-Encryption Password before File Zipping for private Files (Enter Empty for Autogeneration) : ")
            if private_before_zip == '':
                private_before_zip = generateRandom(50)
            private_zip = getpass(f"Enter Password for private ZIP Files (Enter Empty for Autogeneration) : ")
            if private_zip == '':
                private_zip = generateRandom(50)
            private_after_zip = getpass(f"Enter AES-Encryption Password afer File Zipping for private Files (Enter Empty for Autogeneration) : ")
            if private_after_zip == '':
                private_after_zip = generateRandom(50)
        else:
            with open(f"configs/{arguments.user}/public_config", 'rb') as file:
                public_config = pickle.load(file.read())
                public_before_zip = public_config["public_before_zip"]
                public_zip = public_config["public_zip"]
                public_after_zip = public_config["public_after_zip"]
                config_salt = public_config["salt"]
            with open(f"configs/{arguments.user}/public_config", 'rb') as file:
                content = file.read()
                key, _ = generate_key(github_password)
                private_config = decrypt(content, key, config_salt)
                encrypted_private_before_zip = private_config["private_before_zip"]
                encrypted_private_zip = private_config["private_zip"]
                encrypted_private_after_zip = private_config["private_after_zip"]
                salt = private_config["salt"]
            private_before_zip = decrypt(encrypted_private_before_zip, key, salt).decode()
            private_zip = decrypt(encrypted_private_zip, key, salt).decode()
            private_after_zip = decrypt(encrypted_private_after_zip, key, salt).decode()
        auth_storing_status = input(f"Do you want to Store the Token (Y/n) : ")
        if 'y' in auth_storing_status.lower():
            auth_token_password = getpass(f"Enter the Password to Securely Store the Token : ")
            if salt == None:
                key, salt = generate_key(auth_token_password)
            else:
                key, _ = generate_key(auth_token_password, salt)
            encrypted_auth_token = encrypt(auth_token.encode(), key, salt)
            encrypted_github_password = encrypt(github_password.encode(), key, salt)
            encrypted_private_before_zip = encrypt(private_before_zip.encode(), key, salt)
            encrypted_private_zip = encrypt(private_zip.encode(), key, salt)
            encrypted_private_after_zip = encrypt(private_after_zip.encode(), key, salt)
            authentication_tokens[arguments.user] = {
                "token": encrypted_auth_token,
                "github_password": encrypted_github_password,
                "public_before_zip": public_before_zip,
                "public_zip": public_zip,
                "public_after_zip": public_after_zip,
                "private_before_zip": encrypted_private_before_zip,
                "private_zip": encrypted_private_zip,
                "private_after_zip": encrypted_private_after_zip,
                "salt": salt
            }
            with open("authentication_tokens.pickle", 'wb') as file:
                pickle.dump(authentication_tokens, file)
    else:
        encrypted_auth_token = authentication_tokens[arguments.user]["token"]
        encrypted_github_password = authentication_tokens[arguments.user]["github_password"]
        public_before_zip = authentication_tokens[arguments.user]["public_before_zip"]
        public_zip = authentication_tokens[arguments.user]["public_zip"]
        public_after_zip = authentication_tokens[arguments.user]["public_after_zip"]
        encrypted_private_before_zip = authentication_tokens[arguments.user]["private_before_zip"]
        encrypted_private_zip = authentication_tokens[arguments.user]["private_zip"]
        encrypted_private_after_zip = authentication_tokens[arguments.user]["private_after_zip"]
        salt = authentication_tokens[arguments.user]["salt"]
        auth_token_password =  getpass(f"Enter the Password for Accessing Token : ")
        try:
            key, _ = generate_key(auth_token_password, salt)
            auth_token = decrypt(encrypted_auth_token, key, salt).decode()
            github_password = decrypt(encrypted_github_password, key, salt).decode()
            private_before_zip = decrypt(encrypted_private_before_zip, key, salt).decode()
            private_zip = decrypt(encrypted_private_zip, key, salt).decode()
            private_after_zip = decrypt(encrypted_private_after_zip, key, salt).decode()
        except Exception as err:
            display('-', f"Wrong Password!")
            exit(0)
    users_present = os.listdir("configs")
    if arguments.user not in users_present:
        config_repository_status = cloneRepository(auth_token, arguments.user, "storage_config", f"configs/{arguments.user}")
        if config_repository_status != 0:
            createRepository(auth_token, "storage_config", False)
            cloneRepository(auth_token, arguments.user, "storage_config", f"configs/{arguments.user}")
    config_files = os.listdir(f"configs/{arguments.user}")
    config_files.remove(".git")
    config_files.sort()
    if config_files != ["private_config", "public_config"]:
        for file in config_files:
            os.system(f"rm configs/{arguments.user}/{file}")
        public_config = {
            "public_before_zip": public_before_zip,
            "public_zip": public_zip,
            "public_after_zip": public_after_zip,
        }
        private_config = {
            "private_before_zip": encrypted_private_before_zip,
            "private_zip": encrypted_private_zip,
            "private_after_zip": encrypted_private_after_zip,
        }
        key, config_salt = generate_key(github_password)
        public_config["salt"] = config_salt
        private_config["salt"] = salt
        with open(f"configs/{arguments.user}/public_config", 'wb') as file:
            pickle.dump(public_config, file)
        with open(f"configs/{arguments.user}/private_config", 'wb') as file:
            content = encrypt(pickle.dumps(private_config), key, salt)
            file.write(content)
        os.chdir(f"configs/{arguments.user}")
        os.system("git add .")
        os.system(f"git commit -m 'Added Configuration Files'")
        os.system(f"git push origin {arguments.branch}")
        os.chdir(str(cwd))
    else:
        os.chdir(f"configs/{arguments.user}")
        os.system(f"git pull")
        with open(f"public_config", 'rb') as file:
            public_config = pickle.load(file)
        public_before_zip = public_config["public_before_zip"]
        public_zip = public_config["public_zip"]
        public_after_zip = public_config["public_after_zip"]
        config_salt = public_config["salt"]
        key, _ = generate_key(github_password, config_salt)
        with open(f"private_config", 'rb') as file:
            content = file.read()
            private_config = pickle.loads(decrypt(content, key, config_salt))
        salt = private_config = private_config["salt"]
        encrypted_private_before_zip = private_config["private_before_zip"]
        encrypted_private_zip = private_config["private_zip"]
        encrypted_private_after_zip = private_config["private_after_zip"]
        private_before_zip = decrypt(encrypted_private_before_zip, key, salt).decode()
        private_zip = decrypt(encrypted_private_zip, key, salt).decode()
        private_after_zip = decrypt(encrypted_private_after_zip, key, salt).decode()