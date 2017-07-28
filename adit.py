#!/usr/bin/env python3

import re
import webbrowser
from html.parser import HTMLParser

import requests

class ADITSession(HTMLParser):

    def handle_starttag(self, tag, attributes):
        for name, value in attributes:
            if name == 'href' and tag == "a":
                self.url = value

    def get_session_id(self):
        """ Return the session ID."""

        matches = re.search("ufid=(.+?)&", self.url)
        if matches and len(matches.groups()) > 0:
            return matches.groups(0)[0]
        else:
            raise ValueError("No session.")

    def get_url(self):
        return self.url

# Start doing the session
session = requests.Session()
request = session.post("http://144.92.167.205/cgi-bin/bmrb-adit/adit-session-driver")


adit = ADITSession()
adit.feed(request.text)
print(test)
