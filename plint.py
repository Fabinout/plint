#!/usr/bin/python3 -uO

import localization
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
  localization.init_locale()
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    print(_("Usage: %s TEMPLATE [OCONTEXT]") % sys.argv[0], file=sys.stderr)
    print(_("Check stdin according to TEMPLATE, report errors on stdout"),
        file=sys.stderr)
    sys.exit(1)

  f = open(sys.argv[1])
  x = f.read()
  f.close()

  template = template.Template(x)

  ok = run()
  sys.exit(0 if ok else 1)

