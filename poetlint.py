#!/usr/bin/python3 -uO

import re
import sys
import metric
import template
from pprint import pprint

if len(sys.argv) != 2:
  print("Usage: %s TEMPLATE" % sys.argv[0], file=sys.stderr)
  print("Check stdin according to template, report errors on stdout",
      file=sys.stderr)
  sys.exit(1)

f = open(sys.argv[1])
template = template.Template(f)
f.close()

def run():
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    errors = template.check(line)
    for error in errors:
      print(error.report(), file=sys.stderr)

run()

