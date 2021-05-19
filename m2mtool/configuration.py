#!/usr/bin/env python3

import os
import json

# Load the configuration file
_DIR = os.path.dirname(os.path.realpath(__file__))
configuration = json.loads(open(os.path.join(_DIR, "config.json"), "r").read())
