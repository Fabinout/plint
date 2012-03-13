#!/bin/bash

DIR="$( cd "$( dirname "$0" )" && pwd )"

cat $DIR/top.html
cat $1 | $DIR/make_poem.pl
cat $DIR/bottom.html
