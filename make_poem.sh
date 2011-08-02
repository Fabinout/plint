#!/bin/bash

cat top.html > www/index.html
cat poem | ./make_poem.pl >> www/index.html
cat bottom.html >> www/index.html
cp style.css www/
