#!/usr/bin/python3

"""compare file from littre and file from plint for disagreements"""

import sys

plint = open(sys.argv[1])
littre = open(sys.argv[2])

while True:
  l_plint = plint.readline()
  if not l_plint:
    break
  l_littre = littre.readline()
  w_plint, p_plint = l_plint.split('%')
  w_littre, p_littre = l_littre.split('%')
  p_littre = int(p_littre)
  assert(w_plint == w_littre)
  w = w_plint
  if '-' in p_plint:
    lo, hi = p_plint.split('-')
    lo = int(lo)
    hi = int(hi)
  else:
    lo = int(p_plint)
    hi = lo
  if not (lo <= p_littre <= hi):
    print ("%s : %d vs %d-%d" % (w, p_littre, lo, hi))
