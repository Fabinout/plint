#!/bin/bash

FILES="andromaque mithridate boileau ../additions cyrano$@"
DIR="$( cd "$( dirname "$0" )" && pwd )"
mkdir -p contexts
rm -f contexts/*
cp diaeresis_empty.json diaeresis0.json;
for a in $(seq 0 4); do
  b=$(($a+1));
  ./onepass.sh $a diaeresis${a}.json $FILES > diaeresis${b}.json;
done;
cat diaeresis5.json
