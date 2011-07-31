#!/usr/bin/python3 -uO

import re
import sys
import rhyme
import metric
import template
from pprint import pprint
from common import normalize

if len(sys.argv) != 3:
  print("Usage: %s TEMPLATE POEM" % sys.argv[0], file=sys.stderr)
  print("Check stdin according to template, report errors on stdout",
      file=sys.stderr)
  sys.exit(1)

f = open(sys.argv[1])
template = template.Template(f)
f.close()

f = open(sys.argv[2], 'r')
for line in f.readlines():
  l = line.split(' ')
  if l[1] == '/me':
    continue # ignore /me
  errors = template.check(' '.join(l[1:]))
  if len(errors) > 0:
    print("Existing poem is wrong!", file=sys.stderr)
    sys.exit(2)
f.close()

f = open(sys.argv[2], 'a')

template.reject_errors = True

def run():
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    l = line.rstrip().split(' ')
    text = ' '.join(l[2:])
    if normalize(text.strip()) == '':
      continue
    first = [a for a in line.split(' ')[2:] if a != ''][0]
    if first[-1] == ':' or first[0].upper() != first[0]:
      continue # ignore non-poem lines
    if first == '/me':
      # always accept actions
      print(' '.join(l[1:]), file=f)
      f.flush()
      continue
    if first[0] == '/':
      continue # ignore other commands
    errors = template.check(text)
    for error in errors:
      print(error.report())
    if len(errors) == 0:
      print(' '.join(l[1:]))
      print(' '.join(l[1:]), file=f)
      f.flush()

run()

f.close()

