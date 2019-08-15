#!/usr/bin/python3 -uO

"""Undocumented hack to play oulipo's dictionary game with plint"""

import copy
import localization
from template import Template
from rhyme import Rhyme
import re
import sys
import time
from common import normalize, apostrophes, strip_accents_one, vowels, consonants
from verse import elision, remove_trivial
from pos import postag
sys.path.insert(0, "../drime")
from query import query

ORTHO = 0
CGRAM = 3
GENRE = 4
NOMBRE = 5
FREQ = 7

localization.init_locale()

cats = ['ADV', 'NOM', 'ADJ']
posses = ['A', 'N', 'ADV']
corr = {
    'ADV': 'ADV',
    'NOM': 'N',
    'ADJ': 'A'}
varcats = ['NOM', 'ADJ']
genres = ['m', 'f']
nombres = ['s', 'p']
# TODO options to favor frequent, nonfrequent words, words from a certain theme
# TODO verbs
fthresh = 1
exclude = ['travers', 'loin', 'ainsi', 'assez', 'guère', 'pas', 'partout', 'ni',
    'ne', 'là-bas', 'tant', 'est-ce', 'beau', 'fois', 'milieu', 'présent',
    'peu', 'peur', 'très', 'enfin', 'tous', 'tout', 'toute', 'toutes', 'bien',
    'peine', 'autre', 'million', 'millier', 'plus', 'seul', 'puis', 'côté',
    'encore', 'encor', 'plus', 'point', 'quelque']
mdur = 5

f = open(sys.argv[1], 'r')

offset = int(sys.argv[3])

words = {}
mwords = []
idx = {}

def adj(x, y):
  if x == '':
    return y
  return [x]

def cutword(word):
  x = re.sub("[" + apostrophes + "]", "'", word)
  if "'" in x:
    s = x.split("'")
    before, main, after = cutword(s[-1])
    return "'".join(s[:-1]) + "'" + before, main, after
  before = ""
  main = ""
  after = ""
  started = False
  finished = False
  for c in x:
    if not strip_accents_one(c)[0].lower() in vowels + consonants + ('-' if
        started else ''):
      if started:
        finished = True
        after = after + c
        continue
      before = before + c
      continue
    if not finished:
      started = True
      main = main + c
  return before, main, after

def sure(poss):
  for (cat, x, y) in poss:
    if cat not in cats:
      return False
  return True

def possible(poss, tag):
  for (cat, x, y) in poss:
    if cat in cats:
      if tag in posses:
        return True
  return False

def ok_extends(w, w2, tag):
  try:
    p = mwords[idx[w]][1]
  except KeyError:
    p = [('NOM', 'm', 's'), ('NOM', 'f', 's')]
  w2 = w2.lower()
  if w2 not in idx.keys():
    return False
  p2 = mwords[idx[w2]][1]
  for (cat, a, b) in p:
    # and corr[cat] == tag 
    if cat in cats and (cat, a, b) not in p2:
      return False
  if w2 != w and set(elision(w)) <= set(elision(w2)):
    return True
  return False

def valid_word(w, tag):
  global words, lists, idx
  if w not in idx.keys():
    return False
  p = mwords[idx[w]][1]
  if not sure(p) and not possible(p, tag):
    return False
  return True

def change(w, tag):
  #print(w, sure(p), tag, possible(p, tag))
  try:
    i = idx[w]
  except KeyError:
    i = len([w2 for w2 in idx.keys() if w2 < w])
  for (w2, rare, p2) in mwords[i:] + mwords[:i]:
    if ok_extends(w, w2, tag):
      yield w2
  yield w
  # p = idx[cat][genre][nombre][w]
  # n = len(lists[cat][genre][nombre])
  # return lists[cat][genre][nombre][(p+offset) % n]

  # if w not in words.keys():
  #   return w
  # if len(words[w]) > 1:
  #   return w
  # entry = words[w][0]
  # if entry[CGRAM] not in cats:
  #   return w
  # cat = entry[CGRAM]
  # genre = entry[GENRE]
  # nombre = entry[NOMBRE]
  # if cat in varcats and (genre not in genres or nombre not in nombres):
  #   return w
  # #print(cat, genre, nombre, w)
  # p = idx[cat][genre][nombre][w]
  # n = len(lists[cat][genre][nombre])
  # return lists[cat][genre][nombre][(p+offset) % n]

first = True
while True:
  l = f.readline()
  if not l:
    break
  # split header line
  if first:
    first = False
    continue
  s = l.split('\t')
  if s[ORTHO] not in words.keys():
    words[s[ORTHO]] = []
  words[s[ORTHO]].append(s)

f.close()
f = open(sys.argv[2], 'r')
x = f.read()
template = Template(x)
template.options['phon_supposed_ok'] = False
f.close()
template.reject_errors = True

lwords = sorted(list(words.keys()))

