#!/usr/bin/python3

"""Get the number of syllables of a vowel cluster with context"""

import os
import json
import sys


class DiaeresisFinder(object):

    def __init__(self, diaeresis_file="../data/diaeresis.json"):
        self._trie = None
        self._diaeresis_file = diaeresis_file
        try:
            self._load_diaeresis()
        except json.JSONDecodeError:
            pass  # cannot read the file, we assume that another file will be loaded later

    def _load_diaeresis(self):
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), self._diaeresis_file)) as f:
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


diaeresis_finder = DiaeresisFinder()


def set_diaeresis(diaeresis_file):
    global diaeresis_finder
    diaeresis_finder = DiaeresisFinder(diaeresis_file=diaeresis_file)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        diaeresis_finder = DiaeresisFinder(sys.argv[1])

    if len(sys.argv) > 2:
        for arg in sys.argv[2:]:
            diaeresis_finder.wrap_lookup(arg)
    else:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            diaeresis_finder.wrap_lookup(line.lower().lstrip().rstrip().split())
