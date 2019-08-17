#!/usr/bin/python3 -u
# encoding: utf8

import copy
import re
import sys
from pprint import pprint
from frhyme import frhyme
import functools
from plint.options import default_options
from plint.common import is_vowels, normalize

# number of possible rhymes to consider
NBEST = 5
# phonetic vowels
vowel = list("Eeaio592O#@y%u()$")

# use for supposed liaison both in phon and eye
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
    'ï': 'hi',
    "ai": "é",
    'm': 'n',
    'à': 'a',
    'û': 'u',
    'ù': 'u'
}


def mmax(a, b):
    """max, with -1 representing infinity"""
    if a == -1 or b == -1:
        return -1
    else:
        return max(a, b)


class Constraint:

    def __init__(self, classical=True, phon=1):
        self.phon = phon  # minimal number of common suffix phones
        self.classical = classical  # should we impose classical rhyme rules

    def restrict(self, c):
        """take the max between us and constraint object c"""
        if not c:
            return
        self.phon = mmax(self.phon, c.phon)
        self.classical = self.classical or c.classical


class Rhyme:

    def __init__(self, line, constraint=None, mergers=None, options=None, phon=None):
        if constraint:
            self.constraint = constraint
        else:
            self.constraint = Constraint()
        self.mergers = {}
        # length of smallest end-of-verse word in syllables
        # will be provided later
        self.last_count = 42
        if options:
            self.options = options
        else:
            self.options = default_options
        if mergers:
            for phon_set in mergers:
                for pho in phon_set[1:]:
                    self.mergers[pho] = phon_set[0]
        if not phon:
            phon = self.lookup(line)
        self.phon = set([self.apply_mergers(x) for x in phon])
        self.eye = self.supposed_liaison(self.consonant_suffix(line))
        self.raw_eye = line
        self.old_phon = None
        self.old_eye = None
        self.old_raw_eye = None
        self.old_last_count = None
        self.new_rhyme = None

        # store if rhyme is a succession of two vowels
        self.double_vocalic = False
        l2 = normalize(line)
        if len(l2) >= 2:
            if is_vowels(l2[-2], with_y=False, with_h=False):
                self.double_vocalic = True
            if l2[-2] == 'h':
                if len(l2) >= 3 and is_vowels(l2[-3], with_y=False, with_h=False):
                    self.double_vocalic = True
        self.old_double_vocalic = False

    def apply_mergers(self, phon):
        return ''.join([(self.mergers[x] if x in self.mergers.keys()
                         else x) for x in phon])

    def supposed_liaison(self, x):
        if x[-1] in liaison.keys() and self.options['eye_supposed_ok']:
            return x[:-1] + liaison[x[-1]]
        return x

    def rollback(self):
        self.phon = self.old_phon
        self.eye = self.old_eye
        self.raw_eye = self.old_raw_eye
        self.last_count = self.old_last_count
        self.double_vocalic = self.old_double_vocalic

    def sufficient_phon(self):
        # return the shortest accepted rhymes among old_phon
        ok = set()
        for p in self.phon:
            slen = len(p)
            for i in range(len(p)):
                if p[-(i + 1)] in vowel:
                    slen = i + 1
                    break
            slen = max(slen, self.constraint.phon)
            ok.add(p[-slen:])
        return ok

    def sufficient_eye_length(self, old_phon=None):
        if not self.constraint.classical:
            return self.eye, 0  # not classical, nothing required
        if ((old_phon >= 2 if old_phon else self.satisfied_phon(2))
                or not self.options['poor_eye_required']):
            return self.eye, 1
        if self.last_count == 1:
            return self.eye, 1
        if self.options['poor_eye_vocalic_ok'] and self.double_vocalic:
            return self.eye, 1
        if self.options['poor_eye_supposed_ok']:
            return self.eye, 2
        else:
            return self.raw_eye, 2

    def sufficient_eye(self, old_phon=None):
        d, val = self.sufficient_eye_length(old_phon)
        if val <= len(d):
            return d[-val:]
        else:
            return d

    def match(self, phon, eye, raw_eye):
        """limit our phon and eye to those which match phon and eye and which respect constraints"""
        new_phon = set()
        for x in self.phon:
            for y in phon:
                val = phon_rhyme(x, y)
                if 0 <= self.constraint.phon <= val:
                    new_phon.add(x[-val:])
        self.phon = new_phon
        if self.eye:
            val = eye_rhyme(self.eye, eye)
            if val == 0:
                self.eye = ""
            else:
                self.eye = self.eye[-val:]
        if self.raw_eye:
            val = eye_rhyme(self.raw_eye, raw_eye)
            if val == 0:
                self.raw_eye = ""
            else:
                self.raw_eye = self.raw_eye[-val:]

    def adjust_last_count(self, v):
        self.last_count = min(self.last_count, v)

    def restrict(self, r):
        """take the intersection between us and rhyme object r"""
        if self.satisfied():
            self.old_phon = self.phon
            self.old_eye = self.eye
            self.old_last_count = self.last_count
            self.old_double_vocalic = self.double_vocalic
            self.old_raw_eye = self.raw_eye
        # lastCount will be applied later
        self.constraint.restrict(r.constraint)
        self.new_rhyme = r
        if not r.double_vocalic:
            self.double_vocalic = False  # rhyme is ok if all rhymes are double vocalic
        self.match(set([self.apply_mergers(x) for x in r.phon]),
                   self.supposed_liaison(self.consonant_suffix(r.eye)), r.raw_eye)

    def consonant_suffix(self, s):
        if not self.options['eye_tolerance_ok']:
            return s
        for k in tolerance.keys():
            if s.endswith(k):
                return s[:-(len(k))] + tolerance[k]
        return s

    def feed(self, line, constraint=None):
        """extend us with a line and a constraint"""
        # lastCount is not applied yet
        return self.restrict(Rhyme(line, constraint, self.mergers, self.options))

    def satisfied_phon(self, val=None):
        if not val:
            val = self.constraint.phon
        for x in self.phon:
            if len(x) >= val:
                return True
        return False

    def satisfied_eye(self):
        d, val = self.sufficient_eye_length()
        return len(d) >= val

    def satisfied(self):
        return self.satisfied_phon() and self.satisfied_eye()

    def pprint(self):
        pprint(self.phon)

    def adjust(self, result, s):
        """add liason kludges"""
        result2 = copy.deepcopy(result)
        # adjust for tolerance with classical rhymes
        # e.g. "vautours"/"ours", "estomac"/"Sidrac"
        if self.options['phon_supposed_ok']:
            # the case 'ent' would lead to trouble for gender
            if s[-1] in liaison.keys() and not s.endswith('ent'):
                for r in result2:
                    result.add(r + liaison[s[-1]])
                    if s[-1] == 's':
                        result.add(r + 's')
        return result

    def lookup(self, s):
        """lookup the pronunciation of s, adding rime normande kludges"""
        result = raw_lookup(s)
        if self.options['normande_ok'] and (s.endswith('er') or s.endswith('ers')):
            result.add("ER")
        return self.adjust(result, s)


