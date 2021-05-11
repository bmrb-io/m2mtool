#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  m2mtool.py
#
#  Copyright 2017 Jon Wedell <wedell@bmrb.wisc.edu>
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
import file_selector
import xml.etree.cElementTree as ET
from html import escape as html_escape
from pathlib import Path
from tempfile import NamedTemporaryFile
from helpers import ApiSession

import bmrbdep

try:
    from zenipy import error as display_error, entry as get_input
except ImportError:
    def display_error(text):
        print('An error occurred: %s' % text)

    def get_input(prompt):
        return input(prompt + ": ")

import pynmrstar
import requests

#########################
# Module initialization #
#########################

# Load the configuration
from configuration import configuration

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def get_software(api: ApiSession.requests_session, vm_id=None):
    """ Returns a dictionary of the known software packages."""

    # Determine the VM version
    if not vm_id:
        vm_id = get_vm_version()

    logging.info("Getting software information.")

#     with PostgresHelper(database='staging') as cur:
#         cur.execute('''
# SELECT slug,url,software_path,version,synopsis
#   FROM software as sw
#   LEFT JOIN software_versions as sv
#     ON sw.id = sv.software_id
#   LEFT JOIN software_version_vm as svvm
#     ON svvm.software_version_id = sv.id
#   WHERE svvm.vm_id = %s''', [vm_id])
#
#         return {x['software_path']: x for x in cur}

    # with requests.Session() as s:
    #     try:
    #         r = s.get('https://apidev.nmrbox.org/user/automatic-login', params={'token': get_token()})
    #         r.raise_for_status()
    #         r = s.get('https://apidev.nmrbox.org/user/get-software', params={'vm_id': vm_id})
    #         r.raise_for_status()
    #     except requests.exceptions.HTTPError as err:
    #         logging.exception("Encountered error when retrieving software: \n%s", err)
    #     return r.json()
    try:
        r = api.get('https://apidev.nmrbox.org/user/get-software', params={'vm_id': vm_id})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.exception("Encountered error when retrieving software: \n%s", err)
    return r.json()


def get_user_email():
    # with PostgresHelper(database='staging') as cur:
    #     cur.execute('''SELECT email FROM persons WHERE uid=%s''', [os.getuid()])
    #     return cur.fetchone()['email']

    # with requests.Session() as s:
    #     try:
    #         r = s.get('https://apidev.nmrbox.org/user/automatic-login', params={'token': get_token()})
    #         r.raise_for_status()
    #         r = s.get('https://apidev.nmrbox.org/user/person')
    #         r.raise_for_status()
    #     except requests.exceptions.HTTPError as err:
    #         logging.exception("Encountered error when retrieving user info: \n%s", err)
    #     return r.json()['data']['email']

    with ApiSession() as api:
        try:
            r = api.get('https://apidev.nmrbox.org/user/person')
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Encountered error when retrieving user info: \n%s", err)
        return r.json()['data']['email']


def get_entry_saveframe():
    """ Returns information about the NMRbox user. """

    entry = pynmrstar.Saveframe.from_scratch("entry_information", "_Entry")
    entry.add_tags([["Sf_category", "entry_information"], ["Sf_framecode", "entry_information"]])

    # Create the contact person loop
    contact_person = pynmrstar.Loop.from_scratch("_Contact_person")
    contact_person.add_tag(["ID", "Email_address", "Given_name", "Family_name",
                            "Department_and_institution", "Address_1",
                            "Address_2", "Address_3", "City", "State_province",
                            "Country", "Postal_code", "Role", "Organization_type"])

#     with PostgresHelper(database="staging") as cur:
#         cur.execute('''
# SELECT institution_type as user_type, ins.name AS institution, p.*
# FROM persons as p
#          LEFT JOIN institutions AS ins
#                    ON ins.id = p.institution_id
# WHERE p.uid = %s''', [os.getuid()])
#         person = cur.fetchone()

    # with requests.Session() as s:
    #     try:
    #         r = s.get('https://apidev.nmrbox.org/user/automatic-login', params={'token': get_token()})
    #         r.raise_for_status()
    #         r = s.get('https://apidev.nmrbox.org/user/get-person-institution')
    #         r.raise_for_status()
    #     except requests.exceptions.HTTPError as err:
    #         logging.exception("Encountered error when retrieving person and institution info: \n%s", err)
    #     person = r.json()
    with ApiSession() as api:
        try:
            r = api.get('https://apidev.nmrbox.org/user/get-person-institution')
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            logging.exception("Encountered error when retrieving person and institution info: \n%s", err)
        person = r.json()

    for x in person.keys():
        person[x] = "." if person[x] == "" else person[x]
    contact_person.add_data([1, person['email'], person['first_name'],
                             person['last_name'], person['department'] + " " + person['institution'],
                             person['address1'], person['address2'],
                             person['address3'], person['city'],
                             person['state_province'], person['country'],
                             person['zip_code'], person['job_title'],
                             person['user_type'].lower()])

    # Create the entry_author loop
    entry_author = pynmrstar.Loop.from_scratch("_Entry_author")
    entry_author.add_tag(["Ordinal", "Given_name", "Family_name"])
    entry_author.add_data([1, person['first_name'], person['last_name']])

    # Add the children loops
    entry.add_loop(contact_person)
    entry.add_loop(entry_author)

    # Create the citation saveframe
    citation = pynmrstar.Saveframe.from_scratch("citations", "_Citation")
    citation.add_tags([["Sf_category", "citations"], ["Sf_framecode", "citations"]])
    citation_author = pynmrstar.Loop.from_scratch("_Citation_author")
    citation_author.add_tag(["Ordinal", "Given_name", "Family_name"])
    citation_author.add_data([1, person['first_name'], person['last_name']])
    citation.add_loop(citation_author)

    return [entry, citation]


