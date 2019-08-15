#!/usr/bin/python3 -u

import sys

sys.stdin = sys.stdin.detach()
while True:
  l = sys.stdin.readline()
  if not l:
    break
  l = l.decode('utf8').strip()
  print(''.join((l.split(">"))[1:]))
