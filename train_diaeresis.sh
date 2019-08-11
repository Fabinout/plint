#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

# prepare the raw addition file
for a in additions additions_quicherat
do
  cut -d ' ' -f1 ${a}.txt > ${a}.tpl
  cut -d ' ' -f2- ${a}.txt > ${a}
done

# run the training
FILES="andromaque mithridate boileau ../additions ../additions_quicherat cyrano$@"
mkdir -p contexts
rm -f contexts/*
cp diaeresis_empty.json diaeresis0.json;
for a in $(seq 0 4); do
  b=$(($a+1));
  ./onepass.sh $a diaeresis${a}.json $FILES > diaeresis${b}.json;
done;
cat diaeresis5.json
