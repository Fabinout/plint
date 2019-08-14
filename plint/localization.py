import gettext
import locale
import logging
import os

def init_locale(loc=None):
  locale.setlocale(locale.LC_ALL, '') # use user's preferred locale
  # take first two characters of country code
  if not loc:
    loc = locale.getlocale()
  else:
    loc = [loc]
  filename = os.path.dirname(__file__) + "/res/messages_%s.mo" % loc[0][0:2]

  try:
    logging.debug("Opening message file %s for locale %s", filename, loc[0])
    trans = gettext.GNUTranslations(open(filename, "rb"))
  except IOError:
    logging.debug("Locale not found. Using default messages")
    trans = gettext.NullTranslations()

  trans.install()

