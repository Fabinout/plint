#!/bin/bash

# General fixes for lexique

cd "$( dirname "$0" )"

iconv -f latin1 -t utf8 | sed 1d | ./subst.pl

