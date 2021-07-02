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
import webbrowser

import m2mtool.bmrbdep as bmrbdep
import m2mtool.file_selector as file_selector

# Set up logging
logging.basicConfig()


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

    # Run the file uploader
    file_selector.run_progress_bar(path, nickname, selected_files, session_file)


# Run the code in this module
def run_m2mtool():
    if len(sys.argv) != 2:
        raise ValueError('Please supply the path to the folder that is being deposited.')
    try:
        create_deposition(sys.argv[1])
    except Exception as err:
        logging.critical(str(err))
        raise err
