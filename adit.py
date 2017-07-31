#!/usr/bin/env python3

from __future__ import print_function

import re
import sys
import logging
import webbrowser

PY3 = (sys.version_info[0] == 3)
if PY3:
    from html.parser import HTMLParser
else:
    from HTMLParser import HTMLParser

import requests

#ssh adit@adit-alpha
#/home/adit/adit/www/adit/sessions/bmrb-adit
#/adit/www/adit/scratch/upload/

# Set up logging
logging.basicConfig()

ADIT_SERVER = 'http://144.92.167.205'
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


def get_session_id(text):
    """ Returns the session ID."""

    matches = re.search("ufid=(.+?)&", text)
    if matches and len(matches.groups()) > 0:
        return matches.groups(0)[0]
    else:
        raise ValueError("No session.")

def get_activate_url(text):
    """ Returns the session ID."""

    matches = re.search("URL='*(.+?)'*\"", text)
    if matches and len(matches.groups()) > 0:
        return matches.groups(0)[0]
    else:
        raise ValueError("No session.")

def upload_file(the_file, session, key, image=False):
    """ Uploads a given file to the session.

    the_file should be a (filename, type) tuple. """

    url = '%s/cgi-bin/bmrb-adit/upload-req-shifts' % ADIT_SERVER
    files = {'upload_fname': open(the_file[1], 'rb')}
    values = {'ufid': key, 'context': 'deposit-en', 'dbname': '',
              'email': 'wedell@bmrb.wisc.edu', 'archdir': 'bmrb', 'expmeth': 'NMR',
              'moltype': '', 'form_has_been_submitted': 1,
              'prev_upload_dir': '/adit/www//adit/scratch/upload/%s/' % key ,
              'upload_submit': 'Upload'}

    if image:
        values['upload_category'] = 'Image'
    else:
        values['upload_category'] = 'NMR-STAR'
        values[the_file[0]] = file_types[the_file[0]]

    logging.info("Sending file '%s' with type '%s'.", the_file[1], file_types[the_file[0]])
    request = session.post(url, files=files, data=values)

    # Activate the upload (don't know why this is needed...)
    logging.info("Activating file upload pt1.", the_file[1])
    request = session.get("%s/cgi-bin/bmrb-adit/mk-top-interface-screen-view?ufid=%s" % (ADIT_SERVER, key))


def upload_files(flist):
    """ Uploads all of the files to ADIT. flist should be a dictionary
    of {file_path: file_type} where the file_type is populated from the
    dictionary file_types. """

    pass

# Start the ADIT session
def start_session():
    """ Starts a session. """

    with requests.Session() as session:
        logging.info("Creating session.")
        values = {'moltype':'prot', 'expmeth': 'nmr', 'context': 'deposit',
                  'applname': 'adit', 'email': 'bmrbhelp@bmrb.wisc.edu',
                  'return_url': '/'}
        request = session.post("%s/cgi-bin/bmrb-adit/adit-session-driver" % ADIT_SERVER,
                               data=values)

        # Find the session ID
        sid = get_session_id(request.text)
        logging.info("Session ID: %s" % sid)

        # Activate the session (don't know why this is needed...)
        logging.info("Activating session.")
        session.get(get_activate_url(request.text))

        upload_file(['Image', "/tmp/test2"], session, sid, image=True)
        upload_file(['upload_category_29', "/tmp/test"], session, sid)
        upload_file(['upload_category_32', "/tmp/test_re"], session, sid)

        print(sid)


if __name__ == "__main__":
    start_session()

