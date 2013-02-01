#!/usr/bin/python3

from common import consonants, normalize, is_consonants, is_vowels, sure_end_fem
import re
import vowels
import haspirater

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
      # TODO change this when haspirater changes
      return [not haspirater.lookup(word)]
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

  def __init__(self, line, diaeresis):
    self.diaeresis = diaeresis
    whitespace_regexp = re.compile("(\s*)")
    ys_regexp = re.compile("(\s*)")
    all_consonants = consonants + consonants.upper()
    consonants_regexp = re.compile('([^'+all_consonants+'*-]*)', re.UNICODE)
    words = re.split(whitespace_regexp, line)
    words = self.remove_trivial(words, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_apostrophe=True)) == 0))
    pre_chunks = [re.split(consonants_regexp, word) for word in words]
    pre_chunks = [self.remove_trivial(x, (lambda w: re.match("^\s*$", w) or
      len(normalize(w, rm_apostrophe=True)) == 0)) for x in pre_chunks]
    self.chunks = [[{'original': y, 'text': normalize(y, rm_apostrophe=True)}
      for y in x] for x in pre_chunks]

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

    # vowel elision problems
    for w in self.chunks:
      w[0]['elision'] = self.elision(''.join(x['text'] for x in w))

    # sigles
    for i, w in enumerate(self.chunks):
      if len(w) == 1 and is_consonants(w[0]['text']):
        new_word = []
        for j, x in enumerate(w[0]['text']):
          lindex = int(j*len(w[0]['original'])/len(w[0]['text']))
          rindex = int((j+1)*len(w[0]['original'])/len(w[0]['text']))
          part = w[0]['original'][lindex:rindex]
          if (x == 'w'):
            new_word.append({'original': part, 'text': "doublevé"})
          else:
            new_word.append({'original': part, 'text': x + "é"})
        self.chunks[i] = new_word

    # case of 'y'
    ys_regexp = re.compile("(y*)")
    for i, w in enumerate(self.chunks):
      new_word = []
      for j, chunk in enumerate(w):
        if ('y' not in chunk['text'] or len(chunk['text']) == 1  or
            chunk['text'].startswith("y")):
          new_word.append(chunk)
          continue
        # special case of "pays"
        if (chunk['text'] == "ay" and j > 0 and j < len(w) - 1 and
            w[j-1]['text'].endswith("p") and w[j+1]['text'].startswith("s")):
          new_word.append(chunk)
          continue
        subchunks = re.split(ys_regexp, chunk['text'])
        subchunks = [x for x in subchunks if len(x) > 0]
        for j, subchunk in enumerate(subchunks):
          lindex = int(j*len(chunk['original'])/len(subchunks))
          rindex = int((j+1)*len(chunk['original'])/len(subchunks))
          part = chunk['original'][lindex:rindex]
          new_subchunk = 'Y' if 'y' in subchunk else subchunk
          new_word.append({'original': part, 'text': new_subchunk})
      self.chunks[i] = new_word

    # annotate final mute 'e'
    for w in self.chunks[:-1]:
      if w[-1]['text'] != "e":
        continue
      if sum([1 for chunk in w if is_vowels(chunk['text'])]) <= 1:
        continue
      w[-1]['elidable'] = True

    # annotate hiatus and ambiguities
    ambiguous_potential = ["ie", "ée"]
    no_hiatus = ["oui"]
    for i, w in enumerate(self.chunks[:-1]):
      if w[-1]['text'] == "s":
        if w[-2]['text'] in ambiguous_potential:
          w[-2]['error'] = "ambiguous"
      if w[-1]['text'] in ambiguous_potential:
        if self.chunks[i+1][0]['text'][0] in consonants:
          w[-1]['error'] = "ambiguous"
      elif is_vowels(w[-1]['text']) and not w[-1]['text'].endswith('e'):
        if is_vowels(self.chunks[i+1][0]['text']):
          if ''.join(x['text'] for x in w) not in no_hiatus:
            if ''.join(x['text'] for x in self.chunks[i+1]) not in no_hiatus:
              w[-1]['error'] = "hiatus"

    # annotate word ends
    for w in self.chunks[:-1]:
      w[-1]['wordend'] = True

    # collapse words
    self.chunks = sum(self.chunks, [])

    self.text = ''.join(x['text'] for x in self.chunks)

  def contains_break(self, chunk):
    return '-' in chunk['text'] or 'wordend' in chunk

  def possible_weights(self, pos):
    if self.diaeresis == "classical":
      return vowels.possible_weights_ctx([x['text'] for x in self.chunks], pos)
    elif self.diaeresis == "permissive":
      return vowels.possible_weights_approx(self.chunks[pos]['text'])

  def possible_weights_context(self, pos):
      if ((pos >= len(self.chunks) - 2 and self.chunks[pos]['text'] == 'e')
          and not (pos <= 0 or self.contains_break(self.chunks[pos-1]))
          and not (pos <= 1 or self.contains_break(self.chunks[pos-2]))):
        # special case for verse endings, which can get elided (or not)
        # but we don't elide lone syllables ("prends-le", etc.)
        if pos == len(self.chunks) - 1:
          return [0] # ending 'e' is elided
        if self.chunks[pos+1]['text'] == 's':
          return [0] # ending 'es' is elided
        if self.chunks[pos+1]['text'] == 'nt':
          # ending 'ent' is sometimes elided
          # actually, this will have an influence on the rhyme's gender
          return [0, 1]
      if (pos >= len(self.chunks) - 2
          and self.chunks[pos]['text'] in ['ie', 'ée']):
        return [1]
      else:
        if (pos >= len(self.chunks) - 1 and self.chunks[pos] == 'e' and
            pos > 0 and (self.chunks[pos-1]['text'].endswith('-c') or
              self.chunks[pos-1]['text'].endswith('-j'))):
          return [0] # -ce and -je are elided
        if 'elidable' in self.chunks[pos]:
          return [0 if x else 1 for x in self.chunks[pos+1]['elision']]
      return self.possible_weights(pos)

  def fit(self, pos, left):
    """bruteforce exploration of all possible vowel cluster weghting,
    within a maximum total of left"""
    if pos >= len(self.chunks):
      return [[]] # the only possibility is the empty list
    if left < 0:
      return [] # no possibilities
    # skip consonants
    if (not is_vowels(self.chunks[pos]['text'])):
      return [[dict(self.chunks[pos])] + x for x in self.fit(pos+1, left)]
    else:
      result = []
      for weight in self.possible_weights_context(pos):
        # combine all possibilities
        thispos = dict(self.chunks[pos])
        thispos['weight'] = weight
        for x in self.fit(pos+1, left - weight):
          result.append([thispos] + x)
      return result

  def feminine(self, align, phon):
    for a in sure_end_fem:
      if self.text.endswith(a):
        # check that this isn't a one-syllabe wourd
        for i in range(4):
          try:
            if '-' in align[-i-1]['text'] or 'wordend' in align[-i-1]:
              return ['M', 'F']
          except IndexError:
            return ['M', 'F']
        return ['F']
    if not self.text.endswith('ent'):
      return ['M']
    # verse ends with 'ent'
    if align[-2]['weight'] == 0:
      return ['F'] # mute -ent
    if align[-2]['weight'] > 0 and align[-2]['text'] == 'e':
      return ['M'] # non-mute "-ent" by the choice of metric
    possible = []
    # now, we must check pronunciation?
    # "tient" vs. "lient" for instance, "excellent"...
    for possible_phon in phon:
      if possible_phon.endswith(')') or possible_phon.endswith('#'):
        possible.append('M')
      else:
        possible.append('F')
        if possible_phon.endswith('E') and self.text.endswith('aient'):
          # imparfait and conditionnel are masculine...
          possible.append('M')
    return possible

  def coffee(self, phon, bound):
    return list(map((lambda x: (x, self.feminine(x, phon))),
        self.fits(bound)))

  def fits(self, bound):
    return self.fit(0, bound)
