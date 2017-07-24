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

# Standard lib packages
import os
import sys
import json
import logging

# pip/repo installed packages
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2 import ProgrammingError

# Local packages
from PyNMRSTAR import bmrb

#########################
# Module initialization #
#########################

# Load the configuration file
_DIR = os.path.dirname(os.path.realpath(__file__))
configuration = json.loads(open(os.path.join(_DIR, "config.json"), "r").read())

# Set up logging
logging.basicConfig()

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

def get_software(vm_id=2):
    """ Returns a dictionary of the known software packages."""

    # In the future potentially get version from /etc/nmrbox_version

    cur = get_postgres_connection(database="registry", dictionary_cursor=True)[1]
    cur.execute('''
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
    for package in cur:
        res[package['slug']] = dict(package)

    return res

def print_user_activity(username, directory):
    """ Prints a summary of the users activity."""

    cur = get_postgres_connection()[1]
    cur.execute('''
SELECT runtime,cwd,filename,cmd FROM snoopy
  WHERE username = %s AND cwd like %s
  ORDER BY runtime ASC''', [username, directory])
    activities = cur.fetchall()

    for activity in activities:
        print(activity[0], activity[1], activity[2], activity[3])


def main(args):

    get_software()
    #print_user_activity(args[1], args[2])
    return 0

# Run the code in this module
if __name__ == '__main__':
    sys.exit(main(sys.argv))
