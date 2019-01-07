#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
if [[ ! -d "${DIR}/env" ]]; then
  cd ${DIR}
  echo "Performing initial install..."
  pip3 install virtualenv > /dev/null
  python3 -m virtualenv env > /dev/null
  source ${DIR}/env/bin/activate
  pip3 install -r requirements.txt > /dev/null
fi
source ${DIR}/env/bin/activate
${DIR}/m2mtool.py "$@"
