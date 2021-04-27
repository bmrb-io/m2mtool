#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [[ ! -d "${DIR}/venv" ]]; then
  cd "${DIR}" || exit 0
  echo "Performing initial install..."
  pip3 install virtualenv > /dev/null
  python3 -m virtualenv venv > /dev/null
  source "${DIR}"/venv/bin/activate
  pip3 install -r requirements.txt > /dev/null
fi
source "${DIR}"/venv/bin/activate
"${DIR}"/m2mtool.py "$@"
