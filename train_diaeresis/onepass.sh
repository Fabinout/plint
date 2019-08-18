#!/bin/bash

# read current diaeresis file as $2 and take unique prefix as $1
# produce on stdout new diaeresis file

# set -x

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"
cd .. # go in the main folder

NUM="$1"
DFILE="$2"
shift
shift

mkdir -p $DIR/contexts

# use the verb diaeresis files if they exist
if [ -f $DIR/diaeresis_verbs/final_syneresis -a -f $DIR/diaeresis_verbs/final_diaeresis ]
then
  cp $DIR/final_syneresis.ctx "$DIR/contexts/final_syneresis.$NUM"
  cp $DIR/final_diaeresis.ctx "$DIR/contexts/final_diaeresis.$NUM"
fi

for f in "$@"
do
  NAME=$(basename "./plint/test_data/$f")
  DEST="$DIR/contexts/$NAME.$NUM"
  python3 -m plint ./plint/test_data/$f.tpl \
    --diaeresis=$DFILE --ocontext="$DEST" < ./plint/test_data/$f
done
cd haspirater/
cat $DIR/contexts/* | ./haspirater/buildtrie_list.py |
  ./haspirater/compresstrie.py

