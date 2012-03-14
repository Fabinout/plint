#!/usr/bin/python3 -uO

import sys
import template

def run():
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    errors = template.check(line)
    for error in errors:
      print(error.report(), file=sys.stderr)

if __name__ == '__main__':
  if len(sys.argv) != 2:
    print("Usage: %s TEMPLATE" % sys.argv[0], file=sys.stderr)
    print("Check stdin according to template, report errors on stdout",
        file=sys.stderr)
    sys.exit(1)

  f = open(sys.argv[1])
  x = f.read()
  f.close()
  template = template.Template(x)

  run()

