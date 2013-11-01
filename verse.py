#!/usr/bin/python3

import common
from common import apostrophes, consonants, normalize, is_consonants, is_vowels, sure_end_fem, strip_accents_one
import re
import vowels
import haspirater
import error
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



class Verse:
  def elision(self, word):
    if (word.startswith('y') and not word == 'y' and not word.startswith("yp") and
        not word.startswith("yeu")):
      return [False]
    if word in ["oui", "ouis"] or word.startswith("ouistiti"):
      # elision for those words, but beware, no elision for "ouighour"
      # boileau : "Ont l'esprit mieux tourné que n'a l'homme ? Oui sans doute."
      # so elission sometimes
      return [True, False]
    # "un", "une" are non-elided as nouns ("cette une")
    if word in ["un", "une"]:
      return [True, False]
    # "onze" is not elided
    if word == "onze":
      return [False]
    if word[0] == 'h':
      return list(map((lambda s: not s), haspirater.lookup(word)))
    if is_vowels(word[0]):
      return [True]
    return [False]

  def remove_trivial(self, chunks, predicate):
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

  @property
  def line(self):
    return ''.join(x['original'] for x in self.chunks)

  @property
  def normalized(self):
    return ''.join(normalize(x['original'], strip=False)
            if 'text_pron' not in x.keys() else x['text']
            for x in self.chunks).lstrip().rstrip()

  def __init__(self, line, template, pattern):
    self.template = template
    self.pattern = pattern
    # will be updated later, used in parse and feminine
    self.phon = None

    whitespace_regexp = re.compile("(\s*)")
    ys_regexp = re.compile("(\s*)")
    all_consonants = consonants + consonants.upper()
    consonants_regexp = re.compile('([^'+all_consonants+'*-]*)', re.UNICODE)

    words = re.split(whitespace_regexp, line)
    words = self.remove_trivial(words, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_all=True)) == 0))
    pre_chunks = [re.split(consonants_regexp, word) for word in words]
    pre_chunks = [self.remove_trivial(x, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_all=True)) == 0)) for x in pre_chunks]
    self.chunks = [[{'original': y, 'text': normalize(y, rm_apostrophe=True)}
      for y in x] for x in pre_chunks]

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
        if w[i]['text'].endswith('g') and len(w[i+1]['text']) >= 2:
          if w[i+1]['text'][1] in "eéèa":
            w[i+1]['text'] = w[i+1]['text'][1:]
    # remove empty chunks created by simplifications
    for i, w in enumerate(self.chunks):
      self.chunks[i] = [x for x in w if len(x['text']) > 0]
    # remove leading and trailing crap
    for w in self.chunks:
      for p in [0, -1]:
        while len(w[p]['text']) > 0 and w[p]['text'][0] in ' -':
          w[p]['text'] = w[p]['text'][1:]
        while len(w[p]['text']) > 0 and w[p]['text'][-1] in ' -':
          w[p]['text'] = w[p]['text'][:-1]

    # sigles
    for i, w in enumerate(self.chunks):
      if len(w) == 1 and is_consonants(w[0]['text']):
        new_chunks = []
        for j, x in enumerate(w[0]['text']):
          try:
            nc = letters[x]
          except KeyError:
            nc = x + 'é'
          new_chunks += re.split(consonants_regexp, nc)
        new_chunks = [x for x in new_chunks if len(x) > 0]
        new_word = []
        for j, x in enumerate(new_chunks):
          lindex = int(j*len(w[0]['original'])/len(w[0]['text']))
          rindex = int((j+1)*len(w[0]['original'])/len(w[0]['text']))
          part = w[0]['original'][lindex:rindex]
          # set elision to True because of possible ending vowels
          # forbid hiatus and instruct that we must use text for the
          # pronunciation
          new_word.append({'original': part, 'text': x,
            'elision': [True], 'no_hiatus': True, 'text_pron': True})
        self.chunks[i] = new_word

    # vowel elision problems
    for w in self.chunks:
      if 'elision' not in w[0].keys():
        w[0]['elision'] = self.elision(''.join(x['text'] for x in w))

    # case of 'y'
    ys_regexp = re.compile("(y*)")
    for i, w in enumerate(self.chunks):
      new_word = []
      for j, chunk in enumerate(w):
        if ('y' not in chunk['text'] or len(chunk['text']) == 1  or
            chunk['text'].startswith("y")):
          new_word.append(chunk)
          continue
        # special cases of "pays" and "alcoyle"
        if (j > 0 and j < len(w) - 1 and
            ((chunk['text'] == "ay" and w[j-1]['text'].endswith("p")
              and w[j+1]['text'].startswith("s"))
            or
             (chunk['text'] == "oy" and w[j-1]['text'].endswith("lc")
              and w[j+1]['text'].startswith("l")))):
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
      if sum([1 for chunk in w if is_vowels(chunk['text'])]) <= 1:
        continue
      w[-1]['elidable'] = self.chunks[i+1][0]['elision']

    # annotate hiatus and ambiguities
    ambiguous_potential = ["ie", "ée"]
    no_hiatus = ["oui"]
    for i, w in enumerate(self.chunks[:-1]):
      if w[-1]['text'] == "s":
        if w[-2]['text'] in ambiguous_potential:
          w[-2]['error'] = "ambiguous"
          w[-1]['error'] = "ambiguous"
      if w[-1]['text'] in ambiguous_potential:
        if self.chunks[i+1][0]['text'][0] in consonants:
          w[-1]['error'] = "ambiguous"
          self.chunks[i+1][0]['error'] = "ambiguous"
      elif is_vowels(w[-1]['text']) and not w[-1]['text'].endswith('e'):
        if is_vowels(self.chunks[i+1][0]['text']):
          if ''.join(x['text'] for x in w) not in no_hiatus:
            if ''.join(x['text'] for x in self.chunks[i+1]) not in no_hiatus:
              if 'no_hiatus' not in w[-1].keys():
                w[-1]['error'] = "hiatus"
                self.chunks[i+1][0]['error'] = "hiatus"

    # annotate word ends
    for w in self.chunks[:-1]:
      w[-1]['wordend'] = True

    # collapse words
    self.chunks = sum(self.chunks, [])

  def parse(self):
    # annotate weights
    for i, chunk in enumerate(self.chunks):
      if (not is_vowels(self.chunks[i]['text'])):
        continue
      # for the case of "pays" and related words
      if 'weights' not in self.chunks[i].keys():
        self.chunks[i]['weights'] = self.possible_weights_context(i)
      self.chunks[i]['hemis'] = self.hemistiche(i)

    self.possible = self.fit(0, 0, self.pattern.hemistiches)
    self.text = self.align2str(self.chunks)

  def contains_break(self, chunk):
    return '-' in chunk['text'] or 'wordend' in chunk

  def possible_weights(self, pos):
    if self.template.options['diaeresis'] == "classical":
      return vowels.possible_weights_ctx(self.chunks, pos)
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
        if len(self.phon) == 0:
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

  def feminine(self, align):
    for a in sure_end_fem:
      if self.text.endswith(a):
        # check that this isn't a one-syllabe wourd
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
          is_vowels(chunk['text']) and (chunk['hemis'] == "ok" or not
          self.template.options['check_end_hemistiche'] and 
          chunk['hemis'] != "cut")):
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

  def align2str(self, align):
    return ''.join([x['text'] for x in align])

  def hemistiche(self, pos):
    ending = self.chunks[pos]['text']
    if not 'wordend' in self.chunks[pos] and pos < len(self.chunks) - 1:
      if not 'wordend' in self.chunks[pos+1]:
        return "cut"
      ending += self.chunks[pos+1]['text']
    if (ending in sure_end_fem):
      if True in self.chunks[pos].get('elidable', [False]):
        return "ok" # elidable final -e
      # check that this isn't a one-syllabe wourd (which is allowed)
      ok = False
      try:
        for i in range(2):
          if '-' in self.chunks[pos-i-1]['text'] or 'wordend' in self.chunks[pos-i-1]:
            ok = True
      except IndexError:
        pass
      if not ok:
        # hemistiche ends in feminine
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


