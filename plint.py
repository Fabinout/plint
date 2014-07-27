#!/usr/bin/python3 -uO

import diaeresis
import localization
import sys
import template
import error

def run():
  ok = True
  f2 = None
  if len(sys.argv) == 4:
    f2 = open(sys.argv[3], 'w')
  should_end = False
  while True:
    line = sys.stdin.readline()
    if not line:
      should_end = True
      line = ""
    errors = template.check(line, f2, last=should_end)
    if errors:
      print(errors.report(), file=sys.stderr)
      ok = False
    if should_end:
      break
  return ok

if __name__ == '__main__':
  localization.init_locale()
  if len(sys.argv) < 2 or len(sys.argv) > 4:
    print(_("Usage: %s TEMPLATE [DFILE [OCONTEXT]]") % sys.argv[0], file=sys.stderr)
    print(_("Check stdin according to TEMPLATE, report errors on stdout"),
        file=sys.stderr)
    sys.exit(1)

  template_name = sys.argv[1]
  if len(sys.argv) > 2:
    diaeresis_name = sys.argv[2]
  else:
    diaeresis_name = "diaeresis.json"

  diaeresis.load_diaeresis(diaeresis_name)

  f = open(template_name)
  x = f.read()
  f.close()

  try:
    template = template.Template(x)
  except error.TemplateLoadError as e:
    print("Could not load template %s: %s" % (template_name, e.msg), file=sys.stderr)
    sys.exit(2)

  ok = run()
  sys.exit(0 if ok else 1)

