#!/usr/bin/python3
#coding: utf-8

"""Compute the number of syllabes taken by a vowel chunk"""

from common import strip_accents

def contains_trema(chunk):
  """Test if a string contains a word with a trema"""
  for x in ['ä', 'ë', 'ï', 'ö', 'ü', 'ÿ']:
    if x in chunk:
      return True
  return False

def possible_weights(chunk):
  """Return the possible number of syllabes taken by a vowel chunk"""
  if len(chunk) == 1:
    return [1]
  # old spelling and weird exceptions
  if chunk in ['ouï']:
    return [1, 2] # TODO unsure about that
  if chunk in ['eüi', 'aoû', 'uë']:
    return [1]
  if contains_trema(chunk):
    return [2]
  chunk = strip_accents(chunk, True)
  if chunk in ['ai', 'ou', 'eu', 'ei', 'eau', 'eoi', 'eui', 'au', 'oi',
      'oie', 'œi', 'œu', 'eaie', 'aie', 'oei', 'oeu', 'ea', 'ae', 'eo',
      'eoie', 'oe', 'eai', 'eue', 'aa', 'oo', 'ee', 'ii', 'aii',
      'yeu', 'ye']:
    return [1]
  for x in ['oa', 'ea', 'eua', 'ao', 'euo', 'ua', 'uo', 'yo', 'yau']:
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

