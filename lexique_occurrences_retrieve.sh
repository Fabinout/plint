#!/bin/bash

ZIP="Lexique371b.zip"
URL="http://www.lexique.org/public/$ZIP"
FILE="Lexique371/Bases+Scripts/Lexique3.txt"

cd "$( dirname "$0" )"

wget $URL
unzip -qq $ZIP $FILE
cat $FILE | ./frhyme/lexique/lexique_fix.sh | cut -f1 |
  rev | cut -d' ' -f1 | rev | sort | uniq -c |
  awk '{print $2, $1}'
