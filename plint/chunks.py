import re
import sys
from pprint import pprint

from plint import common
from plint.chunk import Chunk
from plint.common import normalize, get_consonants_regex, SURE_END_FEM, strip_accents
from plint.hyphen_splitter import HyphenSplitter


class Chunks:

    def __init__(self, verse):
        # TODO Find a way to remove this dependency
        self.verse = verse
        self.chunks = []
        self.create_chunks()
        self.separated_chunks = []

    def create_chunks(self):
        self.initialize_chunks()
        self.collapse_apostrophes()
        self.check_forbidden_characters()
        self.simplify_gu_qu()
        self.elide_inside_words()
        self.remove_leading_and_trailing_crap()
        self.collapse_empty_chunks_from_simplifications()
        self.create_acronym()
        self.elide_vowel_problems()
        self.process_y_cases()
        self.annotate_final_mute_e()
        self.annotate_hiatus()
        self.annotate_word_ends()
        self.merge_chunks_words()
        self.print_new_line_if_changed()

    def print_new_line_if_changed(self):
        now_line = ''.join(chunk.original for chunk in self.chunks)
        if now_line != self.verse.input_line:
            print("%s became %s" % (self.verse.input_line, now_line), file=sys.stderr)
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

    def create_acronym(self):
        for i, chunk_group in enumerate(self.separated_chunks):
            if len(chunk_group) == 1:
                first_chunk = chunk_group[0]
                if first_chunk.is_consonants():
                    new_word = first_chunk.create_acronym()
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
        pre_chunks = pre_process_bi_tokens(word_bi_tokens)
        self.separated_chunks = []
        for (is_end_word, pre_chunk) in pre_chunks:
            if len(pre_chunk) != 0:
                self.separated_chunks.append([Chunk(word, self.verse) for word in pre_chunk])
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
        words = re.split(whitespace_regexp, self.verse.input_line)
        return words

    def annotate(self, template, threshold):
        # annotate weights
        for i, chunk in enumerate(self.chunks):
            if not chunk.is_vowels():
                continue

            chunks_before = self.chunks[:i]
            chunks_after = self.chunks[i + 1:]
            # for the case of "pays" and related words
            chunk.set_possible_weights_from_context(chunks_before, chunks_after, template, threshold)

            next_chunk = self.chunks[i + 1] if i < len(self.chunks) - 1 else None
            previous_chunk = self.chunks[i - 1] if i > 0 else None
            previous_previous_chunk = self.chunks[i - 2] if i > 1 else None
            chunk.set_hemistiche_from_context(previous_previous_chunk, previous_chunk, next_chunk)
        return self.align2str()

    def align2str(self):
        return ''.join([x.text for x in self.chunks])

    def print_n_syllables(self, n_syllables, offset, output_file):
        count = 0
        for i, chunk in enumerate(self.chunks[::-1]):
            if chunk.weights is not None:
                if count < offset:
                    count += 1
                    continue
                pos = len(self.chunks) - i - 1
                considered_chunk = self.chunks[pos]
                chunks_before = self.chunks[:pos]
                chunks_after = self.chunks[pos + 1:]
                print(str(n_syllables) + ' ' + ' '.join(considered_chunk.make_query(chunks_before, chunks_after)),
                      file=output_file)
                break

    def normalized(self):
        return ''.join(chunk.normalize() for chunk in self.chunks).lstrip().rstrip()

    def get_line(self):
        return ''.join(chunk.get_original_text() for chunk in self.chunks)

    def get_errors_set(self, forbidden_ok, hiatus_ok):
        errors = set()
        for chunk in self.chunks:
            errors_chunk = chunk.get_errors_set(forbidden_ok, hiatus_ok)
            errors = errors.union(errors_chunk)
        return errors

    def get_feminine(self, template, threshold, align=None):
        text = self.annotate(template, threshold)
        for a in SURE_END_FEM:
            if text.endswith(a):
                # if vowel before, it must be fem
                try:
                    if strip_accents(text[-len(a) - 1]) in common.VOWELS:
                        return ['F']
                except IndexError:
                    # too short
                    if text == "es":
                        return ['M']
                    else:
                        return ['F']
                # check that this isn't a one-syllabe word that ends with "es"
                # => must be masculine as '-es' cannot be mute then
                # => except if there is another vowel before ("fées")
                if text.endswith("es") and (len(text) == 2 or strip_accents(text[-3]) not in common.VOWELS):
                    for i in range(4):
                        try:
                            if self.chunks[-i - 1].is_masculine():
                                return ['M']
                        except IndexError:
                            return ['M']
                return ['F']
        if not text.endswith('ent'):
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
        for possible_phon in self.verse.phon:
            if possible_phon.endswith(')') or possible_phon.endswith('#'):
                possible.append('M')
            else:
                possible.append('F')
                if possible_phon.endswith('E') and text.endswith('aient'):
                    # imparfait and conditionnel are masculine...
                    possible.append('M')
        return possible

    def fit(self, hemistiches, pos=0, count=0):
        if count > self.verse.pattern.length:
            return []  # no possibilites
        if len(hemistiches) > 0 and hemistiches[0] < count:
            return []  # missed a hemistiche
        if pos == len(self.chunks):
            if count == self.verse.pattern.length:
                return [[]]  # empty list is the only possibility
            else:
                return []
        chunk = self.chunks[pos]
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
            if current.weights is not None:
                current.weight = weight
            for x in self.fit(next_hemistiches, pos + 1, count + weight):
                result.append([current] + x)
        return result

    def get_last_count(self):
        tot = 0
        for chunk in self.chunks[::-1]:
            if chunk.original.endswith(' ') or chunk.original.endswith('-'):
                if tot > 0:
                    break
            if chunk.weights is not None:
                tot += min(chunk.weights)
            if ' ' in chunk.original.rstrip() or '-' in chunk.original.rstrip():
                if tot > 0:
                    break
        return tot

    def align_from_keys(self, keys):
        lines = {}
        for key in keys:
            lines[key] = ""
        for chunk in self.chunks:
            for key in keys:
                lines[key] += chunk.get_normalized_rendering(key, keys)
        if 'weights' in keys:
            bounds = self.get_weights_bounds()
            bounds = [str(x) for x in bounds]
            lines['weights'] += " (total: " + ('-'.join(bounds)
                                               if bounds[1] > bounds[0] else bounds[0]) + ")"
        return ["> " + lines[key] for key in keys if len(lines[key].strip()) > 0]

    def get_weights_bounds(self):
        bounds = [0, 0]
        for chunk in self.chunks:
            bounds[0] += chunk.get_min_weight()
            bounds[1] += chunk.get_max_weight()
        return bounds


def remove_trivial(words, predicate):
    new_chunks = []
    words_accumulation = ""
    for i, chunk in enumerate(words):
        if predicate(chunk):
            if len(new_chunks) == 0:
                words_accumulation = words_accumulation + chunk
            else:
                new_chunks[-1] = new_chunks[-1] + chunk
        else:
            new_chunks.append(words_accumulation + chunk)
            words_accumulation = ""
    return new_chunks


def split_all_hyphen(words):
    return sum([HyphenSplitter().split(w) for w in words], [])


def is_empty_word(word):
    return re.match(r"^\s*$", word) or len(normalize(word, rm_all=True)) == 0


def pre_process_bi_tokens(word_bi_tokens):
    consonants_regexp = get_consonants_regex()
    pre_chunks = [(b, re.split(consonants_regexp, word)) for (b, word) in word_bi_tokens]
    pre_chunks = [(b, remove_trivial(x, is_empty_word)) for (b, x) in pre_chunks]
    return pre_chunks
