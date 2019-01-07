#!/bin/bash
if [[ ! -d "./env" ]]; then
  ./setup_virtualenv.sh
fi
source ./env/bin/activate
./m2mtool.py "$@"
