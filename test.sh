echo "It is normal that some errors occur when running this script"
for a in test/*.tpl; do echo "$a"; ./plint.py $a < ${a%.tpl}; done
