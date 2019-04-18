#!/bin/bash

# General fixes for lexique

cd "$( dirname "$0" )"

sed 1d | ./subst.pl

