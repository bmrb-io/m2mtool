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
import re
import pwd
import sys
import json
import logging
from tempfile import NamedTemporaryFile

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

    return entry

def build_entry(software_packages):
    """ Builds a NMR-STAR entry. Pass a list of
    software package dictionary (as returned by get_software)."""

    logging.info("Building software saveframe.")

    entry = pynmrstar.Entry.from_scratch('TBD')

    #dep_files = pynmrstar.Saveframe.from_template("deposited_data_files")
    entry.add_saveframe(get_entry_saveframe())

    package_id = 1
    for package in software_packages:
        frame = pynmrstar.Saveframe.from_template("software", package['slug'])

        try:
            entry.add_saveframe(frame)
        except ValueError:
            continue

        frame.add_tag("ID", package_id, update=True)
        frame.add_tag("Entry_ID", 'TBD', update=True)
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
        vendor = [name, None, package["email"], "TBD", package_id]
        if vendor[0] or vendor[1] or vendor[2]:
            frame['_Vendor'].add_data(vendor)

        package_id += 1


    return(entry)

def get_username():
    """ Return the username of the current user."""

    return pwd.getpwuid(os.getuid()).pw_name

def get_user_activity(directory):
    """ Prints a summary of the users activity."""

    dirmod = get_modified_time(directory)

    cur = get_postgres_connection()[1]
    cur.execute('''
SELECT runtime,cwd,filename,cmd FROM snoopy
  WHERE username = %s AND cwd like %s
  ORDER BY runtime ASC''', [get_username(), directory + "%"])

    return cur.fetchall()

def get_vm_version():
    """ Returns the version of the VM that is running."""

    try:
        with open("/etc/nmrbox_version", "r") as nmr_version:
            matches = re.search("Release([0-9\.]+)", nmr_version.readline())
            if matches and len(matches.groups()) > 0:
                return matches.groups(0)[0]
    except IOError:
        pass

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

    software = filter_software(get_software(), args[1])

    with NamedTemporaryFile() as star_file:
        star_file.write(str(build_entry(software)).encode())
        star_file.flush()
        os.system("gedit %s" % star_file.name)

    return 0

# Run the code in this module
if __name__ == '__main__':
    sys.exit(main(sys.argv))
