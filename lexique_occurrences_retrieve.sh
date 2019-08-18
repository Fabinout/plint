#!/bin/bash

ZIP="Lexique383.zip"
URL="http://www.lexique.org/databases/Lexique383/$ZIP"
FILE="Lexique383.tsv"

cd "$( dirname "$0" )"

wget $URL
unzip -qq $ZIP $FILE
cat $FILE | ./lexique_fix.sh | cut -f1 |
  rev | cut -d' ' -f1 | rev |
  cat - additions_occurrences |
  sort | uniq -c |
  awk '{print $2, $1}'

