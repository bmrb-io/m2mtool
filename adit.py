#!/usr/bin/env python3

from __future__ import print_function

import re
import sys
import logging

PY3 = (sys.version_info[0] == 3)
if PY3:
    from io import StringIO
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser
    from cStringIO import StringIO

import requests

#ssh adit@adit-alpha
#/home/adit/adit/www/adit/sessions/bmrb-adit
#/adit/www/adit/scratch/upload/

# Set up logging
logging.basicConfig()

class ADITSession():
    """ A class to manage the session. """

    sid = None
    session = None
    nmrstar_file = None

    server = 'http://144.92.167.205'
    file_types = {
    "upload_category_1": "Assigned NMR chemical shifts",
    "upload_category_2": "Scalar coupling constants",
    "upload_category_3": "Auto relaxation parameters",
    "upload_category_4": "Tensor data",
    "upload_category_5": "Interatomic distance data",
    "upload_category_6": "Chemical shift anisotropy",
    "upload_category_7": "Heteronuclear NOEs",
    "upload_category_8": "T1 (R1) NMR relaxation data",
    "upload_category_9": "T2 (R2) NMR relaxation data",
    "upload_category_10": "T1rho (R1rho) NMR relaxation data",
    "upload_category_11": "Order parameters",
    "upload_category_12": "Dynamics trajectory file",
    "upload_category_13": "Dynamics movie file",
    "upload_category_14": "Residual dipolar couplings",
    "upload_category_15": "Hydrogen exchange rates",
    "upload_category_16": "Hydrogen exchange protection data",
    "upload_category_17": "Chemical rate constants",
    "upload_category_18": "Spectral peak lists",
    "upload_category_19": "Dipole-dipole couplings",
    "upload_category_20": "Quadrupolar couplings",
    "upload_category_21": "Homonuclear NOEs",
    "upload_category_22": "Dipole-dipole relaxation data",
    "upload_category_23": "Dipole-dipole cross correlation data",
    "upload_category_24": "Dipole-CSA cross correlation data",
    "upload_category_25": "Binding constants",
    "upload_category_26": "NMR-derived pH transitions (pKa's; pHmid's)",
    "upload_category_27": "NMR-derived D/H fractionation factors",
    "upload_category_28": "Theoretical (calculated) chemical shift values",
    "upload_category_29": "Theoretical coupling constants",
    "upload_category_30": "Theoretical heteronuclear NOEs",
    "upload_category_31": "Theoretical T1 values",
    "upload_category_32": "Theoretical T2 values",
    "upload_category_33": "Spectral density factors",
    "upload_category_34": "Time-domain data (raw spectral data)",
    "upload_category_35": "Molecular orientations",
    "upload_category_36": "Secondary structure features",
    "upload_category_37": "Atomic coordinates",
    "upload_category_38": "Mass spectrometry data",
    "upload_category_39": "Other kinds of data",
    "Image": "An image"
}

    def __init__(self, nmrstar_file, sid=None, server=None):
        self.nmrstar_file = nmrstar_file
        self.sid = sid
        if server:
            self.server = server

    def __enter__(self):
        """ Start the session.

        Creates a python requests Session() and starts an ADIT-NMR session."""

        if self.sid != None:
            return self

        self.session = requests.Session()

        logging.info("Creating session.")
        values = {'moltype':'prot', 'expmeth': 'nmr', 'context': 'deposit',
                  'applname': 'adit', 'email': 'bmrbhelp@bmrb.wisc.edu',
                  'return_url': '/'}
        r = self.session.post("%s/cgi-bin/bmrb-adit/adit-session-driver" % self.server,
                              data=values)

        # Find the session ID
        self.sid = ADITSession._get_session_id(r.text)
        logging.info("Session ID: %s" % self.sid)

        # Activate the session (don't know why this is needed...)
        logging.info("Activating session.")
        self.session.get(ADITSession._get_activate_url(r.text))

        # If there was an error closing the session raise it
        r.raise_for_status()

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """ End the current session."""

        logging.info("Upload the session NMR-STAR file.")
        self.upload_file('upload_category_39', self.nmrstar_file)

        logging.info("Ask session to process uploaded files.")
        values = {'ufid': self.sid, 'context': 'deposit-en', 'dbname': '',
                  'email': 'bmrbhelp@bmrb.wisc.edu', 'archdir': 'bmrb', 'expmeth': 'NMR',
                  'moltype': '', 'form_has_been_submitted': 1,
                  'upload_submit': 'CONTINUE DEPOSITION'}
        r = self.session.post("%s/cgi-bin/bmrb-adit/upload-req-shifts" % self.server,
                              data=values, files=[('upload_name',StringIO(""))])
        r.raise_for_status()

        # End the HTTP session
        self.session.close()

    def upload_file(self, file_type, file_name):
        """ Uploads a given file to the session.

        the_file should be a (filename, type) tuple. """

        url = '%s/cgi-bin/bmrb-adit/upload-req-shifts' % self.server
        files = {'upload_fname': open(file_name, 'rb')}
        values = {'ufid': self.sid, 'context': 'deposit-en', 'dbname': '',
                  'email': 'bmrbhelp@bmrb.wisc.edu', 'archdir': 'bmrb', 'expmeth': 'NMR',
                  'moltype': '', 'form_has_been_submitted': 1,
                  'prev_upload_dir': '/adit/www//adit/scratch/upload/%s/' % self.sid ,
                  'upload_submit': 'Upload'}

        if file_type == "Image":
            values['upload_category'] = 'Image'
        else:
            values['upload_category'] = 'NMR-STAR'
            values[file_type] = self.file_types[file_type]

        logging.info("Sending file '%s' with type '%s'.", file_name, self.file_types[file_type])
        r = self.session.post(url, files=files, data=values)
        r.raise_for_status()

    def get_session_url(self):
        """ Returns the session URL."""

        return "%s/cgi-bin/bmrb-adit/mk-top-interface-screen-view?ufid=%s" % (self.server, self.sid)

    @staticmethod
    def _get_session_id(text):
        """ Returns the session ID."""

        matches = re.search("ufid=(.+?)&", text)
        if matches and len(matches.groups()) > 0:
            return matches.groups(0)[0]
        else:
            raise ValueError("No session.")

    @staticmethod
    def _get_activate_url(text):
        """ Returns the session ID."""

        matches = re.search("URL='*(.+?)'*\"", text)
        if matches and len(matches.groups()) > 0:
            return matches.groups(0)[0]
        else:
            raise ValueError("No session.")


