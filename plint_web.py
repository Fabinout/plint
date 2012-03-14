#!/usr/bin/python3 -O
#encoding: utf8

import re
import template
from bottle import run, Bottle, request, static_file
from jinja2 import Environment, PackageLoader

env = Environment(loader=PackageLoader('plint_web', 'views'))

app = Bottle()

def get_locale():
  # TODO
  if "fr" in request.headers.get('Accept-Language'):
    return "fr"
  else:
    return 'en'
  #best_match(['en', 'fr'])

def get_title():
  if get_locale() == 'fr':
    return "plint -- vérification formelle de poèmes"
  else:
    return "plint -- French poetry checker"

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
  if len(poem) > 4096:
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
    }
  d['poem'] = re.sub(r'<>&', '', d['poem'])
  poem = check(d['poem'])
  if not poem:
    return env.get_template('error.html').render(**d)
  if not re.match("^[a-z]+$", d['template']):
    return env.get_template('error.html').render(**d)
  try:
    f = open("tpl/" + d['template'] + ".tpl")
  except IOError:
    return env.get_template('error.html').render(**d)
  templ = template.Template(f)
  f.close()
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
  run(app, host='0.0.0.0', port='5000')

