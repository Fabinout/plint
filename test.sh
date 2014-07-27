#!/bin/bash
echo "It is normal that some errors occur when running this script"
for a in test/*.tpl; do
  echo "$a"
  if [[ $a == *cyrano_full* ]]
  then
    ./plint.py $a diaeresis_cyrano.json < ${a%.tpl}
  else
    ./plint.py $a < ${a%.tpl}
  fi
done