def build_entry(software_packages):
    """ Builds a NMR-STAR entry. Pass a list of
    software package dictionary (as returned by get_software)."""

    logging.info("Building software saveframe.")

    entry = pynmrstar.Entry.from_scratch('NEED_ACC_NUM')

    for frame in get_entry_saveframe():
        entry.add_saveframe(frame)

    # Add NMRbox
    software_packages.append({'slug': 'NMRbox',
                              'version': get_vm_version(),
                              'synopsis': 'NMRbox is a cloud-based virtual machine loaded with NMR software.',
                              'first_name': 'NMRbox Team',
                              'last_name': None,
                              'email': 'support@nmrbox.org'})

    package_id = 1
    for package in software_packages:
        frame = pynmrstar.Saveframe.from_template("software", package['slug'])

        try:
            entry.add_saveframe(frame)
        except ValueError:
            continue

        frame.add_tag("ID", package_id, update=True)
        frame.add_tag("Name", package['slug'], update=True)
        frame.add_tag("Version", package['version'], update=True)
        frame.add_tag("Details", package['synopsis'], update=True)

        # Add to the vendor loop if we have useful data
        first_name = package["first_name"]
        last_name = package["last_name"]
        if not first_name and not last_name:
            name = None
        elif not first_name:
            name = last_name
        elif not last_name:
            name = first_name
        else:
            name = first_name + " " + last_name
        vendor = [name, None, package["email"], None, package_id]
        if vendor[0] or vendor[1] or vendor[2]:
            frame['_Vendor'].add_data(vendor)

        package_id += 1

    return entry


def get_user_activity(directory, api: ApiSession.requests_session):
    """ Prints a summary of the users activity."""

    logging.info("Fetching user command activity.")

#     with PostgresHelper() as cur:
#         cur.execute('''
# SELECT current_dir,exe,command_line FROM usage.process
#   WHERE uid = %s AND current_dir LIKE %s AND month = 11 and year=2020;''',
#                     [os.getuid(), directory + "%"])
#         return cur.fetchall()
#
#     with requests.Session() as s:
#         try:
#             r = s.get('https://apidev.nmrbox.org/user/automatic-login', params={'token': get_token()})
#             r.raise_for_status()
#             r = s.get('https://apidev.nmrbox.org/user/get-user-activity', params={'directory': directory})
#             r.raise_for_status()
#         except requests.exceptions.HTTPError as err:
#             logging.exception("Encountered error when retrieving user activity: \n%s", err)
#         return r.json()

    try:
        r = api.get('https://apidev.nmrbox.org/user/get-user-activity', params={'directory': directory})
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        logging.exception("Encountered error when retrieving user activity: \n%s", err)
    return r.json()


def get_vm_version():
    """ Returns the version of the VM that is running."""

    # Remove once the DB is updated
    return "2"

    # Get the NMRBox version from the xml
    with open("/etc/nmrbox_version.xml", "r") as nmr_version_file:
        root = ET.parse(nmr_version_file).getroot()
        version = next(root.iter("version")).text

        return version[:version.index("-")]

    # Assume the latest version in the absence of the necessary info
    return configuration['latest_vm_version']


def get_modified_time(path):
    """ Returns the last modified time of the file/folder."""

    return os.path.getmtime(path)


def filter_software(all_packages, path, api: ApiSession.requests_session):
    """ Returns the software packages used by this user in the selected
    directory. """

    activities = []
    activities_dict = {}

    for activity in get_user_activity(path, api):
        if not activity['exe'].startswith("/usr/software"):
            continue
        sw_path = os.path.join(*Path(activity['software_path']).parts[0:4])

        if sw_path not in activities_dict:
            if sw_path in all_packages:
                activities.append(all_packages[sw_path])
                activities_dict[sw_path] = True

    return activities


def create_deposition(path):
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
    # software = filter_software(get_software(), path)
    with ApiSession() as api:
        software = filter_software(get_software(api), path, api)

    with NamedTemporaryFile() as star_file:
        star_file.write(str(build_entry(software)).encode())
        star_file.flush()
        star_file.seek(0)

        if not nickname:
            display_error('Cancelling deposition creation: a nickname is necessary.')
        with bmrbdep.BMRBDepSession(nmrstar_file=star_file,
                                    user_email=get_user_email(),
                                    nickname=nickname) as bmrbdep_session:

            # Run the progress bar, which handles uploading of data files
            file_selector.run_progress_bar(selected_files, bmrbdep_session)

            # Delete the metadata file from the "upload file" list
            bmrbdep_session.delete_file('m2mtool_generated.str')

        with open(session_file, "w") as session_log:
            session_info = {"sid": bmrbdep_session.sid, "ctime": time.time()}
            session_log.write(json.dumps(session_info))

        # Open the session
        webbrowser.open_new_tab(bmrbdep_session.session_url)
        time.sleep(3)

    return 0


# Run the code in this module
if __name__ == '__main__':
    test_path = "/home/nmrbox/0015/jchin/Qt5.12.10/"  # delete later
    try:
        # create_deposition(sys.argv[1])  # restore later
        create_deposition(test_path)  # delete later
    except Exception as e:
        logging.critical(str(e))
        display_error(text=html_escape(str(e)))
        sys.exit(1)
