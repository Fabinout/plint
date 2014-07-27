#!/bin/bash

# read current diaeresis file as $2 and take unique prefix as $1
# produce on stdout new diaeresis file

cd "$( dirname "$0" )"
NUM="$1"
DFILE="$2"
shift
shift

mkdir -p contexts
for f in "$@"
do
  DEST=$(echo "contexts/$f.$NUM" | sed 's!/\.\.!!g')
  ./plint.py test/$f.tpl $DFILE "$DEST" < test/$f
done
cat contexts/* | ./haspirater/buildtrie_list.py |
  ./haspirater/compresstrie.py

