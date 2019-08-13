import re
import sys
from pprint import pprint

from haspirater import haspirater
from plint import common, vowels
from plint.common import is_vowels, APOSTROPHES, is_consonants, normalize, strip_accents_one, CONSONANTS, SURE_END_FEM
from plint.hyphen_splitter import HyphenSplitter


class Chunk:

    def __init__(self, word):
        self.original = word
        self.text = normalize(word, rm_apostrophe=True)
        self.hemistiche = None
        self.error = None
        self.illegal_str = None
        self.weights = None
        self.had_hyphen = None
        self.text_pron = None
        self.elision = None
        self.no_hiatus = None
        self.elidable = None
        self.word_end = False
        # TODO What is a weight without s?
        self.weight = None

    def __repr__(self):
        return "Chunk("\
                + "original:" + self.original\
                + ", text:" + self.text\
                + ", weights:" + str(self.weights or [])\
                + ", weight:" + str(self.weight or "")\
                + ", elidable:" + str(self.elidable or False)\
                + ", elision:" + str(self.elision or False)\
                + ", hemistiche:" + str(self.hemistiche)\
            + ", error:" + str(self.error)\
            + ", illegal_str:" + str(self.illegal_str)\
            + ", had_hypher:" + str(self.had_hyphen)\
            + ", text_pron:" + str(self.text_pron)\
            + ", no_hiatus:" + str(self.no_hiatus)\
            + ", word_end:" + str(self.word_end)\
            + ")" + "\n"

    def copy(self):
        new_chunk = Chunk(self.original)
        new_chunk.original = self.original
        new_chunk.text = self.text
        new_chunk.hemistiche = self.hemistiche
        new_chunk.error = self.error
        new_chunk.illegal_str = self.illegal_str
        new_chunk.weights = self.weights
        new_chunk.had_hyphen = self.had_hyphen
        new_chunk.text_pron = self.text_pron
        new_chunk.elision = self.elision
        new_chunk.no_hiatus = self.no_hiatus
        new_chunk.elidable = self.elidable
        new_chunk.word_end = self.word_end
        new_chunk.weight = self.weight
        return new_chunk

    def set_hemistiche(self, hemis):
        self.hemistiche = hemis

    def check_forbidden_characters(self):
        es = ""
        for x in self.text:
            if not common.remove_punctuation(strip_accents_one(x)[0].lower()) in common.LEGAL:
                es += 'I'
                self.error = "illegal"
            else:
                es += ' '
        if self.error is not None and self.error == "illegal":
            self.illegal_str = es

    def simplify_gu_qu(self, next_chunk):
        if next_chunk.text.startswith('u'):
            if self.text.endswith('q'):
                next_chunk.text = next_chunk.text[1:]
                if next_chunk.text == '':
                    self.original += next_chunk.original
                    next_chunk.original = ''
            if self.text.endswith('g') and len(next_chunk.text) >= 2:
                if next_chunk.text[1] in "eéèa":
                    next_chunk.text = next_chunk.text[1:]

    def elide_inside_words(self, all_next_chunks):
        if self.text == "e-":
            self.weights = [0]  # force elision
        next_chunk = all_next_chunks[0]
        if self.text == "e" and next_chunk.text.startswith("-h"):
            # collect what follows until the next hyphen or end
            flw = next_chunk.original.split('-')[1]
            for future_chunk in all_next_chunks[1:]:
                flw += future_chunk.original.split('-')[0]
                if '-' in future_chunk.original:
                    break
            # TODO: not sure if this reconstruction of the original word is bulletproof...
            if haspirater.lookup(normalize(flw)):
                self.weights = [0]
            else:
                self.weights = [1]

    def remove_leading_and_trailing_crap(self):
        seen_space = False
        seen_hyphen = False
        while len(self.text) > 0 and self.text[0] in ' -':
            if self.text[0] == ' ':
                seen_space = True
            else:
                seen_hyphen = True
            self.text = self.text[1:]
        while len(self.text) > 0 and self.text[-1] in ' -':
            if self.text[-1] == ' ':
                seen_space = True
            else:
                seen_hyphen = True
            self.text = self.text[:-1]
        if seen_hyphen and not seen_space:
            self.had_hyphen = True

    def is_empty(self):
        return len(self.text) == 0

    def add_original(self, other_chunk):
        self.original += other_chunk.original

    def create_sigles(self):
        new_chunks = []
        for j, character in enumerate(self.text):
            try:
                new_chunk_content = LETTERS[character]
                # hack: the final 'e's in letters are just to help pronunciation
                # inference and are only needed at end of word, otherwise they will
                # mess syllable count up
                if j < len(self.text) - 1 and new_chunk_content[-1] == 'e':
                    new_chunk_content = new_chunk_content[:-1]
            except KeyError:
                new_chunk_content = character + 'é'
            new_chunks += [(j, x) for x in re.split(get_consonants_regex(), new_chunk_content)]
        new_chunks = [x for x in new_chunks if len(x[1]) > 0]
        new_word = []
        last_opos = -1
        for j, (original_position, character) in enumerate(new_chunks):
            part = ""
            if j == len(new_chunks) - 1:
                # don't miss final spaces
                part = self.original[last_opos + 1:]
            elif last_opos < original_position:
                part = self.original[last_opos + 1:original_position + 1]
                last_opos = original_position
            # allow or forbid elision because of possible ending '-e' before
            # forbid hiatus both for this and for preceding
            # instruct that we must use text for the pronunciation
            new_chunk = Chunk(part)
            new_chunk.original = part
            new_chunk.text = character
            new_chunk.text_pron = True
            new_chunk.elision = [False, True]
            new_chunk.no_hiatus = True
            new_word.append(new_chunk)
            # propagate information from splithyph
            new_word[-1].hemistiche = self.hemistiche
        return new_word

    def check_elidable(self):
        if self.text == 'e':
            self.elidable = [True]

    def is_consonants(self):
        return is_consonants(self.text)

    def ends_with_apostrophe(self):
        return re.search("[" + APOSTROPHES + "]$", self.original) is not None

    def elide_vowel_problems(self, chunk_group):
        if self.elision is None:
            self.elision = elision_wrap(chunk_group)

    def process_y_cases(self, previous_chunk, next_chunk):
        new_word_from_chunk = []
        if 'y' not in self.text or len(self.text) == 1 or self.text.startswith("y"):
            new_word_from_chunk.append(self)
        else:
            if previous_chunk is not None and next_chunk is not None:
                # special cases of "pays", "alcoyle", "abbayes"
                c_text = self.text
                p_text = previous_chunk.text
                n_text = next_chunk.text
                # TODO Should you force if this condition does not apply?
                if ((c_text == "ay" and p_text.endswith("p") and n_text.startswith("s"))
                        or
                        (c_text == "oy" and p_text.endswith("lc")
                         and n_text.startswith("l"))
                        or
                        (c_text == "aye" and p_text.endswith("bb")
                         and n_text.startswith("s"))):
                    # force weight
                    self.weights = [2]
                    new_word_from_chunk.append(self)
            else:
                must_force = next_chunk is None and previous_chunk is not None and \
                             (self.text == "aye" and previous_chunk.text.endswith("bb"))
                if must_force:
                    # force weight
                    self.weights = [2]
                    new_word_from_chunk.append(self)
                else:
                    sub_chunks = re.split(re.compile("(y+)"), self.text)
                    sub_chunks = [x for x in sub_chunks if len(x) > 0]
                    for j, sub_chunk in enumerate(sub_chunks):
                        lindex = int(j * len(self.original) / len(sub_chunks))
                        rindex = int((j + 1) * len(self.original) / len(sub_chunks))
                        part = self.original[lindex:rindex]
                        new_subchunk_text = 'Y' if 'y' in sub_chunk else sub_chunk
                        new_subchunk = self.copy()
                        new_subchunk.original = part
                        new_subchunk.text = new_subchunk_text
                        new_word_from_chunk.append(new_subchunk)
        return new_word_from_chunk

    def is_vowels(self):
        return is_vowels(self.text)

    def is_dash_elidable(self):
        # "fais-le" not elidable, but "suis-je" and "est-ce" is
        return not ('-' in self.text and not self.text.endswith('-j') and not self.text.endswith('-c'))

    def check_elidable_with_next(self, next_chunk):
        if self.elidable is None:
            self.elidable = next_chunk.elision

    def is_potentially_ambiguous_hiatus(self):
        return self.text in ["ie", "ée", "ue"]

    def ends_with_potentially_ambiguous_hiatus(self):
        return len(self.text) >= 2 and self.text[-2:] in ["ie", "ée", "ue"]

    def check_potentially_ambiguous_plural(self, previous_chunk):
        if self.text == "s":
            if previous_chunk.is_potentially_ambiguous_hiatus():
                previous_chunk.error = "ambiguous"
                self.error = "ambiguous"

    def check_potentially_ambiguous_with_elision(self, next_chunk):
        if self.ends_with_potentially_ambiguous_hiatus():
            if next_chunk.elision is not None or True not in next_chunk.elision:
                self.error = "ambiguous"
                next_chunk.error = "ambiguous"

    def check_hiatus(self, previous_chunk, next_chunk, only_two_parts):
        if previous_chunk is not None:
            self.check_potentially_ambiguous_plural(previous_chunk)
        if self.ends_with_potentially_ambiguous_hiatus():
            if not any(next_chunk.elision or [False]):
                self.error = "ambiguous"
                next_chunk.error = "ambiguous"

        # elision concerns words ending with a vowel without a mute 'e'
        # that have not been marked "no_hiatus"
        # it also concerns specifically "et"
        elif (not self.text.endswith('e') and self.no_hiatus is None
              and (self.is_vowels() or self.text == 'Y')
              or (only_two_parts and previous_chunk.text == 'e' and self.text == 't')):
            # it happens if the next word is not marked no_hiatus
            # and starts with something that causes elision
            if all(next_chunk.elision) and next_chunk.no_hiatus is None:
                self.error = "hiatus"
                next_chunk.error = "hiatus"

    def make_word_end(self):
        self.word_end = True

    def contains_break(self):
        return '-' in self.text \
            or self.word_end or False \
            or self.had_hyphen or False

    def is_e(self):
        return self.text == "e"


