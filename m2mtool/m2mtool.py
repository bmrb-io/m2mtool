#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  m2mtool.py
#
#  Copyright 2021 Jon Wedell <wedell@uchc.edu>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

import json
import logging
import os
import sys
import time
import webbrowser
from tempfile import NamedTemporaryFile

import pynmrstar
import requests

import m2mtool.bmrbdep as bmrbdep
import m2mtool.file_selector as file_selector
from m2mtool.configuration import configuration
from m2mtool.helpers import ApiSession

#########################
# Module initialization #
#########################

# Set up logging
logging.basicConfig()


def get_vm_version() -> str:
    """ Returns the version of the VM that is running."""

    try:
        with open('/etc/nmrbox.d/motd-identifier', 'r') as motd:
            return motd.readline().split(":")[1].strip()
    except (IOError, ValueError):
        logging.error('Could not determine the version of NMRbox running on this machine.')
        return 'unknown'


def create_deposition(path) -> None:
    # If the sessions exists, re-open it

    session_file = os.path.join(path, '.bmrbdep_session')
    if os.path.isfile(session_file):
        logging.info("Loading existing session...")
        session_info = json.loads(open(session_file, "r").read())

        bmrbdep_session = bmrbdep.BMRBDepSession(sid=session_info['sid'])
        webbrowser.open_new_tab(bmrbdep_session.session_url)
        sys.exit(0)

    # Run the file selector
    nickname, selected_files = file_selector.run_file_selector(path)

    # Fetch the software list
    with ApiSession() as api:
        try:
            url = f"{configuration['api_root_url']}/user/get-bmrbdep-metadata"
            r = api.get(url, json={'path': path, 'vm_id': get_vm_version()})
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Encountered error when retrieving BMRBdep session metadata: %s", err)
            raise IOError('Encountered error when retrieving BMRBdep session metadata.')

        try:
            with NamedTemporaryFile() as star_file:
                star_file.write(r.text.encode())
                star_file.flush()
                star_file.seek(0)

                user_email = pynmrstar.Entry.from_string(r.text).get_tag('_Contact_person.Email_address')[0]

                with bmrbdep.BMRBDepSession(nmrstar_file=star_file,
                                            user_email=user_email,
                                            nickname=nickname) as bmrbdep_session:

                    # Run the progress bar, which handles uploading of data files
                    file_selector.run_progress_bar(bmrbdep_session, selected_files, path)

                    # Delete the metadata file from the "upload file" list
                    bmrbdep_session.delete_file('m2mtool_generated.str')

                with open(session_file, "w") as session_log:
                    session_info = {"sid": bmrbdep_session.sid, "ctime": time.time()}
                    session_log.write(json.dumps(session_info))

                # Open the session
                webbrowser.open_new_tab(bmrbdep_session.session_url)
                time.sleep(3)

        except IOError as err:
            file_selector.show_error(err)


# Run the code in this module
def run_m2mtool():
    if len(sys.argv) != 2:
        raise ValueError('Please supply the path to the folder that is being deposited.')
    try:
        create_deposition(sys.argv[1])
    except Exception as err:
        logging.critical(str(err))
        raise err
