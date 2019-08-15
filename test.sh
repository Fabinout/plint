#!/bin/bash

# about the hiatus error found in malherbe, see:
# http://books.google.de/books?id=qpQGAAAAQAAJ&pg=PA40&lpg=PA40&dq=Et+que+pour+retarder+une+heure+seulement+%22Pour+ne+mourir+jamais%22,+meure+%C3%A9ternellement&source=bl&ots=G8VEFnXkmB&sig=qzmHRiloQpIp6Ebb-9aJrYOoIM0&hl=en&sa=X&ei=3oL8T9WiJ6aB4gTK8pWPBw&redir_esc=y#v=onepage&q=Et%20que%20pour%20retarder%20une%20heure%20seulement%20%22Pour%20ne%20mourir%20jamais%22%2C%20meure%20%C3%A9ternellement&f=false

echo "It is normal that some errors occur when running this script" >/dev/stderr
echo "See test_expected_output.out for the usual errors that are output" >/dev/stderr

rm -f test_temp.txt;
rm -f test_temp_sorted.txt;
rm -f test_expected_sorted.txt;

for a in plint/test_data/*.tpl; do
  echo "$a"
  echo "$a" >> test_temp.txt
  if [[ $a == *cyrano_full* ]]
  then
    ./plint.py $(pwd)/$a ../data/diaeresis_cyrano.json < $(pwd)/${a%.tpl} &>> test_temp.txt
  else
    ./test_one.sh $(basename "${a%.tpl}") &>> test_temp.txt
  fi
done

if diff test_temp.txt test_expected_output.out
then
    echo "TEST SUCCEED";
    RET=0
else
    echo "TEST FAILED";
    RET=1
fi

rm -f test_temp.txt;

exit "$RET"
