#!/usr/bin/python3

from plint import error
from plint.chunks import Chunks


# the writing is designed to make frhyme succeed
# end vowels will be elided
# missing letters have a default case


class Verse:

    @property
    def line(self):
        return self.chunks.get_line()

    @property
    def normalized(self):
        return self.chunks.normalized()

    def __init__(self, input_line, template, pattern, threshold=None):
        self.template = template
        self.pattern = pattern
        self.threshold = threshold
        self.phon = None
        self.possible = None
        self.input_line = input_line
        self.chunks = Chunks(self)

    def annotate(self):
        self.chunks.annotate(self.template, self.threshold)

    def parse(self):
        self.annotate()
        self.possible = self.chunks.fit(self.pattern.hemistiches)

    def get_last_count(self):
        """return min number of syllables for last word"""
        return self.chunks.get_last_count()

    def problems(self):
        errors = self.chunks.get_errors_set(self.template.options['forbidden_ok'], self.template.options['hiatus_ok'])
        result = []
        if len(self.possible) == 0:
            result.append(error.ErrorBadMetric())
        for k in errors:
            result.append(k())
        return result

    def valid(self):
        return len(self.problems()) == 0

    def genders(self):
        result = set()
        for p in self.possible:
            result.update(set(self.chunks.get_feminine(self.template, self.threshold, p)))
        if len(self.possible) == 0:
            # try to infer gender even when metric is wrong
            result.update(set(self.chunks.get_feminine(self.template, self.threshold, None)))
        return result

    def print_n_syllables(self, n_syllables, offset, output_file):
        self.annotate()
        # only generate a context with the prescribed final weight
        # where "final" is the offset-th chunk with a weight from the end
        self.chunks.print_n_syllables(n_syllables, offset, output_file)

    def align(self):
        keys = ['original', 'error']
        if len(self.possible) == 0:
            keys.append('weights')
            if len(self.pattern.hemistiches) > 0:
                keys.append('hemis')
        return self.chunks.align_from_keys(keys)

    def print_possible(self, output_file):
        if not output_file:
            return
        possible = self.possible
        if len(possible) == 1:
            for i, chunk in enumerate(possible[0]):
                chunks_before = possible[0][:i]
                chunks_after = possible[0][i + 1:]
                chunk.print_query(chunks_after, chunks_before, output_file)
