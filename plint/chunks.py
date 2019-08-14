import re
import sys
from pprint import pprint

from plint import vowels
from plint.chunk import Chunk
from plint.common import normalize, SURE_END_FEM, get_consonants_regex
from plint.hyphen_splitter import HyphenSplitter


class Chunks:

    def __init__(self, line):
        self._line = line
        self.chunks = []
        self.create_chunks()
        self.phon = None
        self.separated_chunks = []

    def create_chunks(self):
        self.initialize_chunks()
        self.collapse_apostrophes()
        self.check_forbidden_characters()
        self.simplify_gu_qu()
        self.elide_inside_words()
        self.remove_leading_and_trailing_crap()
        self.collapse_empty_chunks_from_simplifications()
        self.create_sigles()
        self.elide_vowel_problems()
        self.process_y_cases()
        self.annotate_final_mute_e()
        self.annotate_hiatus()
        self.annotate_word_ends()
        self.merge_chunks_words()
        self.print_new_line_if_changed()

    def print_new_line_if_changed(self):
        now_line = ''.join(chunk.original for chunk in self.chunks)
        if now_line != self._line:
            print("%s became %s" % (self._line, now_line), file=sys.stderr)
            pprint(self.chunks, stream=sys.stderr)

    def merge_chunks_words(self):
        self.chunks = sum(self.separated_chunks, [])

    def annotate_word_ends(self):
        for chunk_group in self.separated_chunks[:-1]:
            chunk_group[-1].make_word_end()

    def annotate_hiatus(self):
        for i, chunk_group in enumerate(self.separated_chunks[:-1]):
            last_chunk = chunk_group[-1]
            next_chunk = self.separated_chunks[i + 1][0]
            if len(chunk_group) >= 2:
                previous_last_chunk = chunk_group[-2]
            else:
                previous_last_chunk = None
            only_two_parts = len(chunk_group) == 2
            last_chunk.check_hiatus(previous_last_chunk, next_chunk, only_two_parts)

    def annotate_final_mute_e(self):
        for i, chunk_group in enumerate(self.separated_chunks[:-1]):
            if chunk_group[-1].is_e():
                n_weight = 0
                for chunk in chunk_group[::-1]:
                    if chunk.is_vowels():
                        n_weight += 1
                    if not chunk.is_dash_elidable():
                        break
                if n_weight == 1:
                    continue
                next_group_first_chunk = self.separated_chunks[i + 1][0]
                chunk_group[-1].check_elidable_with_next(next_group_first_chunk)

    def process_y_cases(self):
        for i, chunk_group in enumerate(self.separated_chunks):
            new_word = []
            for j, chunk in enumerate(chunk_group):
                if j != 0:
                    previous_chunk = chunk_group[j - 1]
                else:
                    previous_chunk = None
                if j != len(chunk_group) - 1:
                    next_chunk = chunk_group[j + 1]
                else:
                    next_chunk = None
                new_word_from_chunk = chunk.process_y_cases(previous_chunk, next_chunk)
                new_word += new_word_from_chunk
            self.separated_chunks[i] = new_word

    def elide_vowel_problems(self):
        for chunk_group in self.separated_chunks:
            chunk_group[0].elide_vowel_problems(chunk_group)

    def collapse_apostrophes(self):
        future_chunks = []
        acc = []
        for chunk_group in self.separated_chunks:
            if chunk_group[-1].ends_with_apostrophe():
                acc += chunk_group
            else:
                future_chunks.append(acc + chunk_group)
                acc = []
        if acc:
            future_chunks.append(acc)
        self.separated_chunks = future_chunks

    def create_sigles(self):
        for i, chunk_group in enumerate(self.separated_chunks):
            if len(chunk_group) == 1:
                first_chunk = chunk_group[0]
                if first_chunk.is_consonants():
                    new_word = first_chunk.create_sigles()
                    self.separated_chunks[i] = new_word
                    self.separated_chunks[i][-1].check_elidable()

    def collapse_empty_chunks_from_simplifications(self):
        for i, chunk_group in enumerate(self.separated_chunks):
            new_chunks = []
            for chunk in chunk_group:
                if not chunk.is_empty():
                    new_chunks.append(chunk)
                else:
                    # propagate the original text
                    # newly empty chunks cannot be the first ones
                    new_chunks[-1].add_original(chunk)
            self.separated_chunks[i] = new_chunks

    def remove_leading_and_trailing_crap(self):
        for chunk_group in self.separated_chunks:
            for chunk in chunk_group:
                chunk.remove_leading_and_trailing_crap()

    def elide_inside_words(self):
        for chunk_group in self.separated_chunks:
            for i, chunk in enumerate(chunk_group[:-1]):
                all_next_chunks = chunk_group[i + 1:]
                chunk.elide_inside_words(all_next_chunks)

    def simplify_gu_qu(self):
        for chunk_group in self.separated_chunks:
            if len(chunk_group) >= 2:
                for i, chunk in enumerate(chunk_group[:-1]):
                    next_chunk = chunk_group[i + 1]
                    chunk.simplify_gu_qu(next_chunk)

    def check_forbidden_characters(self):
        for chunk_group in self.separated_chunks:
            for chunk in chunk_group:
                chunk.check_forbidden_characters()

    def initialize_chunks(self):
        word_bi_tokens = self.get_word_tokens()
        pre_chunks = preprocess_bi_tokens(word_bi_tokens)
        self.separated_chunks = []
        for (is_end_word, pre_chunk) in pre_chunks:
            if len(pre_chunk) != 0:
                self.separated_chunks.append([Chunk(word) for word in pre_chunk])
                if not is_end_word:
                    # word end is a fake word end
                    for chunk in self.separated_chunks[-1]:
                        chunk.set_hemistiche('cut')

    def get_word_tokens(self):
        words = self.split_input_line_by_whitespace()
        words = remove_trivial(words, is_empty_word)
        word_tokens = split_all_hyphen(words)
        return word_tokens

    def split_input_line_by_whitespace(self):
        whitespace_regexp = re.compile(r"(\s+)")
        words = re.split(whitespace_regexp, self._line)
        return words

    def annotate(self, template, threshold):
        # annotate weights
        for i, chunk in enumerate(self.chunks):
            if not chunk.is_vowels():
                continue
            # for the case of "pays" and related words
            if chunk.weights is None:
                chunk.weights = self.possible_weights_context(i, template, threshold)
            if chunk.hemistiche is None:
                chunk.hemistiche = self.hemistiche(i)
        return self.align2str()

    def possible_weights_context(self, pos, template, threshold):
        chunk = self.chunks[pos]
        if pos != len(self.chunks) - 1:
            next_chunk = self.chunks[pos + 1]
        else:
            next_chunk = None
        if pos > 0:
            previous_chunk = self.chunks[pos - 1]
        else:
            previous_chunk = None
        if pos > 1:
            previous_previous_chunk = self.chunks[pos - 2]
        else:
            previous_previous_chunk = None

        if ((pos >= len(self.chunks) - 2 and chunk.is_e())
                and not (next_chunk is not None and next_chunk.is_vowels())
                and not (previous_chunk is None or previous_chunk.contains_break())
                and not (previous_previous_chunk is None or previous_previous_chunk.contains_break())):
            # special case for verse endings, which can get elided (or not)
            # but we don't elide lone syllables ("prends-le", etc.)

            if next_chunk is None:
                return [0]  # ending 'e' is elided
            if next_chunk.text == 's':
                return [0]  # ending 'es' is elided
            if next_chunk.text == 'nt':
                # ending 'ent' is sometimes elided, try to use pronunciation
                # actually, this will have an influence on the rhyme's gender
                # see feminine
                possible = []
                if not self.phon or len(self.phon) == 0:
                    return [0, 1]  # do something reasonable without pron
                for possible_phon in self.phon:
                    if possible_phon.endswith(')') or possible_phon.endswith('#'):
                        possible.append(1)
                    else:
                        possible.append(0)
                return possible
            return self.possible_weights(pos, template, threshold)
        if (next_chunk is None and chunk.text == 'e' and
                previous_chunk is not None and (previous_chunk.text.endswith('-c')
                                                or previous_chunk.text.endswith('-j')
                                                or (previous_chunk.text == 'c'
                                                    and previous_chunk.had_hyphen is not None)
                                                or (previous_chunk.text == 'j'
                                                    and previous_chunk.had_hyphen is not None))):
            return [0]  # -ce and -je are elided
        if next_chunk is None and chunk.text in ['ie', 'ée']:
            return [1]
        # elide "-ée" and "-ées", but be specific (beware of e.g. "réel")
        if (pos >= len(self.chunks) - 2
                and chunk.text == 'ée'
                and (next_chunk is None or self.chunks[-1].text == 's')):
            return [1]
        if chunk.elidable is not None:
            return [int(not x) for x in chunk.elidable]
        return self.possible_weights(pos, template, threshold)

    def possible_weights(self, pos, template, threshold):
        if template.options['diaeresis'] == "classical":
            return vowels.possible_weights_ctx(self.chunks, pos, threshold=threshold)
        elif template.options['diaeresis'] == "permissive":
            return vowels.possible_weights_approx(self.chunks[pos].text)

    def hemistiche(self, pos):
        current_chunk = self.chunks[pos]
        ending = current_chunk.text
        if not (current_chunk.word_end or False) and pos < len(self.chunks) - 1:
            if not (self.chunks[pos + 1].word_end or False):
                return "cut"
            ending += self.chunks[pos + 1].text
        if ending in SURE_END_FEM:
            # check that this isn't a one-syllabe wourd (which is allowed)
            ok = False
            try:
                for i in range(2):
                    if '-' in self.chunks[pos - i - 1].original or (self.chunks[pos - i - 1].word_end or False):
                        ok = True
            except IndexError:
                pass
            if not ok:
                # hemistiche ends in feminine
                if any(current_chunk.elidable or [False]):
                    return "elid"  # elidable final -e, but only OK if actually elided
                else:
                    return "fem"
        return "ok"

    def align2str(self):
        return ''.join([x.text for x in self.chunks])


def remove_trivial(chunks, predicate):
    new_chunks = []
    accu = ""
    for i, w in enumerate(chunks):
        if predicate(w):
            if len(new_chunks) == 0:
                accu = accu + w
            else:
                new_chunks[-1] = new_chunks[-1] + w
        else:
            new_chunks.append(accu + w)
            accu = ""
    return new_chunks


def split_all_hyphen(words):
    return sum([HyphenSplitter().split(w) for w in words], [])


def is_empty_word(word):
    return re.match(r"^\s*$", word) or len(normalize(word, rm_all=True)) == 0


def preprocess_bi_tokens(word_bi_tokens):
    consonants_regexp = get_consonants_regex()
    pre_chunks = [(b, re.split(consonants_regexp, word)) for (b, word) in word_bi_tokens]
    pre_chunks = [(b, remove_trivial(x, is_empty_word)) for (b, x) in pre_chunks]
    return pre_chunks