def get_consonants_regex():
    all_consonants = CONSONANTS + CONSONANTS.upper()
    consonants_regexp = re.compile('([^' + all_consonants + '*-]+)', re.UNICODE)
    return consonants_regexp


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
        pre_chunks = self.preprocess_bi_tokens(word_bi_tokens)
        self.separated_chunks = []
        for (is_end_word, pre_chunk) in pre_chunks:
            if len(pre_chunk) != 0:
                self.separated_chunks.append([Chunk(word) for word in pre_chunk])
                if not is_end_word:
                    # word end is a fake word end
                    for chunk in self.separated_chunks[-1]:
                        chunk.set_hemistiche('cut')

    def preprocess_bi_tokens(self, word_bi_tokens):
        consonants_regexp = get_consonants_regex()
        pre_chunks = [(b, re.split(consonants_regexp, word)) for (b, word) in word_bi_tokens]
        pre_chunks = [(b, remove_trivial(x, self.is_empty_word)) for (b, x) in pre_chunks]
        return pre_chunks

    def get_word_tokens(self):
        words = self.split_input_line_by_whitespace()
        words = remove_trivial(words, self.is_empty_word)
        word_tokens = self.split_all_hyph(words)
        return word_tokens

    def split_all_hyph(self, words):
        return sum([HyphenSplitter().split(w) for w in words], [])

    def is_empty_word(self, word):
        return re.match(r"^\s*$", word) or len(normalize(word, rm_all=True)) == 0

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
                    if '-' in self.chunks[pos - i - 1].original or (self.chunks[pos - i - 1].word_end or False) :
                        ok = True
            except IndexError:
                pass
            if not ok:
                # hemistiche ends in feminine
                if any(current_chunk.elidable or [False]):
                    return "elid"  # elidable final -e, but only OK if actually elided
                else:
                    return "fem"
            else:
                print("IT IS OK", current_chunk)
        return "ok"

    def align2str(self):
        return ''.join([x.text for x in self.chunks])


