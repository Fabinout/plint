#!/bin/bash

# read current diaeresis file on stdin and take unique prefix as $1
# produce on stdout new diaeresis file

cd "$( dirname "$0" )"
NUM="$1"
shift

TEMP=`mktemp`
mkdir -p contexts
mv -f diaeresis.json $TEMP
cat > diaeresis.json
for f in "$@"
do
  DEST=$(echo "contexts/$f.$NUM" | sed 's!/\.\.!!g')
  ./plint.py test/$f.tpl "$DEST" < test/$f
done
mv $TEMP diaeresis.json
cat contexts/* | ./haspirater/buildtrie_list.py |
  ./haspirater/compresstrie.py

