#!/usr/bin/python3 -uO

import gettext
import locale
import logging
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

def init_localization():
  '''prepare l10n'''
  locale.setlocale(locale.LC_ALL, '') # use user's preferred locale
  # take first two characters of country code
  loc = locale.getlocale()
  filename = "res/messages_%s.mo" % locale.getlocale()[0][0:2]

  try:
    logging.debug("Opening message file %s for locale %s", filename, loc[0])
    trans = gettext.GNUTranslations(open(filename, "rb"))
  except IOError:
    logging.debug("Locale not found. Using default messages")
    trans = gettext.NullTranslations()

  trans.install()

if __name__ == '__main__':
  init_localization()
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