LETTERS = {
    'f': 'effe',
    'h': 'ache',
    'j': 'gi',
    'k': 'ka',
    'l': 'elle',
    'm': 'aime',
    'n': 'aine',
    'q': 'cu',
    'r': 'ère',
    's': 'esse',
    'w': 'doublevé',
    'x': 'ixe',
    'z': 'zaide'
}


def elision_wrap(chunk_group):
    first_letter = common.remove_punctuation(chunk_group[0].original.strip())
    temp = elision(''.join(chunk.text for chunk in chunk_group),
                   ''.join(chunk.original for chunk in chunk_group),
                   first_letter == first_letter.upper())
    return temp


def elision(word, original_word, was_cap):
    if word.startswith('y'):
        if word == 'y':
            return [True]
        if was_cap:
            if word == 'york':
                return [False]
            # Grevisse, Le Bon usage, 14th ed., paragraphs 49-50
            # depends on whether it's French or foreign...
            return [True, False]
        else:
            exc = ["york", "yeux", "yeuse", "ypérite"]
            for w in exc:
                if word.startswith(w):
                    return [True]
            # otherwise, no elision
            return [False]
    if word in ["oui", "ouis"]:
        # elision for those words, but beware, no elision for "ouighour"
        # boileau : "Ont l'esprit mieux tourné que n'a l'homme ? Oui sans doute."
        # so elision sometimes
        return [True, False]
    if word.startswith("ouistiti") or word.startswith("ouagadougou"):
        return [False]
    # "un", "une" are non-elided as nouns ("cette une")
    if word in ["un", "une"]:
        return [True, False]
    # "onze" is not elided
    if word == "onze":
        return [False]
    if word.startswith('ulul'):
        return [False]  # ululement, ululer, etc.
    if word.startswith('uhlan'):
        return [False]  # uhlan
    if word[0] == 'h':
        if word == "huis":
            # special case, "huis" is elided but "huis clos" isn't
            return [True, False]
        # look up in haspirater using the original (but normalized) word
        return list(map((lambda s: not s),
                        haspirater.lookup(normalize(original_word))))
    if is_vowels(word[0]):
        return [True]
    return [False]


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
