#!/bin/bash
if [[ ! -d "./env" ]]; then
  echo "Performing initial install..."
  pip3 install virtualenv > /dev/null
  python3 -m virtualenv env > /dev/null
  source ./env/bin/activate
  pip3 install -r requirements.txt > /dev/null
fi
source ./env/bin/activate
./m2mtool.py "$@"
