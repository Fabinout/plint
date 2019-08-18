cut -f1,4 ~/git/lexique/lexique_my_format | grep 'NOM$' | cut -f1 | grep -E 'ion$|ions$' >> final_diaeresis
