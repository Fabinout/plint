#!/usr/bin/python3

import os
import sys

# modules are in the parent folder
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from common import consonants

for l in sys.stdin.readlines():
    w = l.strip()
    if w.endswith("ions"):
        lens = 4
    else:
        lens = 3
    if (len(w) < lens+2):
        print ("1 %s" % w)
        continue
    x = w[-lens-2]
    y = w[-lens-1]
    if not x in consonants or not y in consonants or x == y:
        print ("1 %s" % w)
        continue
    # inspired by
    # https://www.cairn.info/revue-litteratures-classiques-2015-3-page-187.htm
    if y in "rl" and x not in "rl":
        print ("2 %s" % w)
        continue
    print ("1 %s" % w)
    continue


