#!/usr/bin/python3
#coding: utf-8

import unicodedata
import re

vowels = 'aeiouyœæ'
consonants = "bcçdfghjklmnpqrstvwxz'"
legal = vowels + consonants + ' -'

# a variant of x-sampa such that all french phonemes are one-character
SUBSTS = [
  ('#', 'A~'),
  ('$', 'O~'),
  (')', 'E~'),
  ('(', '9~'),
    ]

# Forbidden at the end of a hemistiche. "-ent" would also be forbidden
# in some cases but not others...
sure_end_fem = ['es', 'e', 'ë']

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents_one(s, with_except=False):
  """Strip accent from a string
  
  with_except keeps specifically 'é' and 'è'"""
  r = []
  for x in s:
    if with_except and x in ['è', 'é']:
      r.append(x)
    else:
      r += unicodedata.normalize('NFD', x)
  return r

def strip_accents(s, with_except=False):
  return ''.join(
      (c for c in strip_accents_one(s, with_except)
      if unicodedata.category(c) != 'Mn'))

def norm_spaces(text):
  """Remove multiple consecutive whitespace"""
  return re.sub("\s+-*\s*", ' ', text)

def rm_punct(text):
  """Remove punctuation from text"""
  text = re.sub("’", "'", text) # no weird apostrophes
  text = re.sub("' ", "'", text) # space after apostrophes

  #TODO rather: keep only good chars
  pattern = re.compile("[^'\w -]", re.UNICODE)
  text2 = pattern.sub(' ', text)
  return text2

def is_vowels(chunk, with_h=False, with_y=True):
  """Test if a chunk is vowels

  with_h counts 'h' as vowel, with_y allows 'y'"""

  if not with_y and chunk == 'y':
    return False
  for char in strip_accents(chunk):
    if char not in vowels:
      if char != 'h' or not with_h:
        return False
  return True

def is_consonants(chunk):
  """Test if a chunk is consonants"""

  for char in strip_accents(chunk):
    if char not in consonants:
      return False
  return True

def normalize(text, downcase=True):
  """Normalize text, ie. lowercase, no useless punctuation or whitespace"""
  return norm_spaces(rm_punct(text.lower() if downcase else text)).rstrip().lstrip()

def subst(string, subs):
  if len(subs) == 0:
    return string
  return subst(string.replace(subs[0][0], subs[0][1]), subs[1:])

def to_xsampa(s):
  """convert our modified format to x-sampa"""
  return subst(s, SUBSTS)

def from_xsampa(s):
  """convert x-sampa to our modified format"""
  return subst(s, [(x[1], x[0]) for x in SUBSTS])

