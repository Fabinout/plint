#!/usr/bin/python3
# coding: utf-8

"""Compute the number of syllabes taken by a vowel chunk"""


def intersperse(left, right):
    if (len(left) == 0 or left[0] == ' ') and (len(right) == 0 or right[0] == ' '):
        return []
    if len(left) == 0 or left[0] == ' ':
        return ["/", right[0]] + intersperse(left, right[1:])
    if len(right) == 0 or right[0] == ' ':
        return [left[0], "/"] + intersperse(left[1:], right)
    return [left[0], right[0]] + intersperse(left[1:], right[1:])


def contains_trema(chunk):
    """Test if a string contains a word with a trema"""
    for x in ['ä', 'ë', 'ï', 'ö', 'ü', 'ÿ']:
        if x in chunk:
            return True
    return False
