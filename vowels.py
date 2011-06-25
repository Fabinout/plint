#!/usr/bin/python3

from common import strip_accents

def contains_trema(chunk):
  for x in ['ä', 'ï', 'ö', 'ü', 'ÿ']:
    if x in chunk:
      return True
  return False

def possible_weights(chunk):
  if len(chunk) == 1:
    return [1]
  # old spelling and weird exceptions
  if chunk in ['ouï']:
    return [2]
  if chunk in ['eüi', 'aoû']:
    return [1]
  if contains_trema(chunk):
    return [2]
  chunk = strip_accents(chunk, True)
  # TODO 'ée' ? ('déesse')
  if chunk in ['ai', 'ou', 'eu', 'ei', 'eau', 'eoi', 'eui', 'au', 'oi',
      'oie', 'œi', 'œu', 'eaie', 'aie', 'oei', 'oeu', 'ea', 'ae', 'eo',
      'eoie', 'oe', 'eai', 'eue', 'aa', 'oo', 'ee', 'ii', 'aii',
      'yeu', 'ye']:
    return [1]
  for x in ['oa', 'ea', 'eua', 'ao', 'euo', 'ua', 'uo', 'yo', 'yau']:
    if x in chunk:
      return [2]
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
  # only non-accented left
  
  # TODO hmm
  return [99]
