#!/usr/bin/python3
# coding: utf-8

import unicodedata
import re

VOWELS = 'aeiouyœæ'
CONSONANTS = "bcçdfghjklmnpqrstvwxzñĝ'"
APOSTROPHES = "'’`"
LEGAL = VOWELS + CONSONANTS + ' -'

# a variant of x-sampa such that all french phonemes are one-character
SUBSTITUTIONS = [
    ('#', 'A~'),
    ('$', 'O~'),
    (')', 'E~'),
    ('(', '9~'),
]

# Forbidden at the end of a hemistiche. "-ent" would also be forbidden
# in some cases but not others...
SURE_END_FEM = ['es', 'e', 'ë']


# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents_one(s, with_except=False):
    """Strip accent from a string with_except keeps specifically 'é' and 'è'"""
    r = []
    for x in s:
        if with_except and x in ['è', 'é']:
            r.append(x)
        else:
            r += unicodedata.normalize('NFD', x)
    return r


def strip_accents(s, with_except=False):
    return ''.join(
        (c for c in strip_accents_one(s, with_except)
         if unicodedata.category(c) != 'Mn'))


def normalize_spaces(text):
    """Remove multiple consecutive whitespace"""
    return re.sub(r"\s+-*\s*", ' ', text)


def remove_punctuation(text, rm_all=False, rm_apostrophe=False, rm_apostrophe_end=True):
    """Remove punctuation from text"""
    text = re.sub("[" + APOSTROPHES + "]", "'", text)  # no weird apostrophes
    if rm_apostrophe:
        text = re.sub(r"'", "", text)
    if rm_apostrophe_end:
        text = re.sub(r"'*$", "", text)  # apostrophes at end of line
    text = re.sub(r"[‒–—―⁓⸺⸻]", " ", text)  # no weird dashes
    text = re.sub(r"^--*\s", " ", text)  # no isolated dashes
    text = re.sub(r"--*\s", " ", text)  # no trailing dashes
    text = re.sub(r"^\s*-\s*$", " ", text)  # no lone dash
    text = re.sub(r"^--*$", "", text)  # no only dashes

    # TODO rather: keep only good chars
    if not rm_all:
        pattern = re.compile(r"[^'\w -]", re.UNICODE)
        text2 = pattern.sub(' ', text)
    else:
        pattern = re.compile(r"[^\w]", re.UNICODE)
        text2 = pattern.sub('', text)
    text2 = re.sub(r"\s'*$", " ", text2)  # no lonely apostrophes
    text2 = re.sub(r"^'*$", "", text2)  # not only apostrophes
    return text2


def is_vowels(chunk_text, with_h=False, with_y=True, with_crap=False):
    """Test if a chunk is vowels with_h counts 'h' as vowel, with_y allows 'y'"""
    if not with_y and chunk_text == 'y':
        return False
    for char in strip_accents(chunk_text):
        if char not in VOWELS and (char != 'h' or not with_h) and (char not in ['*', '?'] or not with_crap):
            return False
    return True


def is_consonants(chunk_text):
    """Test if a chunk is consonants"""
    for char in strip_accents(chunk_text):
        if char not in CONSONANTS:
            return False
    return True


def normalize(text, downcase=True, rm_all=False, rm_apostrophe=False,
              rm_apostrophe_end=True, strip=True):
    """Normalize text, ie. lowercase, no useless punctuation or whitespace"""
    res = normalize_spaces(remove_punctuation(text.lower() if downcase else text,
                                              rm_all=rm_all, rm_apostrophe=rm_apostrophe,
                                              rm_apostrophe_end=rm_apostrophe_end))
    if strip:
        return res.rstrip().lstrip()
    else:
        return res


def subst(string, subs):
    if len(subs) == 0:
        return string
    return subst(string.replace(subs[0][0], subs[0][1]), subs[1:])


def to_xsampa(s):
    """convert our modified format to x-sampa"""
    return subst(s, SUBSTITUTIONS)


def from_xsampa(s):
    """convert x-sampa to our modified format"""
    return subst(s, [(x[1], x[0]) for x in SUBSTITUTIONS])


def get_consonants_regex():
    all_consonants = CONSONANTS + CONSONANTS.upper()
    consonants_regexp = re.compile(r'([^' + all_consonants + '*-]+)', re.UNICODE)
    return consonants_regexp
