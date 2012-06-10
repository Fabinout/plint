for a in test/*.tpl; do echo "$a"; ./plint.py $a < ${a%.tpl}; done
