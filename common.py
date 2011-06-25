#!/usr/bin/python3

import unicodedata
import re

vowels = 'aeiouyœæ'

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents_one(s, with_except):
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
  return re.sub("\s+-*\s*", ' ', text)

def rm_punct(text):
  text = re.sub("'", '', text)
  #TODO rather: keep only good chars
  pattern = re.compile('[^\w -]', re.UNICODE)
  return pattern.sub(' ', text)

def is_vowels(chunk, with_h = False, with_y = True):
  if not with_y and chunk == 'y':
    return False
  for char in strip_accents(chunk):
    if char not in vowels:
      if char != 'h' or not with_h:
        return False
  return True

def normalize(text):
  return norm_spaces(rm_punct(text.lower())).rstrip().lstrip()

