#!/usr/bin/python3 -u
#encoding: utf8

import copy
import re
import sys
from pprint import pprint
import frhyme
import functools
from common import consonants

# number of possible rhymes to consider
NBEST = 5
# phonetic vowels
vowel = list("Eeaio592O#@y%u()$")

liaison = {
    'c': 'k',
    'd': 't',
    'g': 'k',
    'k': 'k',
    'p': 'p',
    'r': 'R',
    's': 'z',
    't': 't',
    'x': 'z',
    'z': 'z',
    }

tolerance = {
    'ï': 'i',
    "ai": "é",
    'm': 'n',
    'à': 'a',
    'û': 'u',
    }


class Constraint:
  def __init__(self, classical, phon):
    self.phon = phon # minimal number of common suffix phones
    self.classical = classical # should we impose classical rhyme rules

  def mmax(self, a, b):
    """max, with -1 representing infty"""
    if a == -1 or b == -1:
      return -1
    else:
      return max(a, b)

  def restrict(self, c):
    """take the max between us and constraint object c"""
    if not c:
      return
    self.phon = self.mmax(self.phon, c.phon)
    self.eye = self.classical or c.classical

class Rhyme:
  def apply_mergers(self, phon):
    return ''.join([(self.mergers[x] if x in self.mergers.keys()
        else x) for x in phon])

  def supposed_liaison(self, x):
    if x[-1] in liaison.keys():
      return x + liaison[x[-1]]
    return x

  def __init__(self, line, constraint, mergers=[], normande_ok=True, phon=None):
    self.constraint = constraint
    self.mergers = {}
    self.normande_ok = normande_ok
    for phon_set in mergers:
      for phon in phon_set[1:]:
        self.mergers[phon] = phon_set[0]
    if not phon:
      phon = self.lookup(line)
    self.phon = set([self.apply_mergers(x) for x in phon])
    self.eye = self.supposed_liaison(consonant_suffix(line))

  def match(self, phon, eye):
    """limit our phon and eye to those which match phon and eye and which
    respect constraints"""
    new_phon = set()
    for x in self.phon:
      for y in phon:
        val = phon_rhyme(x, y)
        if val >= self.constraint.phon and self.constraint.phon >= 0:
          new_phon.add(x[-val:])
        val = assonance_rhyme(x, y)
    self.phon = new_phon
    if self.eye:
      val = eye_rhyme(self.eye, eye)
      if val == 0:
        self.eye = ""
      else:
        self.eye = self.eye[-val:]

  def restrict(self, r):
    """take the intersection between us and rhyme object r"""
    self.constraint.restrict(r.constraint)
    self.match(set([self.apply_mergers(x) for x in r.phon]),
        self.supposed_liaison(consonant_suffix(r.eye)))

  def feed(self, line, constraint=None):
    """extend us with a line and a constraint"""
    return self.restrict(Rhyme(line, constraint, self.mergers))

  def satisfied(self):
    return (len(self.phon) >= self.constraint.phon
        and len(self.eye) >= self.constraint.eye
        and (len(self.eye) > 0 or not self.constraint.classical))

  def pprint(self):
    pprint(self.phon)

  def adjust(self, result):
    """add liason kludges"""
    # TODO better here
    result2 = copy.deepcopy(result)
    # the case 'ent' would lead to trouble for gender
    if self.constraint.classical:
      if s[-1] in liaison.keys() and not s.endswith('ent'):
        for r in result2:
          result.add(r + liaison[s[-1]])
          if (s[-1] == 's'):
            result.add(r + 's')
    return result


  def lookup(self, s):
    """lookup the pronunciation of s, adding rime normande kludges"""
    result = raw_lookup(s)
    if self.normande_ok and (s.endswith('er') or s.endswith('ers')):
      result.add("ER")
    return self.adjust(result)

def suffix(x, y):
  """length of the longest common suffix of x and y"""
  bound = min(len(x), len(y))
  for i in range(bound):
    a = x[-(1+i)]
    b = y[-(1+i)]
    if a != b:
      return i
  return bound

def phon_rhyme(x, y):
  """are x and y acceptable phonetic rhymes?"""
  assert(isinstance(x, str))
  assert(isinstance(y, str))
  nphon = suffix(x, y)
  for c in x[-nphon:]:
    if c in vowel:
      return nphon
  return 0

def strip_consonants(x):
  return str([a for a in x if a in vowel or a == 'j'])

def assonance_rhyme(x, y):
  return phon_rhyme(strip_consonants(x), strip_consonants(y))

def eye_rhyme(x, y):
  """value of x and y as an eye rhyme"""
  return suffix(x, y)

def concat_couples(a, b):
  """the set of x+y for x in a, y in b"""
  s = set()
  for x in a:
    for y in b:
      s.add(x + y)
  return s

def consonant_suffix(s):
  for k in tolerance.keys():
    if s.endswith(k):
      s = s[:-(len(k))] + tolerance[k]
  for i in range(len(s)):
    if not s[-(i+1)] in consonants:
      break
  result = s[-(i):]
  return result

def raw_lookup(s):
  # kludge: take the last three words and concatenate them to take short words
  # into account
  s = s.split(' ')[-3:]
  sets = list(map((lambda a: set([x[1] for x in
    frhyme.lookup(escape(a), NBEST)])), s))
  return functools.reduce(concat_couples, sets, set(['']))

#workaround for lexique
def escape(t):
  return re.sub('œ', 'oe', re.sub('æ', 'ae', t))

if __name__ == '__main__':
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    line = line.lower().strip().split(' ')
    if len(line) < 1:
      continue
    constraint = Constraint(True, 1)
    rhyme = Rhyme(line[0], constraint, self.mergers, self.normande_ok)
    for x in line[1:]:
      rhyme.feed(x)
      rhyme.pprint()
      if not rhyme.satisfied():
        print("No.")
        break
    if rhyme.satisfied():
      print ("Yes.")

