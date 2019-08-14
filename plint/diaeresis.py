#!/usr/bin/python3

"""Get the number of syllables of a vowel cluster with context"""

import os
import json
import sys


class DiaresisFinder(object):

    def __init__(self, diaresis_file="../data/diaeresis.json"):
        self._trie = None
        self._diaresis_file = diaresis_file
        self._load_diaeresis()

    def _load_diaeresis(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), self._diaresis_file)) as f:
            self._trie = json.load(f)

    def do_lookup_sub(self, trie, key):
        if len(key) == 0 or (key[0] not in trie[1].keys()):
            return trie[0]
        return self.do_lookup_sub(trie[1][key[0]], key[1:])

    def lookup(self, key):
        return self.do_lookup(key + ['-', '-'])

    def wrap_lookup(self, line_read):
        result = self.lookup(line_read)
        print("%s: %s" % (line_read, result))

    def do_lookup(self, key):
        return self.do_lookup_sub(self._trie, key)


diaresis_finder = DiaresisFinder()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        diaresis_finder = DiaresisFinder(sys.argv[1])

    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            diaresis_finder.wrap_lookup(arg)
    else:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            diaresis_finder.wrap_lookup(line.lower().lstrip().rstrip().split())
