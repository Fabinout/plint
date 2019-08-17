import os


def nature_count(x):
    # for uppercased words, only one occurrence should be allowed
    if x.lower() != x:
        return 1
    try:
        return count[x]
    except KeyError:
        # return a reasonable overapproximation
        return 9


count = {}

f = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/occurrences'))

while True:
    line = f.readline()
    if not line:
        break
    line = line.rstrip().split(' ')
    count[line[0]] = int(line[1])
