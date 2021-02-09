#!/usr/bin/env python3

import argparse
import base64
import datetime
import gnupg
import httplib2
import logging
import sys

from email.header import Header
from email.message import Message
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders

from googleapiclient.discovery import build, Resource
from oauth2client.client import flow_from_clientsecrets, Credentials
from oauth2client.file import Storage
from oauth2client.tools import run_flow


class LogFilter(logging.Filter):
    def filter(self, record):
        return record.levelno in (logging.DEBUG, logging.INFO)


def parseargs():
    """Process command line arguments"""
    parser = argparse.ArgumentParser(description="""
    Send PGP signed and encrypted emails with Gmail. Pipe the body of the email via stdin.""")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="generate additional debug information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("-p", "--pgp", action="store_true",
                        help="sign and encrypt email with gnupg")
    parser.add_argument("-r", "--sender", type=str, required=True,
                        help="email sender")
    parser.add_argument("-s", "--subject", type=str, required=True,
                        help="email subject")
    parser.add_argument("recipients", type=str, action="append",
                        help="list of email recipients separated by spaces")
    parser.add_argument("-V", "--version", action="version", version="1.0.0")
    return parser.parse_args()


def get_logger(debug: bool = False) -> logging.Logger:
    """Retrieve logging object"""
    logger = logging.getLogger()
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    h1 = logging.StreamHandler(sys.stdout)
    h1.setLevel(logging.DEBUG)
    h1.addFilter(LogFilter())

    h2 = logging.StreamHandler(sys.stderr)
    h2.setLevel(logging.ERROR)

    logger.addHandler(h1)
    logger.addHandler(h2)

    return logger


def get_signature(cleartext: str) -> Message:
    # Private key is automatically selected by GnuPG
    # Password for private key has to be provided by a running gpg agent
    gpg = gnupg.GPG()
    signature = str(gpg.sign(cleartext, detach=True))

    message = MIMEApplication(signature, _subtype='pgp-signature; name="signature.asc',
                              _encoder=encoders.encode_noop)
    message.add_header("Content-Description", "OpenPGP digital signature")
    message.add_header("Content-Disposition", 'attachment; filename="signature.asc"')
    message.add_header("Content-Transfer-Encoding", "7bit")

    return message


def get_encrypted(msgtext: str, recipient: str):
    gpg = gnupg.GPG()

    encrypted = gpg.encrypt(msgtext, recipient, always_trust=True)
    if not encrypted.ok:
        # encrypted.status
        # encrypted.stderr
        # TODO: Raise RuntimeException
        return None

    return str(encrypted)


def gmail_connect() -> Resource:
    # Credentials file retrieved from developer console https://developers.google.com/gmail/api/quickstart/python
    secret_file = "credentials.json"

    # Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
    oauth_scope = 'https://www.googleapis.com/auth/gmail.compose'

    # Start the OAuth flow
    flow = flow_from_clientsecrets(secret_file, scope=oauth_scope)
    stg = Storage('gmail.storage')
    http = httplib2.Http()

    # Try to retrieve authenticaiton code from local storage or run the flow to retrieve it
    credentials: Credentials = stg.get()
    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, stg, http=http)

    # Authorize the httplib2.Http object with our credentials
    http = credentials.authorize(http)

    # Build the Gmail service from discovery
    gmail_service = build('gmail', 'v1', http=http)

    return gmail_service


def gmail_send(gmail_resource: Resource, subject: str, body: str, sender: str, recipients: list,
               encrypt: bool=False):
    """
    TODO:
    - PGP signature is currently not working
    - PGP/MIME encryption is not working as expected (s. comments below)
    """
    status_text = ""
    gmail_result = {}

    # MIME type/subtype is "text/plain", charset is automatically detected ("us-ascii" or "utf-8")
    msg_text = MIMEText(body)
    msg_sign = get_signature(msg_text.as_string().replace('\n', '\r\n'))

    msg = MIMEMultipart(_subtype="signed", micalg="pgp-sha512",
                        protocol="application/pgp-signature")
    msg.attach(msg_text)
    msg.attach(msg_sign)

    if encrypt:
        try:
            encrypted = get_encrypted(body, recipients[0])
        except RuntimeError as e:
            status_text = str(e)
        else:
            if False:
                # PGP/MIME encrypted message as described by https://de.wikipedia.org/wiki/PGP/MIME
                # Somehow it is not working, probably because Gmail iw rewriting the MIME parts ...
                msg = MIMEMultipart(_subtype="encrypted", protocol="application/pgp-encrypted")
                msg_desc = MIMEApplication(_data="Version: 1\n", _subtype="pgp-encrypted",
                                           _encoder=encoders.encode_noop)
                msg_desc.add_header("Content-Description", "PGP/MIME version identification")
                msg_enc = MIMEApplication(_data=encrypted, _subtype='octet-stream; name="encrypted.asc"',
                                          _encoder=encoders.encode_noop)
                msg_enc.add_header("Content-Description", "OpenPGP encrypted message")
                msg_enc.add_header("Content-Disposition", 'inline; filename="encrypted.asc"')
                msg.attach(msg_desc)
                msg.attach(msg_enc)
            else:
                # ... so this is the next best thing which is currently working with Gmail
                msg = MIMEText(encrypted)

    msg['To'] = ",".join(recipients)
    msg['From'] = sender
    msg['Subject'] = Header(subject, 'utf-8') # Enable utf-8 characters in email subject
    #print(msg.as_string())

    # Gmail specific message encoding
    raw_message = base64.urlsafe_b64encode(msg.as_string().encode('utf-8'))
    body = {'raw': raw_message.decode("utf-8")}

    # The special value "me" for userId indicates the email address of the current user
    gmail_result = gmail_resource.users().messages().send(userId="me", body=body).execute()

    return (status_text, gmail_result)

def main():
    """Main program flow"""
    args = parseargs()
    logger = get_logger(args.debug)

    # Read email body from stdin
    file_handle = sys.stdin
    body = file_handle.read()

    gmail_resource = gmail_connect()

    try:
        (status, result) = gmail_send(gmail_resource, subject=args.subject, body=body,
                             sender=args.sender, recipients=args.recipients,
                             encrypt=args.pgp)
        logger.debug(f"MessageID={result.get('id')}, {status}")
    except Exception as e:
        print(f"Error sending message: {e}")
        exit(1)


if __name__ == '__main__':
    main()
