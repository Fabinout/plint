#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

# prepare the raw addition file
cut -d ' ' -f1 additions.txt > additions.tpl
cut -d ' ' -f2- additions.txt > additions

# run the training
FILES="andromaque mithridate boileau ../additions cyrano$@"
mkdir -p contexts
rm -f contexts/*
cp diaeresis_empty.json diaeresis0.json;
for a in $(seq 0 4); do
  b=$(($a+1));
  ./onepass.sh $a diaeresis${a}.json $FILES > diaeresis${b}.json;
done;
cat diaeresis5.json