def suffix(x, y):
    """length of the longest common suffix of x and y"""
    bound = min(len(x), len(y))
    for i in range(bound):
        a = x[-(1 + i)]
        b = y[-(1 + i)]
        if a != b:
            return i
    return bound


def phon_rhyme(x, y):
    """are x and y acceptable phonetic rhymes?"""
    assert (isinstance(x, str))
    assert (isinstance(y, str))
    nphon = suffix(x, y)
    for c in x[-nphon:]:
        if c in vowel:
            return nphon
    return 0


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


def raw_lookup(s):
    # kludge: take the last three words and concatenate them to take short words
    # into account
    s = s.split(' ')[-3:]
    sets = list(map((lambda a: set([x[1] for x in
                                    frhyme.lookup(escape(a), NBEST)])), s))
    return functools.reduce(concat_couples, sets, {''})


# workaround for lexique
def escape(t):
    return re.sub('œ', 'oe', re.sub('æ', 'ae', t))


if __name__ == '__main__':
    while True:
        input_line = sys.stdin.readline()
        if not input_line:
            break
        input_line = input_line.lower().strip().split(' ')
        if len(input_line) < 1:
            continue
        rhyme = Rhyme(input_line[0], Constraint())
        for character in input_line[1:]:
            rhyme.feed(character, 42)
            rhyme.pprint()
            if not rhyme.satisfied():
                print("No.")
                break
        if rhyme.satisfied():
            print("Yes.")
