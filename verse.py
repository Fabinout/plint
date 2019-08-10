#!/usr/bin/python3

import common
from common import apostrophes, consonants, normalize, is_consonants, is_vowels, sure_end_fem, strip_accents_one
import re
import vowels
import haspirater
import error
import sys
from pprint import pprint

# the writing is designed to make frhyme succeed
# end vowels will be elided
# missing letters have a default case
letters = {
    'f': 'effe',
    'h': 'ache',
    'j': 'gi',
    'k': 'ka',
    'l': 'elle',
    'm': 'aime',
    'n': 'aine',
    'q': 'cu',
    'r': 'ère',
    's': 'esse',
    'w': 'doublevé',
    'x': 'ixe',
    'z': 'zaide'
}

def elision_wrap(w):
  first_letter = common.rm_punct(w[0]['original'].strip())
  return elision(''.join(x['text'] for x in w),
            ''.join(x['original'] for x in w),
            first_letter == first_letter.upper())

def elision(word, original_word, was_cap):
  if word.startswith('y'):
    if word == 'y':
      return [True]
    if was_cap:
      if word == 'york':
        return [False]
      # Grevisse, Le Bon usage, 14th ed., paragraphs 49-50
      # depends on whether it's French or foreign...
      return [True, False]
    else:
      exc = ["york", "yeux", "yeuse", "ypérite"]
      for w in exc:
        if word.startswith(w):
          return [True]
      # otherwise, no elision
      return [False]
  if word in ["oui", "ouis"]:
    # elision for those words, but beware, no elision for "ouighour"
    # boileau : "Ont l'esprit mieux tourné que n'a l'homme ? Oui sans doute."
    # so elision sometimes
    return [True, False]
  if word.startswith("ouistiti") or word.startswith("ouagadougou"):
    return [False]
  # "un", "une" are non-elided as nouns ("cette une")
  if word in ["un", "une"]:
    return [True, False]
  # "onze" is not elided
  if word == "onze":
    return [False]
  if word.startswith('ulul'):
    return [False] # ululement, ululer, etc.
  if word.startswith('uhlan'):
    return [False] # uhlan
  if word[0] == 'h':
    if word == "huis":
      # special case, "huis" is elided but "huis clos" isn't
      return [True, False]
    # look up in haspirater using the original (but normalized) word
    return list(map((lambda s: not s),
        haspirater.lookup(normalize(original_word))))
  if is_vowels(word[0]):
    return [True]
  return [False]

def remove_trivial(chunks, predicate):
  new_chunks = []
  accu = ""
  for i, w in enumerate(chunks):
    if predicate(w):
      if len(new_chunks) == 0:
        accu = accu + w
      else:
        new_chunks[-1] = new_chunks[-1] + w
    else:
      new_chunks.append(accu + w)
      accu = ""
  return new_chunks


