import re

from haspirater import haspirater
from plint import common
from plint.common import normalize, strip_accents_one, is_consonants, APOSTROPHES, is_vowels, get_consonants_regex


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
        return "Chunk(" \
               + "original:" + self.original \
               + ", text:" + self.text \
               + ", weights:" + str(self.weights or []) \
               + ", weight:" + str(self.weight or "") \
               + ", elidable:" + str(self.elidable or False) \
               + ", elision:" + str(self.elision or False) \
               + ", hemistiche:" + str(self.hemistiche) \
               + ", error:" + str(self.error) \
               + ", illegal_str:" + str(self.illegal_str) \
               + ", had_hypher:" + str(self.had_hyphen) \
               + ", text_pron:" + str(self.text_pron) \
               + ", no_hiatus:" + str(self.no_hiatus) \
               + ", word_end:" + str(self.word_end) \
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
                    return new_word_from_chunk
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
