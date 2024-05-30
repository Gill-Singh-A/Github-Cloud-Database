#! /usr/bin/env python3

import requests, json, os, sys, pickle, base64, string, random, shutil, zipfile
from math import ceil, sqrt
from getpass import getpass
from pathlib import Path
from datetime import date
from optparse import OptionParser
from colorama import Fore, Back, Style
from multiprocessing import cpu_count, Pool, Lock
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
mbs = 51
individual_segment_size = mbs * 1000 * 1000
segements_per_repository = 39
github_repo_size = individual_segment_size * segements_per_repository
thread_count = cpu_count()
lock = Lock()

'''
+ .
/ -
= _
'''

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
def cloneRepository(auth_token, user, repository, folder=None, verbose=True):
    if folder == None:
        folder = f".repositories/{repository}"
    status = os.system(f"git clone https://{auth_token}@github.com/{user}/{repository.replace(' ', '-')}.git '{folder.replace(' ', '-')}' {'' if verbose else '>/dev/null 2>/dev/null'}")
    return status
def cloneRepositories(auth_token, user, repositories):
    for repository in repositories:
        cloneRepository(auth_token, user, repository, f".repositories/{repository}", False)
def createRepositories(auth_token, user, repositories, private):
    for repository in repositories:
        createRepository(auth_token, repository, private)
        cloneRepository(auth_token, user, repository, f"../.repositories/{repository}", False)
def encryptFiles(key, salt, files):
    for small_file in files:
        with open(small_file, 'rb') as file:
            content = file.read()
        encrypted_content = encrypt(content, key, salt)
        with open(small_file, 'wb') as file:
            file.write(encrypted_content)
def decryptFiles(key, salt, files):
    for small_file in files:
        with open(small_file, 'rb') as file:
            encrypted_content = file.read()
        content = decrypt(encrypted_content, key, salt)
        with open(small_file, 'wb') as file:
            file.write(content)
def zipFile(file, password=None):
    with zipfile.ZipFile(f"{file}.zip", 'w') as ZipFile:
        ZipFile.write(file)
        if password != None:
            ZipFile.setpassword(password.encode())
def unzipFile(file, password=None):
    with zipfile.ZipFile(f"{file}.zip", 'r') as ZipFile:
        if password:
            ZipFile.setpassword(password.encode())
        ZipFile.extractall(".")
def uploadToRepositories(repositores):
    for repository_name in repositores:
        os.chdir(f"../.repositories/{repository_name.replace(' ', '-')}")
        os.system("git add .")
        os.system("git commit -m 'Added File Segments' >/dev/null 2>/dev/null")
        os.system(f"git push origin {default_branch} >/dev/null 2>/dev/null")
        os.system("..")
        os.system(f"rm -rf {repository_name.replace(' ', '-')}")
