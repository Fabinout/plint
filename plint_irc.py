#!/usr/bin/python3 -uO

import localization
import re
import sys
import diaeresis
import rhyme
from template import Template
from pprint import pprint
from common import normalize

buf = ""
lbuf = []

def write(l, descriptor=None):
  if descriptor:
    f = descriptor
  else:
    f = open(sys.argv[2], 'a')
  print(' '.join(l), file=f)
  if not descriptor:
    f.close()

def output(l, descriptor):
  print(' '.join(l), file=descriptor)
  write(l, descriptor if descriptor != sys.stdout else None)

def leading_cap(text):
  for c in text:
    if c.upper() == c.lower():
      continue # symbol
    if c != c.lower():
      return True
    if c != c.upper():
      return False
  return False

def manage(line, descriptor=sys.stdout):
  """manage one line, indicate if an error occurred"""
  global buf
  global lbuf
  usebuf = False
  l = line.rstrip().split(' ')
  text = ' '.join(l[1:])
  if normalize(text.strip()) == '':
    return True # no text
  first = [a for a in l[1:] if a != ''][0]
  if first == '/me' and len(l) >= 3 and l[2] == 'plint':
    # always accept actions
    if len(lbuf) > 0:
      lbuf.append(l)
    else:
      write(l, descriptor)
    return True
  if first[0] == '/':
    return False # ignore other commands
  if first.lstrip().startswith("...") or first.lstrip().startswith("…"):
    text = buf+text
    usebuf = True
  if not usebuf:
    if first[-1] == ':':
      return False
    if not leading_cap(text):
      return False
    if (not (text.rstrip().endswith("...") or text.rstrip().endswith("…")
        or text.lstrip().endswith("...") or text.lstrip().endswith("…")) and
        len(text) < 13):
      return False # too short
    if len(text) > 130:
      return False # too long
  if (text.rstrip().endswith("...") or
      text.rstrip().endswith("…")):
    # it might be a call
    buf = text
    if usebuf:
      lbuf.append(l)
    else:
      lbuf = [l]
    return True
  errors = template.check(text, quiet=False)
  quiet = False
  if errors:
    print(errors.report())
  if not errors:
    buf = ""
    if usebuf:
      for bl in lbuf:
        output(bl, descriptor)
    output(l, descriptor)
    lbuf = []
  return not errors

if len(sys.argv) not in [3, 4]:
  print("Usage: %s TEMPLATE POEM [OFFSET]" % sys.argv[0], file=sys.stderr)
  print("Check POEM according to TEMPLATE, add valid verse from stdin to POEM",
      file=sys.stderr)
  print("Ignore OFFSET lines from POEM",
      file=sys.stderr)
  sys.exit(1)

localization.init_locale()

f = open(sys.argv[1])
x = f.read()
f.close()
template = Template(x)

diaeresis.load_diaeresis('diaeresis.json')

template.reject_errors = True

offset = 0
if len(sys.argv) == 4:
  offset = int(sys.argv[3])

pos = 0

localization.init_locale()
f = open(sys.argv[2], 'r')
for line in f.readlines():
  pos += 1
  if pos <= offset:
    continue # ignore first lines
  print("%s (read)" % line.rstrip(), file=sys.stderr)
  if not manage(line, sys.stderr):
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

