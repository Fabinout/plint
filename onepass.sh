#!/bin/bash

# read current diaeresis file as $2 and take unique prefix as $1
# produce on stdout new diaeresis file

cd "$( dirname "$0" )"
NUM="$1"
DFILE="$2"
shift
shift

mkdir -p contexts

# use the verb diaeresis files if they exist
if [ -f diaeresis_verbs/final_syneresis -a -f diaeresis_verbs/final_diaeresis ]
then
  cp final_syneresis.ctx "contexts/final_syneresis.$NUM"
  cp final_diaeresis.ctx "contexts/final_diaeresis.$NUM"
fi

for f in "$@"
do
  DEST=$(echo "contexts/$f.$NUM" | sed 's!/\.\.!!g')
  ./plint.py test/$f.tpl $DFILE "$DEST" < test/$f
done
cat contexts/* | ./haspirater/buildtrie_list.py |
  ./haspirater/compresstrie.py

