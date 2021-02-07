#!/usr/bin/env python3

import argparse
import base64
import datetime
import httplib2
import logging
import smtplib, ssl
import sys

from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

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
    Send PGP encrypted emails with Gmail. Pipe the body of the email via stdin.""")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="generate additional debug information")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
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


def gmail_send(gmail_resource: Resource, subject: str, body: str, sender: str, recipients: list):
    message = MIMEText(body)
    message['to'] = ",".join(recipients)
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_string().encode('utf-8'))
    body = {'raw': raw_message.decode("utf-8")}

    # The special value "me" for userId indicates the email address of the current user
    return gmail_resource.users().messages().send(userId="me", body=body).execute()


def main():
    """Main program flow"""
    args = parseargs()
    logger = get_logger(args.debug)

    # Read email body from stdin
    file_handle = sys.stdin
    body = file_handle.read()

    gmail_resource = gmail_connect()

    try:
        message = gmail_send(gmail_resource, subject=args.subject, body=body,
                             sender=args.sender, recipients=args.recipients)
        logger.debug(f"Ok: MessageID={message['id']}")
    except Exception as e:
        print(f"Error sending message: {e}")
        exit(1)


if __name__ == '__main__':
    main()
