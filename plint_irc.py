#!/usr/bin/python3 -uO

import re
import sys
import rhyme
import metric
from template import Template
from pprint import pprint
from common import normalize

buf = ""
lbuf = []

def output(l):
  print(' '.join(l))
  f = open(sys.argv[2], 'a')
  print(' '.join(l), file=f)
  f.close()

def leading_cap(text):
  for c in text:
    if c.upper() == c.lower():
      continue # symbol
    if c != c.lower():
      return True
    if c != c.upper():
      return False
  return False

def manage(line, silent=False):
  """manage one line, indicate if an error occurred"""
  global buf
  global lbuf
  usebuf = False
  l = line.rstrip().split(' ')
  text = ' '.join(l[1:])
  if normalize(text.strip()) == '':
    return True # no text
  first = [a for a in l[1:] if a != ''][0]
  if first == '/me':
    # always accept actions
    if len(lbuf) > 0:
      lbuf.append(l)
    else:
      if not silent:
        f = open(sys.argv[2], 'a')
        print(' '.join(l), file=f)
        f.close()
    return True
  if first[0] == '/':
    return False # ignore other commands
  if first.lstrip().startswith("..."):
    text = buf+text
    usebuf = True
  if not usebuf:
    if first[-1] == ':':
      return False
    if not leading_cap(text):
      return False
  errors = template.check(text)
  if len(errors) > 0 and text.rstrip().endswith("..."):
    # it might be a call
    buf = text
    if usebuf:
      lbuf.append(l)
    else:
      lbuf = [l]
    return True
  for error in errors:
    print(error.report())
  if len(errors) == 0:
    buf = ""
    if not silent:
      if usebuf:
        for bl in lbuf:
          output(bl)
      output(l)
    lbuf = []
  return len(errors) == 0

if len(sys.argv) != 3:
  print("Usage: %s TEMPLATE POEM" % sys.argv[0], file=sys.stderr)
  print("Check POEM according to TEMPLATE, add valid verse from stdin to POEM",
      file=sys.stderr)
  sys.exit(1)

f = open(sys.argv[1])
x = f.read()
f.close()
template = Template(x)

template.reject_errors = True

f = open(sys.argv[2], 'r')
for line in f.readlines():
  print("Read: %s" % line, file=sys.stderr)
  if not manage(line, True):
    print("Existing poem is wrong!", file=sys.stderr)
    sys.exit(2)
f.close()

print("ready", file=sys.stderr)

def run():
  global lbuf
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    print("Seen: %s" % line, file=sys.stderr)
    manage(' '.join(line.split(' ')[1:]))

run()

