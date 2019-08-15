#!/usr/bin/python3

import os
import sys

# modules are in the parent folder
import plint.pattern
from plint.rhyme import Rhyme
from plint.template import Template
from plint.verse import Verse

sys.path.insert(1, os.path.join(sys.path[0], '..'))

template = Template()
pattern = plint.pattern.Pattern("12")

for l in sys.stdin.readlines():
    w = (l.strip().split("\t"))[0]
    verse = Verse(w, template, pattern)
    rhyme = Rhyme(verse.normalized,
                  pattern.constraint, template.mergers, template.options)
    verse.phon = rhyme.phon
    verse.annotate()
    mx = 0
    mn = 0
    for c in verse.chunks:
        if 'weights' in c.keys():
            mn += min(c['weights'])
            mx += max(c['weights'])
    print("%s\t%d\t%d" % (w, mn, mx))

