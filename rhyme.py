#!/usr/bin/python3 -u

import re
import sys
from pprint import pprint
import frhyme
import functools

# number of possible rhymes to consider
NBEST = 5
# phonetic vowels
vowel = list("Eeaio592O#@y%u()$")

class Constraint:
  def __init__(self, phon, eye, aphon):
    self.phon = phon # minimal number of common suffix phones
    self.eye = eye # minimal number of common suffix letters
    self.aphon = aphon # minimal number of common suffix vowel phones

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
    self.eye = self.mmax(self.eye, c.eye)
    self.aphon = self.mmax(self.aphon, c.aphon)

class Rhyme:
  def __init__(self, line, constraint):
    self.constraint = constraint
    self.phon = lookup(line)
    self.eye = line

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
        if val >= self.constraint.aphon and self.constraint.aphon >= 0:
          new_phon.add(x[-val:])
    self.phon = new_phon
    if self.eye:
      val = eye_rhyme(self.eye, eye)
      if val >= self.constraint.eye and self.constraint.eye >= 0:
        self.eye = self.eye[-val:]
      else:
        self.eye = None

  def restrict(self, r):
    """take the intersection between us and rhyme object r"""
    self.constraint.restrict(r.constraint)
    self.match(r.phon, r.eye)

  def feed(self, line, constraint=None):
    """extend us with a line and a constraint"""
    return self.restrict(Rhyme(line, constraint))

  def satisfied(self):
    return self.eye or len(self.phon) > 0

  def print(self):
    pprint(self.phon)

def suffix(x, y):
  """length of the longest common suffix of x and y"""
  bound = min(len(x), len(y))
  for i in range(bound):
    if x[-(1+i)] != y[-(1+i)]:
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

def lookup(s):
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
    constraint = Constraint(1, -1, -1)
    rhyme = Rhyme(line[0], constraint)
    for x in line[1:]:
      rhyme.feed(x)
      rhyme.print()
      if not rhyme.satisfied():
        print("No.")
        break
    if rhyme.satisfied():
      print ("Yes.")