class Verse:

  @property
  def line(self):
    return ''.join(x['original'] for x in self.chunks)

  @property
  def normalized(self):
    return ''.join(normalize(x['original'], strip=False, rm_apostrophe_end=False)
            if 'text_pron' not in x.keys() else x['text']
            for x in self.chunks).lstrip().rstrip()

  def __init__(self, line, template, pattern, threshold=None):
    self.template = template
    self.pattern = pattern
    self.threshold = threshold
    # will be updated later, used in parse and feminine
    self.phon = None
    self.possible = None

    self.hyphen_regexp = re.compile("(-+)")
    whitespace_regexp = re.compile("(\s+)")
    all_consonants = consonants + consonants.upper()
    consonants_regexp = re.compile('([^'+all_consonants+'*-]+)', re.UNICODE)

    words = re.split(whitespace_regexp, line)
    words = remove_trivial(words, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_all=True)) == 0))
    words2 = sum([self.splithyph(w) for w in words], [])
    pre_chunks = [(b, re.split(consonants_regexp, word)) for (b, word) in words2]
    pre_chunks = [(b, remove_trivial(x, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_all=True)) == 0))) for (b, x) in pre_chunks]
    self.chunks = []
    for (b, chunk) in pre_chunks:
      if len(chunk) == 0:
        continue # no empty chunks
      self.chunks.append([{'original': y, 'text': normalize(y, rm_apostrophe=True)}
      for y in chunk])
      if not b:
        # word end is a fake word end
        for y in self.chunks[-1]:
          y['hemis'] = 'cut'

    # collapse apostrophes
    self.chunks2 = []
    acc = []
    for w in self.chunks:
      if re.search("[" + apostrophes + "]\s*$", w[-1]['original']):
        acc += w
      else:
        self.chunks2.append(acc + w)
        acc = []
    if len(acc) > 0:
      self.chunks2.append(acc)
    self.chunks = self.chunks2

    # check forbidden characters
    for w in self.chunks:
      for y in w:
        es = ""
        for x in y['text']:
          if not common.rm_punct(strip_accents_one(x)[0].lower()) in common.legal:
            es += 'I'
            y['error'] = "illegal"
          else:
            es += ' '
        if 'error' in y.keys() and y['error'] == "illegal":
          y['illegal_str'] = es

    # gu- and qu- simplifications
    for w in self.chunks:
      if len(w) < 2:
        continue
      for i, x in enumerate(w[:-1]):
        if not w[i+1]['text'].startswith('u'):
          continue
        if w[i]['text'].endswith('q'):
          w[i+1]['text'] = w[i+1]['text'][1:]
          if w[i+1]['text'] == '':
            w[i]['original'] += w[i+1]['original']
            w[i+1]['original'] = ''
        if w[i]['text'].endswith('g') and len(w[i+1]['text']) >= 2:
          if w[i+1]['text'][1] in "eéèa":
            w[i+1]['text'] = w[i+1]['text'][1:]

    # elide inside words ("porte-avions")
    for word in self.chunks:
      for i, w in enumerate(word[:-1]):
        if w['text'] == "e-":
          w['weights'] = [0] # force elision
        if (w['text'] == "e" and i < len(word) - 1 and
            word[i+1]['text'].startswith("-h")):
          # collect what follows until the next hyphen or end
          flw = word[i+1]['original'].split('-')[1]
          ii = i+2
          while ii < len(word):
              flw += word[ii]['original'].split('-')[0]
              if '-' in word[ii]['original']:
                  break
              ii += 1
          # TODO: not sure if this reconstruction of the original word is bulletproof...
          if haspirater.lookup(normalize(flw)):
              w['weights'] = [0]
          else:
              w['weights'] = [1]

    # remove leading and trailing crap
    for w in self.chunks:
      for p in range(len(w)):
        while len(w[p]['text']) > 0 and w[p]['text'][0] in ' -':
          w[p]['text'] = w[p]['text'][1:]
        while len(w[p]['text']) > 0 and w[p]['text'][-1] in ' -':
          w[p]['text'] = w[p]['text'][:-1]

    # collapse empty chunks created by simplifications
    for i, w in enumerate(self.chunks):
      new_chunks = []
      for x in self.chunks[i]:
        if len(x['text']) > 0:
          new_chunks.append(x)
        else:
          # propagate the original text
          # newly empty chunks cannot be the first ones
          new_chunks[-1]['original'] += x['original']
      self.chunks[i] = new_chunks

    # sigles
    for i, w in enumerate(self.chunks):
      if len(w) == 1 and is_consonants(w[0]['text']):
        new_chunks = []
        for j, x in enumerate(w[0]['text']):
          try:
            nc = letters[x]
            # hack: the final 'e's in letters are just to help pronunciation
            # inference and are only needed at end of word, otherwise they will
            # mess syllable count up
            if j < len(w[0]['text']) - 1 and nc[-1] == 'e':
              nc = nc[:-1]
          except KeyError:
            nc = x + 'é'
          new_chunks += [(j, x) for x in re.split(consonants_regexp, nc)]
        new_chunks = [x for x in new_chunks if len(x[1]) > 0]
        new_word = []
        last_opos = -1
        for j, (opos, x) in enumerate(new_chunks):
          part = ""
          if j == len(new_chunks) - 1:
            # don't miss final spaces
            part = w[0]['original'][last_opos+1:]
          elif last_opos < opos:
            part = w[0]['original'][last_opos+1:opos+1]
            last_opos = opos
          # allow or forbid elision because of possible ending '-e' before
          # forbid hiatus both for this and for preceding
          # instruct that we must use text for the pronunciation
          new_word.append({'original': part, 'text': x, 'text_pron': True,
            'elision': [False, True], 'no_hiatus': True})
          # propagate information from splithyph
          if 'hemis' in w[0].keys():
            new_word[-1]['hemis'] = w[0]['hemis']
        self.chunks[i] = new_word
        # the last one is also elidable
        if self.chunks[i][-1]['text'] == 'e':
          self.chunks[i][-1]['elidable'] = [True]

    # vowel elision problems
    for w in self.chunks:
      if 'elision' not in w[0].keys():
        w[0]['elision'] = elision_wrap(w)

    # case of 'y'
    ys_regexp = re.compile("(y+)")
    for i, w in enumerate(self.chunks):
      new_word = []
      for j, chunk in enumerate(w):
        if ('y' not in chunk['text'] or len(chunk['text']) == 1  or
            chunk['text'].startswith("y")):
          new_word.append(chunk)
          continue
        must_force = False
        if j > 0:
          # special cases of "pays", "alcoyle"
          c_text = chunk['text']
          p_text = w[j-1]['text']
          if j < len(w) - 1:
            n_text = w[j+1]['text']
            if ((c_text == "ay" and p_text.endswith("p")
                    and n_text.startswith("s"))
              or
                (c_text == "oy" and p_text.endswith("lc")
                    and n_text.startswith("l"))):
              must_force = True
              new_word.append(chunk)
              # force weight
              chunk['weights'] = [2]
              continue
          else:
            # special case of "abbaye"
            if (c_text == "aye" and p_text.endswith("bb")):
              must_force = True
        if must_force:
          new_word.append(chunk)
          # force weight
          chunk['weights'] = [2]
          continue
        subchunks = re.split(ys_regexp, chunk['text'])
        subchunks = [x for x in subchunks if len(x) > 0]
        for j, subchunk in enumerate(subchunks):
          lindex = int(j*len(chunk['original'])/len(subchunks))
          rindex = int((j+1)*len(chunk['original'])/len(subchunks))
          part = chunk['original'][lindex:rindex]
          new_subchunk_text = 'Y' if 'y' in subchunk else subchunk
          new_subchunk = dict(chunk)
          new_subchunk['original'] = part
          new_subchunk['text'] = new_subchunk_text
          new_word.append(new_subchunk)
      self.chunks[i] = new_word

    # annotate final mute 'e'
    for i, w in enumerate(self.chunks[:-1]):
      if w[-1]['text'] != "e":
        continue
      nweight = 0
      for chunk in w[::-1]:
        if is_vowels(chunk['text']):
          nweight += 1
        # "fais-le" not elidable, but "suis-je" and "est-ce" is
        if ('-' in chunk['text'] and not chunk['text'].endswith('-j') and not
            chunk['text'].endswith('-c')):
          break
      if nweight == 1:
        continue
      if 'elidable' not in w[-1].keys():
        w[-1]['elidable'] = self.chunks[i+1][0]['elision']

    # annotate hiatus and ambiguities
    ambiguous_potential = ["ie", "ée", "ue"]
    for i, w in enumerate(self.chunks[:-1]):
      if w[-1]['text'] == "s":
        if w[-2]['text'] in ambiguous_potential:
          w[-2]['error'] = "ambiguous"
          w[-1]['error'] = "ambiguous"
      if len(w[-1]['text']) >= 2 and w[-1]['text'][-2:] in ambiguous_potential:
        nchunk = self.chunks[i+1][0]
        if 'elision' not in nchunk.keys() or True not in nchunk['elision']:
          w[-1]['error'] = "ambiguous"
          self.chunks[i+1][0]['error'] = "ambiguous"
      elif ((is_vowels(w[-1]['text']) or w[-1]['text'] == 'Y') and not
          w[-1]['text'].endswith('e')):
        if (False not in self.chunks[i+1][0]['elision'] and 
                'no_hiatus' not in self.chunks[i+1][0].keys() and
                'no_hiatus' not in w[-1].keys()):
          w[-1]['error'] = "hiatus"
          self.chunks[i+1][0]['error'] = "hiatus"

    # annotate word ends
    for w in self.chunks[:-1]:
      w[-1]['wordend'] = True

    # collapse words
    self.chunks = sum(self.chunks, [])

    now_line = ''.join(x['original'] for x in self.chunks)
    if now_line != line:
      print("%s became %s" % (line, now_line), file=sys.stderr)
      pprint(self.chunks, stream=sys.stderr)

  def splithyph(self, word):
    """split hyphen-delimited word parts into separate words if they are only
    consonants, so that the sigle code later can deal with them (e.g. "k-way")
    annotates parts with boolean indicating if there is a word end afterward"""

    pre_chunks2 = []
    cs = re.split(self.hyphen_regexp, word)
    miss = ""
    for i in range(len(cs)):
      if re.match("^-*$", cs[i]) or re.match("^ *$", cs[i]):
        if len(pre_chunks2) > 0:
          pre_chunks2[-1] = (pre_chunks2[-1][0], pre_chunks2[-1][1] + cs[i])
          continue
        else:
          miss += cs[i]
          continue
      if is_consonants(normalize(cs[i])):
        pre_chunks2.append((False if i < len(cs) - 1 else True, miss + cs[i]))
        miss = ""
      else:
        pre_chunks2.append((True, miss + "".join(cs[i:])))
        miss = ""
        break
    if miss != "":
      if len(pre_chunks2) > 0:
        pre_chunks2[-1] = (pre_chunks2[-1][0], pre_chunks2[-1][1] + miss)
      else:
        pre_chunks2 = [(True, miss)]
    return pre_chunks2

  def annotate(self):
    # annotate weights
    for i, chunk in enumerate(self.chunks):
      if (not is_vowels(self.chunks[i]['text'])):
        continue
      # for the case of "pays" and related words
      if 'weights' not in self.chunks[i].keys():
        self.chunks[i]['weights'] = self.possible_weights_context(i)
      if 'hemis' not in self.chunks[i].keys():
        self.chunks[i]['hemis'] = self.hemistiche(i)
    self.text = self.align2str(self.chunks)

  def parse(self):
    self.annotate()

    self.possible = self.fit(0, 0, self.pattern.hemistiches)

  def contains_break(self, chunk):
    return '-' in chunk['text'] or 'wordend' in chunk

  def possible_weights(self, pos):
    if self.template.options['diaeresis'] == "classical":
      return vowels.possible_weights_ctx(self.chunks, pos,
          threshold=self.threshold)
    elif self.template.options['diaeresis'] == "permissive":
      return vowels.possible_weights_approx(self.chunks[pos]['text'])

  def possible_weights_context(self, pos):
    if ((pos >= len(self.chunks) - 2 and self.chunks[pos]['text'] == 'e')
        and not (pos == len(self.chunks) - 2 and
          is_vowels(self.chunks[pos+1]['text']))
        and not (pos <= 0 or self.contains_break(self.chunks[pos-1]))
        and not (pos <= 1 or self.contains_break(self.chunks[pos-2]))):
      # special case for verse endings, which can get elided (or not)
      # but we don't elide lone syllables ("prends-le", etc.)


      if pos == len(self.chunks) - 1:
        return [0] # ending 'e' is elided
      if self.chunks[pos+1]['text'] == 's':
        return [0] # ending 'es' is elided
      if self.chunks[pos+1]['text'] == 'nt':
        # ending 'ent' is sometimes elided, try to use pronunciation
        # actually, this will have an influence on the rhyme's gender
        # see feminine
        possible = []
        if not self.phon or len(self.phon) == 0:
          return [0, 1] # do something reasonable without pron
        for possible_phon in self.phon:
          if possible_phon.endswith(')') or possible_phon.endswith('#'):
            possible.append(1)
          else:
            possible.append(0)
        return possible
      return self.possible_weights(pos)
    if (pos == len(self.chunks) - 1 and self.chunks[pos]['text'] == 'e' and
        pos > 0 and (self.chunks[pos-1]['text'].endswith('-c') or
          self.chunks[pos-1]['text'].endswith('-j'))):
      return [0] # -ce and -je are elided
    if (pos >= len(self.chunks) - 1
        and self.chunks[pos]['text'] in ['ie', 'ée']):
      return [1]
    # elide "-ée" and "-ées", but be specific (beware of e.g. "réel")
    if (pos >= len(self.chunks) - 2
        and self.chunks[pos]['text'] == 'ée'
        and (pos == len(self.chunks) - 1
        or self.chunks[len(self.chunks)-1]['text'] == 's')):
      return [1]
    if 'elidable' in self.chunks[pos]:
      return [0 if x else 1 for x in self.chunks[pos]['elidable']]
    return self.possible_weights(pos)

  def feminine(self, align=None):
    for a in sure_end_fem:
      if self.text.endswith(a):
        # if vowel before, it must be fem
        try:
          if self.text[-len(a)-1] in common.vowels:
            return ['F']
        except IndexError:
          return ['M', 'F']
        # check that this isn't a one-syllabe word
        for i in range(4):
          try:
            if '-' in self.chunks[-i-1]['text'] or 'wordend' in self.chunks[-i-1]:
              return ['M', 'F']
          except IndexError:
            return ['M', 'F']
        return ['F']
    if not self.text.endswith('ent'):
      return ['M']
    # verse ends with 'ent'
    if align:
      if align and align[-2]['weight'] == 0:
        return ['F'] # mute -ent
      if align and align[-2]['weight'] > 0 and align[-2]['text'] == 'e':
        return ['M'] # non-mute "-ent" by the choice of metric
    possible = []
    # now, we must check pronunciation?
    # "tient" vs. "lient" for instance, "excellent"...
    for possible_phon in self.phon:
      if possible_phon.endswith(')') or possible_phon.endswith('#'):
        possible.append('M')
      else:
        possible.append('F')
        if possible_phon.endswith('E') and self.text.endswith('aient'):
          # imparfait and conditionnel are masculine...
          possible.append('M')
    return possible

  def fit(self, pos, count, hemistiches):
    if count > self.pattern.length:
      return [] # no possibilites
    if len(hemistiches) > 0 and hemistiches[0] < count:
      return [] # missed a hemistiche
    if pos == len(self.chunks):
      if count == self.pattern.length:
        return [[]] # empty list is the only possibility
      else:
        return []
    chunk = self.chunks[pos]
    result = []
    for weight in chunk.get('weights', [0]):
      next_hemistiches = hemistiches
      if (len(hemistiches) > 0 and count + weight == hemistiches[0] and
              is_vowels(chunk['text'])):
        # need to try to hemistiche
        if (chunk['hemis'] == "ok" or (chunk['hemis'] == "elid" and weight
            == 0)):
          # we hemistiche here
          next_hemistiches = next_hemistiches[1:]
      current = dict(self.chunks[pos])
      if 'weights' in current:
        current['weight'] = weight
      for x in self.fit(pos+1, count + weight, next_hemistiches):
        result.append([current] + x)
    return result

  hemis_types = {
    'ok': '/', # correct
    'cut': '?', # falls at the middle of a word
    'fem': '\\', # preceding word ends by a mute e
    }

  def lastCount(self):
    """return min number of syllables for last word"""
    
    tot = 0
    for c in self.chunks[::-1]:
      if c['original'].endswith(' ') or c['original'].endswith('-'):
        if tot > 0:
          break
      if 'weights' in c.keys():
        tot += min(c['weights'])
      if ' ' in c['original'].rstrip() or '-' in c['original'].rstrip():
        if tot > 0:
          break
    return tot

  def align2str(self, align):
    return ''.join([x['text'] for x in align])

  def hemistiche(self, pos):
    ending = self.chunks[pos]['text']
    if not 'wordend' in self.chunks[pos] and pos < len(self.chunks) - 1:
      if not 'wordend' in self.chunks[pos+1]:
        return "cut"
      ending += self.chunks[pos+1]['text']
    if (ending in sure_end_fem):
      ok_if_elid = False
      if True in self.chunks[pos].get('elidable', [False]):
        ok_if_elid = True
      # check that this isn't a one-syllabe wourd (which is allowed)
      ok = False
      try:
        for i in range(2):
          if '-' in self.chunks[pos-i-1]['original'] or 'wordend' in self.chunks[pos-i-1]:
            ok = True
      except IndexError:
        pass
      if not ok:
        # hemistiche ends in feminine
        if ok_if_elid:
          return "elid" # elidable final -e, but only OK if actually elided
        else:
          return "fem"
    return "ok"

  def problems(self):
    result = []
    errors = set()
    if len(self.possible) == 0:
      result.append(error.ErrorBadMetric())
    for c in self.chunks:
      if 'error' in c:
        if (c['error'] == "ambiguous" and not
            self.template.options['forbidden_ok']):
          errors.add(error.ErrorForbiddenPattern)
        if c['error'] == "hiatus" and not self.template.options['hiatus_ok']:
          errors.add(error.ErrorHiatus)
        if c['error'] == "illegal":
          errors.add(error.ErrorBadCharacters)
    for k in errors:
      result.append(k())
    return result

  def valid(self):
    return len(self.problems()) == 0

  def genders(self):
    result = set()
    for p in self.possible:
      result.update(set(self.feminine(p)))
    if len(self.possible) == 0:
      # try to infer gender even when metric is wrong
      result.update(set(self.feminine(None)))
    return result


