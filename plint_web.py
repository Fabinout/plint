#!/usr/bin/python3 -O
#encoding: utf8

import localization
import re
import template
from bottle import run, Bottle, request, static_file
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('plint_web', 'views'))

app = Bottle()

def best_match(matches, header):
  # inspired by http://www.xml.com/pub/a/2005/06/08/restful.html

  def parse_one(t):
    parts = t.split(";")
    d = dict([tuple([s.strip() for s in param.split("=")])
      for param in parts[1:]])
    if 'q' not in d.keys():
      d['q'] = "1"
    return (parts[0], d)

  parts = []
  for p in header.split(","):
    parsed = parse_one(p)
    parts.append((float(parsed[1]['q']), parsed[0].split("-")))
  for lang in [x[1] for x in sorted(parts, reverse=True)]:
    for match in matches:
      if match in lang:
        return match
  return matches[0]

def get_locale():
  header = request.headers.get('Accept-Language')
  print(header)
  try:
    return best_match(['fr', 'en'], header)
  except AttributeError:
    return 'en'

def get_title():
  if get_locale() == 'fr':
    return "plint -- vérification formelle de poèmes"
  else:
    return "plint -- French poetry checker"

@app.route('/static/tpl/<filename>')
def server_static(filename):
  return static_file(filename, root="./static/tpl", mimetype="text/plain")

@app.route('/static/<filename>')
def server_static(filename):
  return static_file(filename, root="./static")

@app.route('/')
def root():
  return env.get_template('index.html').render(title=get_title(),
      lang=get_locale())

@app.route('/about')
def about():
  return env.get_template('about.html').render(title=get_title(),
      lang=get_locale())

def check(poem):
  if len(poem) > 8192:
    return None
  s = poem.split("\n")
  for x in range(len(s)):
    if len(s[x]) > 512:
      return None
    s[x].strip()
  return s

@app.route('/check', method='POST')
def q():
  d = {
      'poem': request.forms.get('poem'),
      'template': request.forms.get('template'),
      'lang': get_locale(),
    }
  localization.init_locale(get_locale())
  d['poem'] = re.sub(r'<>&', '', d['poem'])
  print(d['poem'])
  poem = check(d['poem'])
  if not poem:
    return env.get_template('error.html').render(**d)
  if not re.match("^[a-z_]+$", d['template']):
    return env.get_template('error.html').render(**d)
  if d['template'] == 'custom':
    x = request.forms.get('custom_template')
  else:
    try:
      f = open("static/tpl/" + d['template'] + ".tpl")
      x = f.read()
      f.close()
    except IOError:
      return env.get_template('error.html').render(**d)
  try:
    templ = template.Template(x)
  except ValueError:
    return env.get_template('error.html').render(**d)
  r = []
  firsterror = None
  nerror = 0
  i = 0
  for line in poem:
    i += 1
    errors = [error.report(short=True) for error in templ.check(line)]
    if errors != [] and not firsterror:
      firsterror = i
    r.append((line, errors))
    nerror += len(errors)
  d['result'] = r
  d['firsterror'] = firsterror
  d['nerror'] = nerror
  if nerror == 0:
    d['title'] = "[Valid] " + get_title()
  else:
    d['title'] = "[Invalid] " + get_title()
  return env.get_template('results.html').render(**d)

if __name__ == '__main__':
  run(app, port='5000', server="cherrypy", host="0.0.0.0")

