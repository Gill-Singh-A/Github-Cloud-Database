# Github Cloud Database
A Python Programs that uses Github Repositories as a Cloud Service to store Files
## Requirements
Language Used = Python3<br />
Modules/Packages used:
* requests
* json
* os
* pickle
* base64
* string
* random
* shutil
* math
* getpass
* pathlib
* datetime
* optparse
* colorama
* multiprocessing
* time
* cryptography
<!-- -->
Install the dependencies:
```bash
pip install -r requirements.txt
```
## Setup
* Make a dummy Github Account (Account that should not be used for any other purposes, because it may get very frustrating if you use your daily-use Github Account)
* Go to [Github Personal Access Token Generation](https://github.com/settings/personal-access-tokens/new) and Generate a New Token with **Repository Access** set to *All* & *Read and Write* Access on **Administration** and **Contents** under ***Repositories Permissions***
<!-- --><br />
![Repository Access](/assets/images/all_repositories.png)<br />
![Administration Permissions](/assets/images/administrator_read_write.png)<br />
![Content Permissions](/assets/images/content_read_write.png.png)<br />
## Encryption Passwords
* It uses AES-256 Symmetric Encryption Algorithm for Encrypting the files.
* There are 4 Passwords for this encryption that it takes:
    * Public (For Public Files)
        * Before Compressing
        * After Compressing
    * Private (For Private Files)
        * Before Compressing
        * After Compressing
* When it Compresses the File, *.zip* format is used. Therefore an option is provide to protect the zip file with password or not.
* You can manually enter the passwords at the first time run of the program *main.py*, but it can be also Autogenerated. The Autogenerated Password Consists uppercase, lowercase and integers as characters and is 50 Characters long.
* The Encryption and Password Protection is useless for current version, becuase it makes no sense to protect a file that is supposed to be Public and also have its passwords, keys and salts Publically available. And also Private Files, who's password are although stored in ***storage_config*** repository but are encrypted (as they're private files and can only be accessed by the Owner of the Account with Github API Token).
* The Idea to introduce passwords is based on a future implementation of sharing files with specific users only, by using custom passwords instead of the passwords available in Publically Available Configuration Files.
* We have the option to Encrypt the Files Before/Afterr Compressing or Both the time or no encryption.
* Also same is for the zip files, option is present to store without password and with password.
## Storage Configuration Files
* The Storage Configuration Files are stored in a Public Repository Named ***storage_config***<br />
* It contains 2 Pickle files:
    * private_config
    * public_config
* The Private Config is Encrypted
* They Contain the following Data:
    * Encryption and Zip Passwords
    * Salts for AES-256 Symmetric Encryptions
    * File Data
        * Associated Repositories
        * Encryption and Zip Passwords (again storing with keeping in the mind the future implementation of sharing files with specific users only, by using custom passwords instead of the passwords available in Publically Available Configuration Files)
        * Salts for AES-256 Symmetric Encryptions
        * File Size
        * Split Size (Used to remove error caused by Expansion of Data by Padding in AES-256 Encryption)
### Note
* This Only works for Linux based Operating Systems (as it uses Linux System Commands)
* Only use a dummy Github Account for this, else everything will get messed up
* The Downloaded Files will be saved to ***downloads*** folder.
* Before running ***main.py*** make sure that ***.tmp*** and ***.repository*** folders are empty. You can empty them by running ***clean.sh***