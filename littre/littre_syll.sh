#!/bin/bash

# extract prononciation from xmllittre
# https://bitbucket.org/Mytskine/xmlittre-data.git

xmlstarlet sel -t -m "//entree" -v "@terme" -v "\"%\"" \
  -v "entete/prononciation" -n "$1"/*.xml > prons
cat prons | grep -E "(syllabes en poésie|en poésie,? de)" > prons_poesie
cat prons | grep -E "(en vers,? de|syllabes en vers)" > prons_vers
cat additions_poesie additions_vers prons_poesie prons_vers |
  awk 'BEGIN {FS = "%";} !a[$1]++;' |
  while read l; do
    echo "$l" | cut -d '%' -f 1 | cut -d ' ' -f 1 | tr -d '\n'
    echo -n '%'
    echo "$l" | cut -d '%' -f 2- | tr ' ' '\n' |
    sed '
      s/^une$/1/;
      s/^deux$/2/;
      s/^trois$/3/;
      s/^quatre$/4/;
      s/^cinq$/5/;
      s/^cinç$/5/;
      s/^six$/6/;
      s/^sept$/7/;
      s/^disylla.*$/2/;
      s/^trisylla.*$/3/;
      ' | grep '[0-9]' | head -1
  done > prons_special

pv prons |
  grep -v '%$' |
  grep -v ' .*%' |
  awk 'BEGIN {FS = "%";} !a[$1]++;' |
  while read l; do
    echo "$l" | cut -d '%' -f 1 | cut -d ' ' -f 1 | tr -d '\n'
    echo -n '%'
    echo "$l" | cut -d '%' -f 2- | sed 's/ *- */-/g' | cut -d ' ' -f 1 | tr -d ',' |
    sed "s/-[^aâàeéêèiîoôuùûäëïöü-]*'//" | tr '-' '\n' | wc -l
  done > prons_normal

pv prons_special prons_normal |
  awk 'BEGIN {FS = "%";} !a[$1]++;' |
  tr -d ',' | sort | grep -v '^%' | sed 's/.*/\L&/' > prons_num

pv prons_num | cut -d '%' -f1 |
  ../plint.py raw.tpl 2>&1 |
  grep 'total:' | cut -d ':' -f4 |
  cut -d ')' -f1 > plint_raw_nums

paste <(cat prons_num| cut -d'%' -f1) plint_raw_nums |
  tr '\t' '%' | sed 's/ *% */%/' \
    > plint_num

./compare_plint.py plint_num prons_num > conflicts

