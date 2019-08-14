#!/usr/bin/python3
from plint.chunks import Chunks
from plint.common import normalize, is_vowels, SURE_END_FEM, strip_accents
from plint import error, common

# the writing is designed to make frhyme succeed
# end vowels will be elided
# missing letters have a default case

class Verse:

    @property
    def line(self):
        return ''.join(x.original for x in self.chunks.chunks)

    @property
    def normalized(self):
        return ''.join(normalize(x.original, strip=False, rm_apostrophe_end=False)
                       if x.text_pron is None else x.text
                       for x in self.chunks.chunks).lstrip().rstrip()

    def __init__(self, input_line, template, pattern, threshold=None):
        self.template = template
        self.pattern = pattern
        self.threshold = threshold
        self.phon = None
        self.possible = None
        self.input_line = input_line
        self.chunks = Chunks(self)
        self.text = None

    def annotate(self):
        self.text = self.chunks.annotate(self.template, self.threshold)

    def parse(self):
        self.annotate()
        self.possible = self.fit(0, 0, self.pattern.hemistiches)

    def feminine(self, align=None):
        for a in SURE_END_FEM:
            if self.text.endswith(a):
                # if vowel before, it must be fem
                try:
                    if strip_accents(self.text[-len(a) - 1]) in common.VOWELS:
                        return ['F']
                except IndexError:
                    # too short
                    if self.text == "es":
                        return ['M']
                    else:
                        return ['F']
                # check that this isn't a one-syllabe word that ends with "es"
                # => must be masculine as '-es' cannot be mute then
                # => except if there is another vowel before ("fées")
                if (self.text.endswith("es") and (len(self.text) == 2 or
                                                  strip_accents(self.text[-3]) not in common.VOWELS)):
                    for i in range(4):
                        try:
                            if ((self.chunks.chunks[-i - 1].had_hyphen or False) or
                                    (self.chunks.chunks[-i - 1].word_end or False)):
                                return ['M']
                        except IndexError:
                            return ['M']
                return ['F']
        if not self.text.endswith('ent'):
            return ['M']
        # verse ends with 'ent'
        if align:
            if align and align[-2].weight == 0:
                return ['F']  # mute -ent
            if align and align[-2].weight > 0 and align[-2].text == 'e':
                return ['M']  # non-mute "-ent" by the choice of metric
        possible = []
        # now, we must check pronunciation?
        # "tient" vs. "lient" for instance, "excellent"...
        for possible_phon in self.phon:
            if possible_phon.endswith(')') or possible_phon.endswith('#'):
                possible.append('M')
            else:
                possible.append('F')
                if possible_phon.endswith('E') and self.text.endswith('aient'):
                    # imparfait and conditionnel are masculine...
                    possible.append('M')
        return possible

    def fit(self, pos, count, hemistiches):
        if count > self.pattern.length:
            return []  # no possibilites
        if len(hemistiches) > 0 and hemistiches[0] < count:
            return []  # missed a hemistiche
        if pos == len(self.chunks.chunks):
            if count == self.pattern.length:
                return [[]]  # empty list is the only possibility
            else:
                return []
        chunk = self.chunks.chunks[pos]
        result = []
        for weight in (chunk.weights or [0]):
            next_hemistiches = hemistiches
            if (len(hemistiches) > 0 and count + weight == hemistiches[0] and
                    chunk.is_vowels()):
                # need to try to hemistiche
                if chunk.hemistiche == "ok" or (chunk.hemistiche == "elid" and weight == 0):
                    # we hemistiche here
                    next_hemistiches = next_hemistiches[1:]
            current = chunk.copy()
            # TODO There was written "weight" here, without the s. Are we sure of the condition?
            if current.weights is not None:
                current.weight = weight
            for x in self.fit(pos + 1, count + weight, next_hemistiches):
                result.append([current] + x)
        return result

    hemis_types = {
        'ok': '/',  # correct
        'cut': '?',  # falls at the middle of a word
        'fem': '\\',  # preceding word ends by a mute e
    }

    def last_count(self):
        """return min number of syllables for last word"""

        tot = 0
        for chunk in self.chunks.chunks[::-1]:
            if chunk.original.endswith(' ') or chunk.original.endswith('-'):
                if tot > 0:
                    break
            if chunk.weights is not None:
                tot += min(chunk.weights)
            if ' ' in chunk.original.rstrip() or '-' in chunk.original.rstrip():
                if tot > 0:
                    break
        return tot

    def problems(self):
        result = []
        errors = set()
        if len(self.possible) == 0:
            result.append(error.ErrorBadMetric())
        for chunk in self.chunks.chunks:
            if chunk.error is not None:
                if chunk.error == "ambiguous" and not self.template.options['forbidden_ok']:
                    errors.add(error.ErrorForbiddenPattern)
                if chunk.error == "hiatus" and not self.template.options['hiatus_ok']:
                    errors.add(error.ErrorHiatus)
                if chunk.error == "illegal":
                    errors.add(error.ErrorBadCharacters)
        for k in errors:
            result.append(k())
        return result

    def valid(self):
        return len(self.problems()) == 0

    def genders(self):
        result = set()
        for p in self.possible:
            result.update(set(self.feminine(p)))
        if len(self.possible) == 0:
            # try to infer gender even when metric is wrong
            result.update(set(self.feminine(None)))
        return result
