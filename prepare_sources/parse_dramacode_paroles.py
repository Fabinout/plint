#!/usr/bin/python3

import sys

last = None
for l in sys.stdin.readlines():
    ll = l.strip()
    if len(ll) == 0:
        continue
    if l[0].isspace():
        last = last + " " + ll
        continue
    if last:
        print(last)
    last = ll

print(last)

