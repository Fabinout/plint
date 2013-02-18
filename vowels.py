#!/usr/bin/python3
#coding: utf-8

"""Compute the number of syllabes taken by a vowel chunk"""

from common import strip_accents
from diaeresis import lookup

def clear(x):
  return (x['text'] + ' ') if 'wordend' in x else x['text']

def intersperse(a, b):
  if (len(a) == 0 or a[0] == ' ') and (len(b) == 0 or b[0] == ' '):
    return []
  if len(a) == 0 or a[0] == ' ':
    return ["/", b[0]] + intersperse(a, b[1:])
  if len(b) == 0 or b[0] == ' ':
    return [a[0], "/"] + intersperse(a[1:], b)
  return [a[0], b[0]] + intersperse(a[1:], b[1:])

def contains_trema(chunk):
  """Test if a string contains a word with a trema"""
  for x in ['ä', 'ë', 'ï', 'ö', 'ü', 'ÿ']:
    if x in chunk:
      return True
  return False

threshold = 10

def make_query(chunks, pos):
  cleared = [clear(x) for x in chunks]
  if cleared[pos].endswith(' '):
    cleared[pos] = cleared[pos].rstrip()
    if pos + 1 <= len(cleared):
      cleared[pos+1] = " " + cleared[pos+1]
    else:
      cleared.append(' ')

  return [cleared[pos]] + intersperse(
      ''.join(cleared[pos+1:]),
      ''.join([x[::-1] for x in cleared[:pos][::-1]]))

def possible_weights_ctx(chunks, pos):
  chunk = chunks[pos]
  q = make_query(chunks, pos)
  #print (q)
  v = lookup(q)
  #print (v)
  if len(v.keys()) == 1 and v[list(v.keys())[0]] > threshold:
    return [int(list(v.keys())[0])]
  else:
    return possible_weights_seed(chunk)

def possible_weights_approx(chunk):
  """Return the possible number of syllabes taken by a vowel chunk (permissive
  approximation)"""
  if len(chunk) == 1:
    return [1]
  # old spelling and weird exceptions
  if chunk in ['ouï']:
    return [1, 2] # TODO unsure about that
  if chunk in ['eüi', 'aoû', 'uë']:
    return [1]
  if chunk in ['aïe', 'oë', 'ouü']:
    return [1, 2]
  if contains_trema(chunk):
    return [2]
  chunk = strip_accents(chunk, True)
  if chunk in ['ai', 'ou', 'eu', 'ei', 'eau', 'eoi', 'eui', 'au', 'oi',
      'oie', 'œi', 'œu', 'eaie', 'aie', 'oei', 'oeu', 'ea', 'ae', 'eo',
      'eoie', 'oe', 'eai', 'eue', 'aa', 'oo', 'ee', 'ii', 'aii',
      'yeu', 'ye', 'you']:
    return [1]
  if chunk == "oua":
    return [1, 2] # "pouah"
  if chunk == "ao":
    return [1, 2] # "paon"
  for x in ['oa', 'ea', 'eua', 'euo', 'ua', 'uo', 'yo', 'yau']:
    if x in chunk:
      return [2]
  # beware of "déesse"
  if chunk == 'ée':
    return [1, 2]
  if chunk[0] == 'i':
    return [1, 2]
  if chunk[0] == 'u' and (strip_accents(chunk[1]) in ['i', 'e']):
    return [1, 2]
  if chunk[0] == 'o' and chunk[1] == 'u' and len(chunk) >= 3 and strip_accents(chunk[2]) in ['i', 'e']:
    return [1, 2]
  if 'é' in chunk or 'è' in chunk:
    return [2]

  # we can't tell
  return [1, 2]

def possible_weights_seed(chunk):
  """Return the possible number of syllabes taken by a vowel chunk"""
  if len(chunk) == 1:
    return [1]
  #if chunk in ['ai', 'ou', 'eu', 'ei', 'eau', 'au', 'oi']:
  #  return [1]
  # we can't tell
  return [1, 2]

