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

###########
# Imports #
###########

# Allow running in python2
from __future__ import print_function

# Standard lib packages
import os
import pwd
import sys
import json
import random
import logging
import webbrowser
from tempfile import NamedTemporaryFile
import xml.etree.cElementTree as ET

import adit

# pip/repo installed packages
try:
    import psycopg2
    from psycopg2.extras import DictCursor
    from psycopg2 import ProgrammingError
except ImportError:
    logging.critical("You must install psycopg2 to run this module.")
    sys.exit(1)

# Local packages
from PyNMRSTAR import bmrb as pynmrstar

#########################
# Module initialization #
#########################

# Load the configuration file
_DIR = os.path.dirname(os.path.realpath(__file__))
configuration = json.loads(open(os.path.join(_DIR, "config.json"), "r").read())

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# Set up pynmrstar
pynmrstar.SKIP_EMPTY_LOOPS = True

###########
# Methods #
###########

def get_postgres_connection(user=configuration['psql']['user'],
                            host=configuration['psql']['host'],
                            database=configuration['psql']['database'],
                            password=configuration['psql']['password'],
                            port=configuration['psql']['port'],
                            dictionary_cursor=False):
    """ Returns a connection to postgres and a cursor."""

    # Errors connecting will be handled upstream
    if dictionary_cursor:
        conn = psycopg2.connect(user=user, host=host, database=database,
                                port=port, password=password,
                                cursor_factory=DictCursor)
    else:
        conn = psycopg2.connect(user=user, host=host, database=database,
                                port=port, password=password)
    cur = conn.cursor()

    return conn, cur

def get_software(vm_id=None):
    """ Returns a dictionary of the known software packages."""

    # Determine the VM version
    if not vm_id:
        vm_id = get_vm_version()

    logging.info("Getting software information.")

    registry_dict_cur = get_postgres_connection(database="registry", dictionary_cursor=True)[1]

    registry_dict_cur.execute('''
SELECT slug,url,software_path,version,synopsis,pr.first_name,pr.last_name,pr.email,pr.address1
  FROM software as sw
  LEFT JOIN software_versions as sv
    ON sw.id = sv.software_id
  LEFT JOIN software_version_vm as svvm
    ON svvm.software_version_id = sv.id
  LEFT JOIN person_software as w
    ON w.software_id = sw.id
  LEFT JOIN persons as pr
    ON w.person_id = pr.id
  WHERE svvm.vm_id = %s''', [vm_id])

    res = {}
    for package in registry_dict_cur:
        res[package['software_path']] = dict(package)

    return res

def get_entry_saveframe():
    """ Returns information about the NMRbox user. """

    registry_dict_cur = get_postgres_connection(database="registry", dictionary_cursor=True)[1]

    registry_dict_cur.execute('''
SELECT institution_type as user_type, ins.name AS institution,p.*
  FROM persons as p
  LEFT JOIN institutions AS ins
    ON ins.id = p.institution_id
  WHERE p.nmrbox_acct=%s''', [get_username()])
    entry = pynmrstar.Saveframe.from_scratch("entry_information", "_Entry")
    entry.add_tags([["Sf_category", "entry_information"], ["Sf_framecode", "entry_information"]])

    # Create the contact person loop
    contact_person = pynmrstar.Loop.from_scratch("_Contact_person")
    contact_person.add_column(["ID","Email_address", "Given_name", "Family_name",
                               "Department_and_institution", "Address_1",
                               "Address_2", "Address_3", "City", "State_province",
                               "Country", "Postal_code", "Role", "Organization_type"])
    person = dict(registry_dict_cur.fetchone())
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
    entry_author.add_column(["Ordinal", "Given_name", "Family_name"])
    entry_author.add_data([1, person['first_name'], person['last_name']])

    # Add the children loops
    entry.add_loop(contact_person)
    entry.add_loop(entry_author)

    # Create the citation saveframe
    citation = pynmrstar.Saveframe.from_scratch("citations", "_Citation")
    citation.add_tags([["Sf_category", "citations"], ["Sf_framecode", "citations"]])
    citation_author = pynmrstar.Loop.from_scratch("_Citation_author")
    citation_author.add_column(["Ordinal", "Given_name", "Family_name"])
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
    software_packages.append({'slug': 'NMRbox', 'version': get_vm_version(),
                              'synopsis': 'NMRbox is a cloud-based virtual machine loaded with NMR software.',
                              'first_name': 'NMRbox Team', 'last_name': None,
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
        fname = package["first_name"]
        lname = package["last_name"]
        if not fname and not lname:
            name = None
        elif not fname:
            name = lname
        elif not lname:
            name = fname
        else:
            name = fname + " " + lname
        vendor = [name, None, package["email"], None, package_id]
        if vendor[0] or vendor[1] or vendor[2]:
            frame['_Vendor'].add_data(vendor)

        package_id += 1


    return(entry)

def get_username():
    """ Return the username of the current user."""

    return pwd.getpwuid(os.getuid()).pw_name

def get_user_activity(directory):
    """ Prints a summary of the users activity."""

    logging.info("Fetching user command activity.")

    dirmod = get_modified_time(directory)

    cur = get_postgres_connection()[1]
    cur.execute('''
SELECT runtime,cwd,filename,cmd FROM snoopy
  WHERE username = %s AND cwd like %s
  ORDER BY runtime ASC''', [get_username(), directory + "%"])

    return cur.fetchall()


def get_vm_version():
    """ Returns the version of the VM that is running."""

    # Remove once the DB is updated
    return "2"

    # Get the NMRBox version from the xml
    with open("/etc/nmrbox_version.xml", "r") as nmr_version_file:
        root = ET.parse(nmr_version_file).getroot()
        version = next(root.getiterator("version")).text

        return version[:version.index("-")]

    # Assume the latest version in the absense of the necessary info
    return configuration['lastest_vm_version']

def get_modified_time(path):
    """ Returns the last modified time of the file/folder."""

    return os.path.getmtime(path)

def filter_software(all_packages, path):
    """ Returns the software packages used by this user in the selected
    directory. """

    activities = []
    activities_dict = {}
    for activity in get_user_activity(path):
        if not activity[2].startswith("/usr/software"):
            continue
        sw_path = os.path.join("/usr/software", activity[2].split("/")[3])

        if sw_path not in activities_dict:
            if sw_path in all_packages:
                activities.append(all_packages[sw_path])
                activities_dict[sw_path] = True

    return activities

# Demo what we can do
def main(args):

    # If the session exists, re-open it
    session_file = os.path.join(args[1], '.aditnmr_session')
    if os.path.isfile(session_file):
        logging.info("Loading existing session...")
        adit_session = adit.ADITSession(None, open(session_file, "r").read())
        webbrowser.open_new_tab(adit_session.get_session_url())
        sys.exit(0)

    # Fetch the software list
    software = filter_software(get_software(), args[1])

    files = [os.path.join(args[1], x) for x in os.listdir(args[1])]
    files = filter(lambda x:os.path.isfile(x),files)

    with NamedTemporaryFile() as star_file:
        star_file.write(str(build_entry(software)).encode())
        star_file.flush()

        with adit.ADITSession(star_file.name) as adit_session:
            # Upload data files

            for ef in files:
                adit_session.upload_file(random.choice(list(adit.ADITSession.file_types.keys())), ef)

            open(session_file, "w").write(str(adit_session.sid))
            session_url = adit_session.get_session_url()

        webbrowser.open_new_tab(adit_session.get_session_url())
        os.system("gedit %s" % star_file.name)

    return 0

# Run the code in this module
if __name__ == '__main__':
    sys.exit(main(sys.argv))
