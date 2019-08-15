#!/usr/bin/python3

import os
import sys

# modules are in the parent folder
import plint.pattern

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from plint import template, verse, rhyme

templateobj = template.Template()
patternobj = plint.pattern.Pattern("12")

for l in sys.stdin.readlines():
    w = (l.strip().split("\t"))[0]
    v = verse.Verse(w, templateobj, patternobj)
    rhymeobj = rhyme.Rhyme(v.normalized,
                           patternobj.constraint, templateobj.mergers, templateobj.options)
    v.phon = rhymeobj.phon
    v.annotate()
    mx = 0
    mn = 0
    for c in v.chunks:
        if 'weights' in c.keys():
            mn += min(c['weights'])
            mx += max(c['weights'])
    print("%s\t%d\t%d" % (w, mn, mx))

