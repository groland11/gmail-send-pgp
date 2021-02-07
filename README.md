# gmail-send-pgp
Send PGP encrypted emails on the commandline with Gmail

## Oauth and Google API
This script uses **oauth** to authenticate against your Gmail account, and then uses the [Google API](https://developers.google.com/gmail/api/reference/rest "Gmail API Reference") to connect to your Gmail inbox. In order to use or modify this script, you should have a basic understanding of how oauth works.

If you want to use **SMTP with TLS** and authenticate with your username and password instead, you need to allow this kind of access in your Gmail settings. Google considers this as insecure, as you usually store your username/password somewhere within the app or script, and can't use 2FA or solve captchas for access protection.

Oauth is a common standard for logging in to one internet service while using a different existing account from somewhere else. You probably already used oauth to login to a new website by using your Google, Facebook, Twitter or GitHub account. Here is a link where you can check which **apps or websites you already granted authentication access** to your Google account: 

https://myaccount.google.com/permissions?pli=1

## PGP
TODO

## Prerequisites (Ubuntu 20.04 packages)
- python3-googleapi
- python3-oauth2client

You can also install these packages using pip3, but then you have to update them manually.

## Steps to take for oauth authentication
- Go to https://developers.google.com/gmail/api/quickstart/python and click on the **"Enable the Gmail API"** button
- Follow the steps and download the file as **"credentials.json"** into the script directory. Among other data, the file contains most importantly the client id, the redirect uri, and the secret to encrypt further communication with the Google authentication service (take a look at the oauth workflow for further details).
- Run the script in a **local console** or over an SSH connection with X11 forwarding enabled (see usage below).
- If you run the script for the **first time**, it will open your default web browser where you have to login to your Gmail account and grant access rights to the script.
- In the background, the script will receive an authentication code used to access your Gmail account (access token). The token along with some other required data will be stored as **"gmail.storage"** in the script directory.
- For any subsequent runs, the script will reuse the already existing **access token** stored in "gmail.storage".
- Once the access token expires, the script will automatically request and store a new access token using the **refresh token** which is also stored in "gmail.storage".
- When the **refresh token also expires** (if you change your password or if you haven't used the refresh token for more then 6 months), you have to repeat the steps.

## Usage
```
pysendpgp.py [-h] [-d] [-v] -r SENDER -s SUBJECT [-V] recipients

Script description

positional arguments:
  recipients            list of email recipients separated by spaces

optional arguments:
  -h, --help            show this help message and exit
  -d, --debug           generate additional debug information
  -v, --verbose         increase output verbosity
  -r SENDER, --sender SENDER
                        email sender
  -s SUBJECT, --subject SUBJECT
                        email subject
  -V, --version         show program's version number and exit
```

## Examples

