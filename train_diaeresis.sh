#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

# use the verb diaeresis files if they exist
if [ -f diaeresis_verbs/final_syneresis -a -f diaeresis_verbs/final_diaeresis ]
then
  cat diaeresis_verbs/final_syneresis | grep -vE -- '-vous$|-nous$' |
    ./plint.py <(echo 12) ../data/diaeresis_empty.json final_syneresis.ctx 1 0
  cat diaeresis_verbs/final_syneresis | grep -E -- '-vous$|-nous$' |
    ./plint.py <(echo 12) ../data/diaeresis_empty.json final_syneresis2.ctx 1 1
  cat final_syneresis.ctx final_syneresis2.ctx | sponge final_syneresis.ctx
  cat diaeresis_verbs/final_diaeresis | grep -vE -- '-vous$|-nous$' |
    ./plint.py <(echo 12) ../data/diaeresis_empty.json final_diaeresis.ctx 2 0
  cat diaeresis_verbs/final_diaeresis | grep -E -- '-vous$|-nous$' |
    ./plint.py <(echo 12) ../data/diaeresis_empty.json final_diaeresis2.ctx 2 1
  cat final_diaeresis.ctx final_diaeresis2.ctx | sponge final_diaeresis.ctx
fi

# prepare the raw addition file
for a in additions additions_quicherat
do
  cut -d ' ' -f1 ${a}.txt > ${a}.tpl
  cut -d ' ' -f2- ${a}.txt > ${a}
done

# run the training
FILES="andromaque mithridate boileau ../../additions ../../additions_quicherat cyrano$@"
mkdir -p contexts
rm -f contexts/*
cp data/diaeresis_empty.json diaeresis0.json;
for a in $(seq 0 4); do
  b=$(($a+1));
  ./onepass.sh $a ../diaeresis${a}.json $FILES > diaeresis${b}.json;
done;
cat diaeresis5.json
