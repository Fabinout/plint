#!/bin/bash

# set -x

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"
cd .. # go in the main folder

# use the verb diaeresis files if they exist
if [ -f $DIR/diaeresis_verbs/final_syneresis -a -f $DIR/diaeresis_verbs/final_diaeresis ]
then
  cat $DIR/diaeresis_verbs/final_syneresis | grep -vE -- '-vous$|-nous$' |
    python3 -m plint <(echo 12) $DIR/diaeresis_empty.json $DIR/final_syneresis.ctx 1 0
  cat $DIR/diaeresis_verbs/final_syneresis | grep -E -- '-vous$|-nous$' |
    python3 -m plint <(echo 12) $DIR/diaeresis_empty.json $DIR/final_syneresis2.ctx 1 1
  cat $DIR/final_syneresis.ctx $DIR/final_syneresis2.ctx | sponge $DIR/final_syneresis.ctx
  cat $DIR/diaeresis_verbs/final_diaeresis | grep -vE -- '-vous$|-nous$' |
    python3 -m plint <(echo 12) $DIR/diaeresis_empty.json $DIR/final_diaeresis.ctx 2 0
  cat $DIR/diaeresis_verbs/final_diaeresis | grep -E -- '-vous$|-nous$' |
    python3 -m plint <(echo 12) $DIR/diaeresis_empty.json $DIR/final_diaeresis2.ctx 2 1
  cat $DIR/final_diaeresis.ctx $DIR/final_diaeresis2.ctx | sponge $DIR/final_diaeresis.ctx
fi

# prepare the raw addition file
for a in $DIR/additions $DIR/additions_quicherat $DIR/additions_cyrano
do
  cut -d ' ' -f1 ${a}.txt > ${a}.tpl
  cut -d ' ' -f2- ${a}.txt > ${a}
done

# run the training
FILES="andromaque mithridate boileau ../../train_diaeresis/additions ../../train_diaeresis/additions_quicherat cyrano$@"
mkdir -p $DIR/contexts
rm -f $DIR/contexts/*
cp $DIR/diaeresis_empty.json $DIR/diaeresis0.json;
for a in $(seq 0 4); do
  b=$(($a+1));
  $DIR/onepass.sh $a $DIR/diaeresis${a}.json $FILES > $DIR/diaeresis${b}.json;
done;
cat $DIR/diaeresis5.json