for w in lwords:
  if w in exclude:
    continue
  poss = set()
  oposs = set()
  ok = True
  for entry in words[w]:
    for cat in entry[CGRAM].split(','):
      #if cat not in cats:
        #ok = False
        #break
      for genre in adj(entry[GENRE], genres):
        for nombre in adj(entry[NOMBRE], nombres):
            poss.add((cat, genre, nombre))
            if float(entry[FREQ]) >= fthresh and cat in cats:
              oposs.add((cat, genre, nombre))
  if ok and len(poss) >= 1:
    idx[w] = len(mwords)
    mwords.append((w, poss, oposs))


# for cat in cats:
#   if cat not in lists.keys():
#     lists[cat] = {}
#     idx[cat] = {}
#   for genre in (genres if cat in varcats else ['']):
#     if genre not in lists[cat].keys():
#       lists[cat][genre] = {}
#       idx[cat][genre] = {}
#     for nombre in (nombres if cat in varcats else ['']):
#       if nombre not in lists[cat][genre].keys():
#         lists[cat][genre][nombre] = []
#         idx[cat][genre][nombre] = {}
#       for w in lwords:
#         if len(words[w]) == 1 and ',' not in words[w][0][CGRAM]:
#           entry = words[w][0]
#           if (entry[CGRAM] == cat and entry[GENRE] == genre and entry[NOMBRE] ==
#               nombre):
#             if float(entry[FREQ]) > fthresh:
#               idx[cat][genre][nombre][w] = len(lists[cat][genre][nombre])
#               lists[cat][genre][nombre].append(w)

whitespace_regexp = re.compile("(\s*)")

while True:
  l = sys.stdin.readline()
  if not l:
    break
  l = l.strip()
  if len(l) == 0:
    print(l)
    continue
  s = re.split(whitespace_regexp, l)
  try:
    loffset = int(s[-1])
    s = s[:-1]
  except ValueError:
    loffset = offset
  #print("before init:", template.position)
  errors = template.check(' '.join(s))
  template.back()
  #print("after init:", template.position)
  if errors:
    print ("PROBLEM with ORIGINAL")
    print (errors.report())
    continue
  lw = s[-1]
  s = remove_trivial(s, (lambda w: re.match("^\s*$", w) or
          len(normalize(w, rm_all=True)) == 0))
  r = []
  #print ("INIT rhyme: ", l)
  constraint = template.template[template.position % len(template.template)].constraint
  rhyme = Rhyme(lw, constraint, template.mergers, template.options)
  scut = [cutword(wfull) for wfull in s]
  #print(scut)
  tags = postag(scut)
  #print(tags)
  #print(scut)
  first = True
  for i, (before, ow, after) in reversed(list(enumerate(scut))):
    #print ("<%s|%s|%s>" % (before, w, after))
    w = ow.lower()
    started = time.time()
    ok = False
    tried = 0
    acceptable = 0
    if valid_word(w, tags[i]) or (ow[0] == ow[0].upper() and i > 0):
      if first and len(normalize(w)) > 0:
        first = False
        was_first = True
        rr, c, sur = query(w)
        try:
          lrhymes = sorted([x['word'] for x in rr['result']] + [w])
          it = lrhymes
          wpos = it.index(w)
          it = it[wpos+1:]
        except KeyError:
          it = change(w, tags[1])
      else:
        it = change(w, tags[i])
      for w2 in it:
        if not (ok_extends(w, w2, tags[i])):
          continue
        if time.time() - started > mdur:
          break #timeout
        if w2.lower() == w.lower():
          break
        tried += 1
        #print (w2, "try:" + ' '.join(r + [w2] + s[i+1:]))
        line = ' '.join(s[:i] + [before + w2 + after] + list(reversed(r)))
        #print ("CONSIDER: " + line)
        if was_first:
          was_first = False
          nrhyme = copy.deepcopy(rhyme)
          #print(lw, rhyme.phon, rhyme.eye)
          nrhyme.feed(w2, constraint)
          #print(normalize(line), nrhyme.phon, nrhyme.eye)
          if not nrhyme.satisfied():
            #print(nrhyme.phon, nrhyme.eye)
            #print ("... NO RHYME")
            continue
        #print ("TRY: " + line)
        #print("before inter:", template.position)
        #print ("check...")
        errors = template.check(line, quiet=True)
        #print ("...done")
        template.back()
        #print("after inter:", template.position)
        if not errors:
          acceptable += 1
          if acceptable == loffset:
            r.append(w2)
            ok = True
            break
        else:
          pass
          #print (errors.report())
    if not ok:
      r.append(w)
    if len(w) > 0 and ow[0] == ow[0].upper():
      r[-1] = r[-1][0].upper() + r[-1][1:]
    r[-1] = before + r[-1] + after
  final = ''.join(reversed(r))
  #print("before final:", template.position)
  errors = template.check(final)
  #print("after final:", template.position)
  if errors:
    print ("PROBLEM")
    print (errors.report())
    break
  print (final)
