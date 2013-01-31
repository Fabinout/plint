#!/usr/bin/python3

from common import consonants, normalize, is_consonants, is_vowels, sure_end_fem
import re
import vowels
import haspirater

class Verse:
  def vowel_elision(self, word):
    if (word.startswith('y') and not word == 'y' and not word.startswith("yp") and
        not word.startswith("yeu")):
      return "*"
    if word in ["oui", "ouis"] or word.startswith("ouistiti"):
      # elision for those words, but beware, no elision for "ouighour"
      # boileau : "Ont l'esprit mieux tourné que n'a l'homme ? Oui sans doute."
      # so elission sometimes
      return "?"
    if word in ["un", "une"]:
      return "?"
    if word == "onze":
      return "*"
    if word[0] == 'h':
      result = haspirater.lookup(word)
      # TODO actually implement this
      if result == None:
        return "?"
      if result:
        return "*"
      else:
        return ""
    return ""

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

  def __init__(self, line):
    whitespace_regexp = re.compile("(\s*)")
    ys_regexp = re.compile("(\s*)")
    all_consonants = consonants + consonants.upper()
    consonants_regexp = re.compile('(['+all_consonants+'*-]*)', re.UNICODE)
    words = re.split(whitespace_regexp, line)
    words = self.remove_trivial(words, (lambda w: re.match("^\s*$", w)))
    pre_chunks = [re.split(consonants_regexp, word) for word in words]
    pre_chunks = [self.remove_trivial(x, (lambda w: re.match("^\s*$", w) or
      len(normalize(w)) == 0)) for x in pre_chunks]
    self.chunks = [[{'original': y, 'text': normalize(y)} for y in x] for x in pre_chunks]

    # gu- and qu- simplifications
    for w in self.chunks:
      if len(w) < 2:
        continue
      for i, x in enumerate(w[:-1]):
        if len(w[i+1]['text']) < 2 or not w[i+1]['text'].startswith("u"):
          continue
        if w[i]['text'] == 'q':
          w[i+1]['text'] = w[i+1]['text'][1:]
        if w[i]['text'] == 'g':
          if w[i+1]['text'][1] in "eéèa":
            w[i+1]['text'] = w[i+1]['text'][1:]

    # vowel elision problems
    for w in self.chunks:
      fw = ''.join(x['text'] for x in w)
      w[0]['text'] = self.vowel_elision(fw) + w[0]['text']

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
    for w in self.chunks:
      if w[-1]['text'] != "e":
        continue
      if sum([1 for chunk in w if is_vowels(chunk['text'])]) <= 1:
        continue
      w[-1]['text'] = "e_"

    # annotate hiatus and ambiguities
    ambiguous_potential = ["ie", "ée"]
    no_hiatus = ["oui"]
    for i, w in enumerate(self.chunks[:-1]):
      if w[-1]['text'] == "s":
        if w[-2]['text'] in ambiguous_potential:
          w[-2]['error'] = "ambiguous"
      if w[-1]['text'] in ambiguous_potential:
        if self.chunks[i+1][0]['text'][0] in consonants + "*":
          w[-1]['error'] = "ambiguous"
      elif is_vowels(w[-1]['text']) and '_' not in w[-1]['text']:
        if is_vowels(self.chunks[i+1][0]['text']):
          if ''.join(x['text'] for x in w) not in no_hiatus:
            if ''.join(x['text'] for x in self.chunks[i+1]) not in no_hiatus:
              w[-1]['error'] = "hiatus"

    # collapse words
    self.chunks = sum(self.chunks, [])

    self.text = ''.join(x['original'] for x in self.chunks)

  def contains_break(self, chunk):
    return '-' in chunk['text']

  def possible_weights(self, pos, diaeresis):
    if diaeresis == "classical":
      return vowels.possible_weights_ctx([x['text'] for x in self.chunks], pos)
    elif diaeresis == "permissive":
      return vowels.possible_weights_approx(self.chunks[pos]['text'])

  def fit(self, pos, left, diaeresis):
    """bruteforce exploration of all possible vowel cluster weghting,
    within a maximum total of left"""
    if pos >= len(self.chunks):
      return [[]] # the only possibility is the empty list
    if left < 0:
      return [] # no possibilities
    # skip consonants
    if (not is_vowels(self.chunks[pos]['text'])):
      return [[self.chunks[pos]] + x for x in self.fit(pos+1, left, diaeresis)]
    else:
      if ((pos >= len(self.chunks) - 2 and self.chunks[pos]['text'] == 'e') and not (
          pos <= 0 or self.contains_break(self.chunks[pos-1])) and not (
          pos <= 1 or self.contains_break(self.chunks[pos-2]))):
        # special case for verse endings, which can get elided (or not)
        # but we don't elide lone syllables ("prends-le", etc.)
        if pos == len(self.chunks) - 1:
          weights = [0] # ending 'e' is elided
        elif self.chunks[pos+1]['text'] == 's':
          weights = [0] # ending 'es' is elided
        elif self.chunks[pos+1]['text'] == 'nt':
          # ending 'ent' is sometimes elided
          # actually, this will have an influence on the rhyme's gender
          weights = [0, 1]
        else:
          weights = self.possible_weights(pos, diaeresis)
      else:
        if (pos >= len(self.chunks) - 1 and self.chunks[pos] == 'e' and
            pos > 0 and (self.chunks[pos-1]['text'].endswith('-c') or
              self.chunks[pos-1]['text'].endswith('-j'))):
          weights = [0] # -ce and -je are elided
        else:
          if self.chunks[pos]['text'] == "e_":
            if self.chunks[pos+1]['text'][0] in consonants + "*":
              weights = [1]
            elif self.chunks[pos+1]['text'][0] == "?":
              weights = [0, 1]
            else:
              weights = [1]
          weights = self.possible_weights(pos, diaeresis)
      result = []
      for weight in weights:
        # combine all possibilities
        thispos = dict(self.chunks[pos])
        thispos['weight'] = weight
        for x in self.fit(pos+1, left - weight, diaeresis):
          result.append([thispos] + x)
      return result

  def feminine(self, align, phon):
    for a in sure_end_fem:
      if self.text.endswith(a):
        # check that this isn't a one-syllabe wourd
        for i in range(4):
          for j in ' -':
            try:
              if j in align[-i-1]:
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

  def coffee(self, phon, bound, diaeresis):
    return list(map((lambda x: (x, self.feminine(x, phon))),
        self.fit(0, bound, diaeresis)))

  def fits(self, bound, diaeresis):
    return self.fit(0, bound, diaeresis)
