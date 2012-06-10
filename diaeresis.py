#!/usr/bin/python3

import os
import json
import sys

f = open(os.path.join(os.path.dirname(
  os.path.realpath(__file__)), 'diaeresis.json'))
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
    for arg in sys.argv[1:]:
      wrap_lookup(arg)
  else:
    while True:
      line = sys.stdin.readline()
      if not line:
        break
      wrap_lookup(line.lower().lstrip().rstrip().split())

