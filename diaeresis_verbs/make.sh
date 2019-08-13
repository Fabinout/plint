#!/bin/bash

french-conjugator --all-infinitives | grep 'ier$' > verbs_ier
tr '\n' '\0' < verbs_ier | xargs -0 french-conjugator --mode=indicative,imperative |
  tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep 'ions$' | sort | uniq > verbs_ier_ions
tr '\n' '\0' < verbs_ier | xargs -0 french-conjugator --mode=indicative,imperative |
  tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep 'iez$' | sort | uniq > verbs_ier_iez
tr '\n' '\0' < verbs_ier | xargs -0 french-conjugator --mode=subjunctive --tense=present |
  tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep 'ions$' | sort | uniq > verbs_ier_subj_ions
tr '\n' '\0' < verbs_ier | xargs -0 french-conjugator --mode=subjunctive --tense=present |
  tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep 'iez$' | sort | uniq > verbs_ier_subj_iez
cat verbs_ier_ions verbs_ier_iez verbs_ier_subj_ions verbs_ier_subj_iez > final_diaeresis

french-conjugator --all-infinitives | grep -v 'ier$' | tr '\n' '\0' |
  xargs -0 french-conjugator | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -E 'iez$|ions$' |
  ./diaeresis_verbs.py | grep '^2 ' | cut -d' ' -f2 >> final_diaeresis
cat final_diaeresis | sort | uniq | sponge final_diaeresis

cat final_diaeresis | grep 'ions$' | sed 's/$/-nous/' > add
cat final_diaeresis | grep 'iez$' | sed 's/$/-vous/' >> add
cat final_diaeresis add | sponge final_diaeresis

french-conjugator --all-infinitives | grep -v 'ier$' | tr '\n' '\0' |
  xargs -0 french-conjugator | tr ',' '\n' | sed 's/^ *//;s/ *$//' | grep -E 'iez$|ions$' |
  ./diaeresis_verbs.py | grep '^1 ' | cut -d' ' -f2 | sort | uniq > final_syneresis
cat final_syneresis | grep 'ions$' | sed 's/$/-nous/' > add
cat final_syneresis | grep 'iez$' | sed 's/$/-vous/' >> add
cat final_syneresis add | sponge final_syneresis