def uploadFile(auth_token, file_path, private, user, key_before, zip_key, key_after):
    file_name = file_path.split('/')[-1]
    file_size = os.path.getsize(file_path)
    free_space = shutil.disk_usage(file_path).free
    display(':', f"File Size  = {Back.MAGENTA}{file_size} Bytes{Back.RESET}")
    display(':', f"Free Space = {Back.MAGENTA}{free_space} Bytes{Back.RESET}")
    if free_space < file_size * 2.5:
        return False, "Not Enough Space for Processing the File", '', file_size
    display('+', f"Copying the File Contents...")
    os.chdir(".tmp")
    if key_before != False:
        display(':', f"Encrypting before Compressing")
        display('+', f"Spliting the File into Files of {mbs}MB each...")
        os.system(f"split -b {mbs}M '{file_path}'")
        files = os.listdir()
        files.sort()
        total_files = len(files)
        display('+', f"Total Segments = {Back.MAGENTA}{total_files}{Back.RESET}")
        display('+', f"Encrypting All the Segments using {thread_count} Threads...")
        key, salt_before = generate_key(key_before)
        pool = Pool(thread_count)
        file_divisions = [files[group*total_files//thread_count: (group+1)*total_files//thread_count] for group in range(thread_count)]
        threads = []
        for file_division in file_divisions:
            threads.append(pool.apply_async(encryptFiles, (key, salt_before, file_division)))
        for thread in threads:
            thread.get()
        pool.close()
        pool.join()
        display('+', f"Merging All the Segments to a Single File...")
        os.system(f"cat {' '.join(files)} > '{file_name}'")
        display('+', f"Removing Segments...")
        os.system(f"rm {' '.join(files)}")
    else:
        salt_before = ''
    display(':', f"Compressing the File...")
    zipFile(file_name, zip_key)
    display('+', f"Removing the Previous File")
    os.system(f"rm '{file_name}'")
    display('+', f"Spliting the File into Files of {mbs}MB each...")
    os.system(f"split -b {mbs}M '{file_name}.zip'")
    os.system(f"rm '{file_name}.zip'")
    if key_after != False:
        display(':', f"Encrypting After Compressing")
        files = os.listdir()
        files.sort()
        total_files = len(files)
        display('+', f"Total Segments = {Back.MAGENTA}{total_files}{Back.RESET}")
        display('+', f"Encrypting All the Segments using {thread_count} Threads...")
        key, salt_after = generate_key(key_after)
        pool = Pool(thread_count)
        file_divisions = [files[group*total_files//thread_count: (group+1)*total_files//thread_count] for group in range(thread_count)]
        threads = []
        for file_division in file_divisions:
            threads.append(pool.apply_async(encryptFiles, (key, salt_after, file_division)))
        for thread in threads:
            thread.get()
        pool.close()
        pool.join()
    else:
        salt_after = ''
    display(':', f"Uploading Segments to Github")
    files = os.listdir()
    files.sort()
    total_files = len(files)
    files = [[file, index // segements_per_repository] for index, file in enumerate(files)]
    repository_count = ceil(total_files / segements_per_repository)
    repositories = [f"{base64.b64encode(file_name.encode()).decode().replace('+', '.').replace('/', '-').replace('=', '_')}_{index}" for index in range(repository_count)]
    repository_divisions = [repositories[group*repository_count//thread_count: (group+1)*repository_count//thread_count] for group in range(thread_count)]
    display('+', f"Repositories Required = {Back.MAGENTA}{repository_count}{Back.RESET}")
    display('+', f"Create Repositories using 16 Threads...")
    pool = Pool(thread_count)
    threads = []
    for repository_division in repository_divisions:
        threads.append(pool.apply_async(createRepositories, (auth_token, user, repository_division, private)))
    for thread in threads:
        thread.get()
    pool.close()
    pool.join()
    display('+', f"Uploading Files to Repositories using {int(sqrt(thread_count))} Threads...")
    for index, (file, repository_index) in enumerate(files):
        os.system(f"mv {file} ../.repositories/{base64.b64encode(file_name.encode()).decode().replace('+', '.').replace('/', '-').replace('=', '_')}_{repository_index}/{index}")
    pool = Pool(int(sqrt(thread_count)))
    repository_divisions = [repositories[group*repository_count//int(sqrt(thread_count)): (group+1)*repository_count//int(sqrt(thread_count))] for group in range(int(sqrt(thread_count)))]
    threads = []
    for repository_division in repository_divisions:
        threads.append(pool.apply_async(uploadToRepositories, (repository_division, )))
    for thread in threads:
        thread.get()
    pool.close()
    pool.join()
    os.chdir(str(cwd))
    return salt_before, salt_after, repositories, file_size
def downloadFile(file, user, repositories, key_before, zip_key, key_after, salt_before, salt_after):
    total_repositories = len(repositories)
    display('+', f"Cloning {total_repositories} Repositories with {thread_count} Threads")
    repository_divisions = [repositories[group*total_repositories//thread_count: (group+1)*(total_repositories)//thread_count] for group in range(thread_count)]
    pool = Pool(thread_count)
    threads = []
    for repository_division in repository_divisions:
        threads.append(pool.apply_async(cloneRepositories, (auth_token, user, repository_division, )))
    for thread in threads:
        thread.get()
    pool.close()
    pool.join()
    base_name = repositories[0].split('_')[0]
    files = [file for file in os.listdir(".repositories") if file.startswith(base_name)]
    temporary_repository_folder = cwd / ".tmp" / base_name
    temporary_repository_folder.mkdir(exist_ok=True, parents=True)
    for repository in files:
        os.system(f"mv .repositories/{repository}/* .tmp/{base_name}/.")
    os.chdir(f".tmp/{base_name}")
    files = os.listdir()
    files.sort()
    total_files = len(files)
    if key_after:
        display('+', f"Total Segments = {Back.MAGENTA}{total_files}{Back.RESET}")
        display('+', f"Decrypting All the Segments using {thread_count} Threads...")
        key, _ = generate_key(key_after, salt_after)
        pool = Pool(thread_count)
        file_divisions = [files[group*total_files//thread_count: (group+1)*total_files//thread_count] for group in range(thread_count)]
        threads = []
        for file_division in file_divisions:
            threads.append(pool.apply_async(decryptFiles, (key, salt_after, file_division)))
        for thread in threads:
            thread.get()
        pool.close()
        pool.join()
    display('+', f"Merging All the Segments to a Single File...")
    os.system(f"cat {' '.join(files)} > '{file}.zip'")
    display('+', f"Removing Segments...")
    os.system(f"rm {' '.join(files)}")
    display(':', f"Decompressing the File...")
    unzipFile(file, zip_key)
    os.system(f"rm '{file}.zip'")
    if key_before:
        display('+', f"Spliting the File into Files of {mbs}MB each...")
        os.system(f"split -b {mbs}M '{file}'")
        os.system(f"rm '{file}'")
        files = os.listdir()
        files.sort()
        total_files = len(files)
        display('+', f"Total Segments = {Back.MAGENTA}{total_files}{Back.RESET}")
        display('+', f"Decrypting All the Segments using {thread_count} Threads...")
        key, _ = generate_key(key_before, salt_before)
        pool = Pool(thread_count)
        file_divisions = [files[group*total_files//thread_count: (group+1)*total_files//thread_count] for group in range(thread_count)]
        threads = []
        for file_division in file_divisions:
            threads.append(pool.apply_async(decryptFiles, (key, salt_before, file_division)))
        for thread in threads:
            thread.get()
        pool.close()
        pool.join()
        display('+', f"Merging All the Segments to a Single File...")
        os.system(f"cat {' '.join(files)} > '{file}'")
        display('+', f"Removing Segments...")
        os.system(f"rm {' '.join(files)}")
    os.chdir(str(cwd))
    os.system(f"mv .tmp/{base_name}/{file} downloads/.")

def generateRandom(length):
    letters = string.ascii_letters + "0123456789"
    return ''.join([random.choice(letters) for _ in range(length)])

def makeFolders():
    temporary_folder = cwd / ".tmp"
    temporary_folder.mkdir(exist_ok=True)
    temporary_repository_folder = cwd / ".repositories"
    temporary_repository_folder.mkdir(exist_ok=True)
    user_config_folder = cwd / "configs"
    user_config_folder.mkdir(exist_ok=True) 
    downloads_folder = cwd / "downloads"
    downloads_folder.mkdir(exist_ok=True)

if __name__ == "__main__":
    makeFolders()
    arguments = get_arguments(('-u', "--user", "user", "Github Username"),
                              ('-b', "--branch", "branch", f"Branch of Github Repositories (Default={default_branch})"),
                              ('-U', "--upload", "upload", "Path to File that you want to upload"),
                              ('-e', "--encryption", "encryption", "Encrypt File (None/Before/After/Both, Default=None)"),
                              ('-p', "--private", "private", "Private File (True/False, Default=True)"),
                              ('-z', "--zip-password", "zip_password", "Password for Compressed File (True/False, Default=False)"),
                              ('-d', "--download", "download", "Download a File"))
    if not arguments.user:
        display('-', f"Please Provide a Username")
        exit(0)
    if not arguments.branch:
        display(':', f"Branch Set to {Back.MAGENTA}{default_branch}{Back.RESET}")
        arguments.branch = default_branch
    else:
        default_branch = arguments.branch
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
                public_config = pickle.load(file)
            public_before_zip = public_config["public_before_zip"]
            public_zip = public_config["public_zip"]
            public_after_zip = public_config["public_after_zip"]
            config_salt = public_config["salt"]
            key, _ = generate_key(github_password, config_salt)
            with open(f"configs/{arguments.user}/private_config", 'rb') as file:
                content = file.read()
                private_config = pickle.loads(decrypt(content, key, config_salt))
                private_before_zip = private_config["private_before_zip"]
                private_zip = private_config["private_zip"]
                private_after_zip = private_config["private_after_zip"]
                salt = private_config["salt"]
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
            os.system(f"rm 'configs/{arguments.user}/{file}'")
        public_config = {
            "public_before_zip": public_before_zip,
            "public_zip": public_zip,
            "public_after_zip": public_after_zip,
        }
        private_config = {
            "private_before_zip": private_before_zip,
            "private_zip": private_zip,
            "private_after_zip": private_after_zip,
        }
        key, config_salt = generate_key(github_password)
        public_config["salt"] = config_salt
        private_config["salt"] = salt
        with open(f"configs/{arguments.user}/public_config", 'wb') as file:
            pickle.dump(public_config, file)
        with open(f"configs/{arguments.user}/private_config", 'wb') as file:
            content = encrypt(pickle.dumps(private_config), key, config_salt)
            file.write(content)
        os.chdir(f"configs/{arguments.user}")
        os.system("git add .")
        os.system(f"git commit -m 'Added Configuration Files'")
        os.system(f"git push origin {arguments.branch}")
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
    os.chdir(str(cwd))
    if arguments.upload and os.path.exists(arguments.upload):
        if os.path.isdir(arguments.upload):
            display('-', f"Directories not Supported Currently!")
            exit(0)
        else:
            private = False if arguments.private == "False" else True
            zip_password = True if arguments.zip_password == "True" else False 
            if arguments.encryption:
                if arguments.encryption.lower() == "before":
                    key_before = private_before_zip if private else public_before_zip
                    key_after = None
                elif arguments.encryption.lower() == "after":
                    key_before = None
                    key_after = private_after_zip if private else public_after_zip
                elif arguments.encryption.lower() == "both":
                    key_before = private_before_zip if private else public_before_zip
                    key_after = private_after_zip if private else public_after_zip
                else:
                    key_before = None
                    key_after = None
            else:
                key_before = None
                key_after = None
            if zip_password:
                key_zip = private_zip if private else public_zip
            salt_before, salt_after, repositories, file_size = uploadFile(auth_token, arguments.upload, private, arguments.user, key_before, key_zip, key_after)
            if salt_before == False:
                display('-', f"Error Occurred : {Back.YELLOW}{salt_after}{Back.RESET}")
                exit(0)
            file_name = arguments.upload.split('/')[-1]
            if private:
                if "files" not in private_config:
                    private_config["files"] = {}
                private_config["files"][file_name] = {"salt_before": salt_before, "salt_after": salt_after, "repositories": repositories, "before_zip": key_before, "zip": key_zip, "after_zip": key_after, "file_size": file_size}
            else:
                if "files" not in public_config:
                    public_config["files"] = {}
                public_config["files"][file_name] = {"salt_before": salt_before, "salt_after": salt_after, "repositories": repositories, "before_zip": key_before, "zip": key_zip, "after_zip": key_after, "file_size": file_size}
            with open(f"configs/{arguments.user}/public_config", 'wb') as file:
                pickle.dump(public_config, file)
            key, _ = generate_key(github_password, config_salt)
            with open(f"configs/{arguments.user}/private_config", 'wb') as file:
                content = encrypt(pickle.dumps(private_config), key, config_salt)
                file.write(content)
            os.chdir(f"configs/{arguments.user}")
            os.system("git add .")
            os.system(f"git commit -m 'Added {'Private' if private else 'Public'} File '")
            os.system(f"git push origin {arguments.branch}")
    elif arguments.upload:
        display('-', f"File {Back.YELLOW}{arguments.upload}{Back.RESET} not found!")
        exit(0)
    if arguments.download:
        if "files" in public_config.keys() and arguments.download in public_config["files"].keys():
            private = False
            repositories = public_config["files"][arguments.download]["repositories"]
            key_before = public_config["files"][arguments.download]["before_zip"]
            zip_key = public_config["files"][arguments.download]["zip"]
            key_after = public_config["files"][arguments.download]["after_zip"]
            salt_before = public_config["files"][arguments.download]["salt_before"]
            salt_after = public_config["files"][arguments.download]["salt_after"]
        elif "files" in private_config.keys() and arguments.download in private_config["files"].keys():
            private = True
            repositories = private_config["files"][arguments.download]["repositories"]
            key_before = private_config["files"][arguments.download]["before_zip"]
            zip_key = private_config["files"][arguments.download]["zip"]
            key_after = private_config["files"][arguments.download]["after_zip"]
            salt_before = private_config["files"][arguments.download]["salt_before"]
            salt_after = private_config["files"][arguments.download]["salt_after"]
        else:
            display('-', f"No File Named {Back.YELLOW}{arguments.download}{Back.RESET} Found")
            exit(0)
        downloadFile(arguments.download, arguments.user, repositories, key_before, zip_key, key_after, salt_before, salt_after)