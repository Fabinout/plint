#!/bin/bash

ZIP="Lexique383.zip"
URL="http://www.lexique.org/databases/Lexique383/$ZIP"
FILE="Lexique383.tsv"

DIR="$( cd "$( dirname "$0" )" && pwd )"
cd "$DIR"

wget $URL
unzip -qq $ZIP $FILE
cat $FILE | sed 1d | cut -f1 |
  rev | cut -d' ' -f1 | rev |
  cat - additions_occurrences |
  sort | uniq -c |
  awk '{print $2, $1}'

