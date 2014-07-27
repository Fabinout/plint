#!/usr/bin/python3

"""Get the number of syllables of a vowel cluster with context"""

import os
import json
import sys

trie = None

def load_diaeresis(fname):
  global trie
  f = open(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), fname))
  trie = json.load(f)
  f.close()

def do_lookup(trie, key):
  if len(key) == 0 or (key[0] not in trie[1].keys()):
    return trie[0]
  return do_lookup(trie[1][key[0]], key[1:])

def lookup(key):
  return do_lookup(trie, key + ['-', '-'])

def wrap_lookup(line):
  result = lookup(line)
  print("%s: %s" % (line, result))

if __name__ == '__main__':
  if len(sys.argv) > 1:
    load_diaeresis(sys.argv[1])
  else:
    load_diaeresis("diaeresis.json")

  if len(sys.argv) > 2:
    for arg in sys.argv[2:]:
      wrap_lookup(arg)
  else:
    while True:
      line = sys.stdin.readline()
      if not line:
        break
      wrap_lookup(line.lower().lstrip().rstrip().split())

