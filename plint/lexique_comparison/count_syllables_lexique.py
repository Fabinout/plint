#!/usr/bin/python3

# count the number of syllables of words according to lexique

import sys

vowels = "ae$E2@#u)9ioO(y"
consonants = "dpgmtRwszlbkZjknfvSNJx8"

for l in sys.stdin.readlines():
    f = l.strip().split("\t")
    nsyl = 0
    for a in f[1]:
        if a in vowels:
            nsyl += 1
        elif a in consonants:
            pass
        else:
            print("unknown phoneme %s" % a, file=sys.stderr)
            sys.exit(1)
    # workaround bug in lexique
    if f[1].endswith("@") and f[0] != "afin de":
        nsyl -= 1
    print("%s\t%d" % (f[0], nsyl))

