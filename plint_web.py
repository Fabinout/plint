#!/usr/bin/python3 -O
#encoding: utf8

import localization
import re
import template
import error
from bottle import run, Bottle, request, static_file, redirect, response
from jinja2 import Environment, PackageLoader
from json import dumps

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

def get_title(lang):
  if lang == 'fr':
    return "plint -- vérification formelle de poèmes"
  else:
    return "plint -- French poetry checker"

@app.route('/static/tpl/<filename>')
def server_static(filename):
  return static_file(filename, root="./static/tpl", mimetype="text/plain")

@app.route('/<lang>/static/img/<filename>')
def server_static(filename, lang=None):
  return static_file(filename, root="./static/img")

@app.route('/<lang>/static/tpl/<filename>')
def server_static(filename, lang=None):
  return static_file(filename, root="./static/tpl", mimetype="text/plain")

@app.route('/static/<filename>')
def server_static(filename):
  return static_file(filename, root="./static")

@app.route('/<lang>/static/<filename>')
def server_static(filename, lang=None):
  return static_file(filename, root="./static")

@app.route('/')
def root():
  redirect('/' + get_locale() + '/')

@app.route('/<page>')
def paged(page):
  redirect('/' + get_locale() + '/' + page)

@app.route('/<lang>/')
def root(lang):
  if lang not in ['fr', 'en']:
    return paged(lang)
  return env.get_template('index.html').render(title=get_title(lang),
      lang=lang, path="")

@app.route('/<lang>/js')
def about(lang):
  return env.get_template('js.html').render(title=get_title(lang),
      lang=lang, path="js")

@app.route('/<lang>/about')
def about(lang):
  return env.get_template('about.html').render(title=get_title(lang),
      lang=lang, path="about")

def check(poem):
  if len(poem) > 8192:
    return None
  s = poem.split("\n")
  for x in range(len(s)):
    if len(s[x]) > 512:
      return None
    s[x].strip()
  return s

@app.route('/<lang>/checkjs', method='POST')
def q(lang):
  response.content_type = 'application/json'
  localization.init_locale(lang)
  poem = request.forms.get('poem')
  poem = re.sub(r'<>&', '', request.forms.get('poem'))
  poem = check(poem)
  if not poem:
    if lang == 'fr':
      msg = "Le poème est vide, trop long, ou a des lignes trop longues"
    else:
      msg = "Poem is empty, too long, or has too long lines"
    return dumps({'error': msg})
  templateName = request.forms.get('template')
  if templateName == 'custom':
    x = request.forms.get('custom_template')
  else:
    try:
      f = open("static/tpl/" + templateName + ".tpl")
      x = f.read()
      f.close()
    except IOError:
      if lang == 'fr':
        msg = "Modèle inexistant"
      else:
        msg = "No such template"
      return dumps({'error': msg})
  print(x)
  try:
    templ = template.Template(x)
  except error.TemplateLoadError as e:
    if lang == 'fr':
      msg = "Erreur à la lecture du modèle : " + e.msg
    else:
      msg = "Error when reading template: " + e.msg
    return dumps({'error': msg})
  print(x)
  poem.append(None)
  r = []
  i = 0
  d = {}
  for line in poem:
    i += 1
    last = False
    if line == None:
      line = ""
      last = True
    errors = templ.check(line, last=last)
    if errors:
      r.append({
        'line': line,
        'num': i,
        'errors': sum(errors.lines(short=True), [])
        })
  d['result'] = r
  return dumps(d)

@app.route('/<lang>/check', method='POST')
def q(lang):
  d = {
      'poem': request.forms.get('poem'),
      'template': request.forms.get('template'),
      'lang': lang,
      'nolocale': True,
    }
  localization.init_locale(lang)
  d['poem'] = re.sub(r'<>&', '', d['poem'])
  print(d['poem'])
  poem = check(d['poem'])
  if not poem:
    if lang == 'fr':
      msg = "Le poème est vide, trop long, ou a des lignes trop longues"
    else:
      msg = "Poem is empty, too long, or has too long lines"
    d['error'] = msg
    return env.get_template('error.html').render(**d)
  if not re.match("^[a-z_]+$", d['template']):
    if lang == 'fr':
      msg = "Modèle inexistant"
    else:
      msg = "No such template"
    d['error'] = msg
    return env.get_template('error.html').render(**d)
  if d['template'] == 'custom':
    x = request.forms.get('custom_template')
  else:
    try:
      f = open("static/tpl/" + d['template'] + ".tpl")
      x = f.read()
      f.close()
    except IOError:
      if lang == 'fr':
        msg = "Modèle inexistant"
      else:
        msg = "No such template"
      d['error'] = msg
      return env.get_template('error.html').render(**d)
  try:
    templ = template.Template(x)
  except error.TemplateLoadError as e:
    if lang == 'fr':
      msg = "Erreur à la lecture du modèle : " + e.msg
    else:
      msg = "Error when reading template: " + e.msg
    d['error'] = msg
    return env.get_template('error.html').render(**d)
  print(d['template'])
  print(x)
  poem.append(None)
  r = []
  firsterror = None
  nerror = 0
  i = 0
  for line in poem:
    i += 1
    last = False
    if line == None:
      line = ""
      last = True
    errors = templ.check(line, last=last)
    if errors and not firsterror:
      firsterror = i
    r.append((line, '\n'.join(sum(errors.lines(short=True), [])) if errors else []))
    nerror += len(errors.errors) if errors else 0
  d['result'] = r
  d['firsterror'] = firsterror
  d['nerror'] = nerror
  if nerror == 0:
    d['title'] = "[Valid] " + get_title(lang)
  else:
    d['title'] = "[Invalid] " + get_title(lang)
  return env.get_template('results.html').render(**d)

if __name__ == '__main__':
  run(app, port='5000', server="cherrypy", host="0.0.0.0")

