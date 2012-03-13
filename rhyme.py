#!/usr/bin/python3 -u

import re
import sys
from pprint import pprint
import frhyme
import functools

# number of possible rhymes to consider
NBEST = 5
# phonetic vowels
vowel = list("Eeaio592O#@y%u")

def suffix(x, y):
  """length of the longest common suffix of x and y"""
  bound = min(len(x), len(y))
  for i in range(bound):
    if x[-(1+i)] != y[-(1+i)]:
      return i
  return bound

def rhyme(x, y):
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
  return rhyme(strip_consonants(x), strip_consonants(y))

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

def init_rhyme(line, constraint):
  """initialize a rhyme"""
  return (lookup(line), line, constraint)

def mmax(a, b):
  """max, with -1 representing infty"""
  if a == -1 or b == -1:
    return -1
  else:
    return max(a, b)

def max_constraints(a, b):
  # TODO get rid of that
  return (mmax(a[0], b[0]), mmax(a[1], b[1]), mmax(a[2], b[2]))

def check_rhyme(current, new):
  oldp, old, old_constraints = current
  new, new_constraints = new
  constraints = max_constraints(new_constraints, old_constraints)
  newp = lookup(new)
  newp_r, new_r = match(oldp, old, newp, new, constraints)
  return (newp_r, new_r, constraints)

def match(ap, a, bp, b, constraints):
  # ap is the possible pronunciations, a the only possible writing
  normalc, eyec, assonancec = constraints
  rp = set()
  for x in ap:
    for y in bp:
      val = rhyme(x, y)
      if val >= normalc and normalc >= 0:
        rp.add(x[-val:])
      val = assonance_rhyme(x, y)
      if val >= assonancec and assonancec >= 0:
        rp.add(x[-val:])
  if a != None:
    val = eye_rhyme(a, b)
    if val >= eyec and eyec >= 0:
      r = a[0][-val:]
    else:
      r = None
  else:
    r = None
  return rp, r

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
    constraint = (1, -1, -1)
    np, p, c = init_rhyme(line[0], constraint)
    pprint(np)
    ok = True
    for x in line[1:]:
      np, n, c = check_rhyme((np, p, c), (x, constraint))
      pprint(np)
      if n == None and len(np) == 0:
        print("No.")
        ok = False
        break
    if ok:
      print ("Yes.")

