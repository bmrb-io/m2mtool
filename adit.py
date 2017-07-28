#!/usr/bin/env python3

import re
import logging
import webbrowser
from html.parser import HTMLParser

import requests

# Set up logging
logging.basicConfig()

def get_session_id(text):
    """ Returns the session ID."""

    matches = re.search("ufid=(.+?)&", request.text)
    if matches and len(matches.groups()) > 0:
        return matches.groups(0)[0]
    else:
        raise ValueError("No session.")

def get_activate_url(text):
    """ Returns the session ID."""

    matches = re.search("URL=(.+?)\"", request.text)
    if matches and len(matches.groups()) > 0:
        return matches.groups(0)[0]
    else:
        raise ValueError("No session.")

# Start the ADIT session
with requests.Session() as session:
    logging.info("Creating session.")
    request = session.post("http://144.92.167.205/cgi-bin/bmrb-adit/adit-session-driver")

    # Find the session ID
    sid = get_session_id(request.text)
    logging.info("Session ID: %s" % sid)

    # Activate the session (don't know why this is needed...)
    logging.info("Activating session.")
    request = session.get(get_activate_url(request.text))

print(sid)
