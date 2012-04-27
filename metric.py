#!/usr/bin/python
#coding: utf-8

import re
from common import normalize, is_vowels, consonants, sure_end_fem
from vowels import possible_weights
import haspirater

def annotate_aspirated(word):
  """Annotate aspirated 'h'"""
  if word[0] != 'h':
    return word
  if haspirater.lookup(word):
    return '*'+word
  else:
    return word

def contains_break(chunk):
  return ' ' in chunk or '-' in chunk

def fit(chunks, pos, left):
  """bruteforce exploration of all possible vowel cluster weghting,
  within a maximum total of left"""
  if pos >= len(chunks):
    return [[]] # the only possibility is the empty list
  if left < 0:
    return [] # no possibilities
  # skip consonants
  if (not is_vowels(chunks[pos])):
    return [[chunks[pos]] + x for x in fit(chunks, pos+1, left)]
  else:
    if ((pos >= len(chunks) - 2 and chunks[pos] == 'e') and not (
        pos <= 0 or contains_break(chunks[pos-1])) and not (
        pos <= 1 or contains_break(chunks[pos-2]))):
      # special case for verse endings, which can get elided (or not)
      # but we don't elide lone syllables ("prends-le", etc.)
      if pos == len(chunks) - 1:
        weights = [0] # ending 'e' is elided
      elif chunks[pos+1] == 's':
        weights = [0] # ending 'es' is elided
      elif chunks[pos+1] == 'nt':
        # ending 'ent' is sometimes elided
        # actually, this will have an influence on the rhyme's gender
        weights = [0, 1]
      else:
        weights = possible_weights(chunks[pos])
    else:
      if (pos >= len(chunks) - 1 and chunks[pos] == 'e' and 
          pos > 0 and (chunks[pos-1].endswith('-c') or
            chunks[pos-1].endswith('-j'))):
        weights = [0] # -ce and -je are elided
      else:
        weights = possible_weights(chunks[pos])
    result = []
    for weight in weights:
      # combine all possibilities
      result += [[(chunks[pos], weight)] + x for x in fit(chunks, pos+1,
        left - weight)]
    return result

def feminine(align, verse):
  for a in sure_end_fem:
    if verse.endswith(a):
      return ['F']
  if not verse.endswith('ent'):
    return ['M']
  # verse ends with 'ent'
  if align[-2][1] == 0:
    return ['F'] # mute -ent
  if align[-2][1] > 0 and align[-2][0] == 'e':
    return ['M'] # non-mute "-ent" by the choice of metric
  # what now? "tient" vs. "lient" for instance, 
  # TODO check pronunciation? :-/
  return ['M', 'F']

def parse(text, bound):
  """Return possible aligns for text, bound is an upper bound on the
  align length to limit running time"""

  original_text = normalize(text)

  # avoid some vowel problems
  text = re.sub("qu", 'q', original_text)
  text = re.sub("gue", 'ge', text)
  text = re.sub("gué", 'gé', text)
  text = re.sub("guè", 'gè', text)
  text = re.sub("gua", 'ga', text)

  # split in words
  words = text.split(' ')

  # other exceptions
  for i in range(len(words)):
    # no elision on y- words except "ypérite", "yeuse", "yeux"
    if words[i].startswith('y') and words[i] != "y" and not (
        words[i].startswith('yp') or words[i].startswith('yeu')):
      words[i] = "*" + words[i]

    # no elision for "oui", "ouis", "ouistitis"
    # but elision for "ouighour"
    # TODO boileau writes:
    # "Ont l'esprit mieux tourné que n'a l'homme ? Oui sans doute."
    # so it's unclear what should be done here
    # if (words[i] == "oui" or words[i] == "ouis" or
    #     words[i].startswith("ouistiti")):
    #   words[i] = "*" + words[i]

    # no elision on those numerals
    # TODO "un" or "une" are sometimes elidable and sometimes non-elidable
    # Belle, une fois encor, réponds à mon appel.
    # Mon journal, il est vrai, a une belle une.
    if (words[i] == "onze"):
      words[i] = "*" + words[i]

    if len(words[i]) == 1 and words[i][0] in consonants:
      if (words[i] == 'w'):
        words[i] = "doublevé"
      else:
        words[i] = words[i] + "a"


  # aspirated
  words = [annotate_aspirated(word) for word in words if word != '']

  pattern = re.compile('(['+consonants+'*-]*)', re.UNICODE)

  # cut each word in chunks of vowels and consonants, with some specific
  # kludges
  for i in range(len(words)):
    words[i] = re.split(pattern, words[i])
    words[i] = [chunk for chunk in words[i] if chunk != '']
    nwords = []
    # the case of 'y' is special
    for chunk in words[i]:
      if 'y' not in chunk or len(chunk) == 1 or chunk[0] == 'y':
        nwords.append(chunk)
      else:
        a = chunk.split('y')
        nwords.append(a[0])
        nwords.append('Y')
        if a[1] != '':
          nwords.append(a[1])
        else:
          # the case of "pays" is very special :-(
          if words[i] == ['p', 'ay', 's']:
            nwords.append('y')
    words[i] = nwords
    # remove mute 'e'
    if i > 0:
      if sum([1 for chunk in words[i-1] if is_vowels(chunk)]) > 1:
        if words[i-1][-1] == 'e' and is_vowels(words[i][0], True):
          words[i-1].pop(-1)
          words[i-1][-1] = words[i-1][-1]+"`"

  # group back words
  for word in words:
    word.append(' ')
  chunks = sum(words, [])[:-1]

  # return all possibilities to weigh the vowel clusters, annotated by
  # the femininity of the align (depending both on the align and
  # original text)
  return list(map((lambda x: (x, feminine(x, original_text))),
    fit(chunks, 0, bound)))

