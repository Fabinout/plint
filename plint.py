#!/usr/bin/python3 -uO

import sys
import template

def run():
  ok = True
  f2 = None
  if len(sys.argv) == 3:
    f2 = open(sys.argv[2], 'w')
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    errors = template.check(line, f2)
    for error in errors:
      print(error.report(), file=sys.stderr)
      ok = False
  return ok

if __name__ == '__main__':
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("Usage: %s TEMPLATE [OCONTEXT]" % sys.argv[0], file=sys.stderr)
    print("Check stdin according to template, report errors on stdout",
        file=sys.stderr)
    sys.exit(1)

  f = open(sys.argv[1])
  x = f.read()
  f.close()

  template = template.Template(x)

  ok = run()
  sys.exit(0 if ok else 1)

