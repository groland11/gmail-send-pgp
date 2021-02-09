# gmail-send-pgp
Send PGP signed and encrypted emails on the Linux command line with Gmail

## OAuth and Google API
This script uses **OAuth 2.0** to authenticate against your Gmail account, and then uses the [Google API](https://developers.google.com/gmail/api/reference/rest "Gmail API Reference") to connect to your Gmail inbox. In order to use or modify this script, you should have a [basic understanding of how OAuth works](https://developers.google.com/identity/protocols/oauth2).

If you want to use **SMTP with TLS** and authenticate with your username and password instead, you need to allow this kind of access in your Gmail settings. Google considers this as insecure, as you usually store your username/password somewhere within the app or script, and can't use 2FA or solve captchas for access protection.

OAuth is a common standard for logging in to one internet service while using a different existing account from somewhere else. You probably already used OAuth to login to a new website by using your Google, Facebook, Twitter or GitHub account. Here is a link where you can check which **apps or websites you already granted authentication access** to your Google account: 

https://myaccount.google.com/permissions?pli=1

## Steps to take for OAuth authentication
- Go to https://developers.google.com/gmail/api/quickstart/python and click on the **"Enable the Gmail API"** button.
- Follow the steps and download the file as **"credentials.json"** into the script directory. Among other data, the file contains most importantly the client id, the redirect uri, and the secret to encrypt further communication with the Google authentication service (take a look at the OAuth workflow for further details).
- Run the script in a **local console** or over an SSH connection with X11 forwarding enabled (see usage below).
- If you run the script for the **first time**, it will open your default web browser where you have to login to your Gmail account and grant access rights to the script.
- In the background, the script will receive an authentication code used to access your Gmail account (access token). The token along with some other required data will be stored as **"gmail.storage"** in the script directory.
- For any subsequent runs, the script will reuse the already existing **access token** stored in "gmail.storage".
- Once the access token expires, the script will automatically request and store a new access token using the **refresh token** which is also stored in "gmail.storage".
- When the **[refresh token expires](https://developers.google.com/identity/protocols/oauth2#expiration)** (if you change your password or if you haven't used the refresh token for more then 6 months), you have to repeat these steps.

## PGP
- First you need to create your own **public and private PGP key pair**. There is an addon for Google Chrome called **[FlowCrypt](https://flowcrypt.com)** that lets you easily create your own PGP key pair. It also lets you send and receive signed and encrypted emails from within the Gmail web interface. Of course you can also use a PGP key pair that you created locally on your computer.
- Next you need to download your new public and private key and **import them into your GnuPG keyring**:
  * ```gpg --import yourcertificate.asc``` 
  * ```gpg --import yourkey.asc```
- Your PGP private key will be used to **sign outgoing messages**.
- For any **recipient** you also need to import their public key into your keyring:
  * ```gpg --import recipient.asc```
- The recipient's PGP public key will be used to **encrypt outgoing messages**.  
- Make sure that the **sender and recipient email addresses** match the email addresses in your keyring:
  * ```gpg -k``` Displays all public keys in your keyring.
  * ```gpg -K``` Display all private keys in your keyring.

#### Notes
- Make sure you have configured the right **password input method** on your terminal. You need to input a password to unlock your private PGP key for message signing.
  * On Ubuntu: ```sudo update-alternatives --config pinentry```
- If you have trouble typing in your password over **remote connections** (e.g. SSH), try this first before you run the script:
  * ```export GPG_TTY=$(tty)```

#### Optional
- In order for others to find your public PGP key more easily, you may **upload the public key to** https://keys.openpgp.org .
- If you have a **German eID**, you may [sign your public key with your eID card](https://pgp.governikus.de/pgp/). This will prove that the public PGP key really belongs to you.

## Prerequisites (Ubuntu 20.04 packages)
- python3-googleapi
- python3-oauth2client
- python3-gpg

You can also install these packages using pip3, but then you have to update them manually whenever there is a bugfix or security patch.

## Usage
```
gmailsendpgp.py [-h] [-d] [-v] -r SENDER -s SUBJECT [-V] recipients

Send PGP encrypted emails with Gmail. Pipe the body of the email via stdin.

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
Send the contents of a text file:
```
cat message.txt | ./gmailsendpgp.py -r myaccount@gmail.com -s "This is a test" test@example.com
```
Interactively type the body of an email:
```
./gmailsendpgp.py -r myaccount@gmail.com -s "This is a test" test@example.com
This is the body of my email.
Nice, it works.
<CTRL+D>
```
