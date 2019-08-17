import re
import sys

from haspirater import haspirater
from plint import common, diaeresis, error
from plint.common import normalize, strip_accents_one, is_consonants, APOSTROPHES, is_vowels, get_consonants_regex, \
    strip_accents, SURE_END_FEM
from plint.error import ErrorCollection
from plint.vowels import contains_trema, intersperse


DEFAULT_THRESHOLD = 3


class Chunk:

    def __init__(self, word, verse):
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
        self.verse = verse

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
        new_chunk = Chunk(self.original, self.verse)
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

    def set_hemistiche(self, hemistiche):
        # The hemistiche can take the following values
        #    ok: correct
        #    cut: falls at the middle of a word
        #    fem: preceding word ends by a mute e
        self.hemistiche = hemistiche

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

    def create_acronym(self):
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
            new_chunk = Chunk(part, self.verse)
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

    def possible_weights_approx(self):
        """Return the possible number of syllabes taken by a vowel chunk (permissive approximation)"""
        chunk_text = self.text
        if len(chunk_text) == 1:
            return [1]
        # old spelling and weird exceptions
        if chunk_text in ['ouï']:
            return [1, 2]  # TODO unsure about that
        if chunk_text in ['eüi', 'aoû', 'uë']:
            return [1]
        if chunk_text in ['aïe', 'oë', 'ouü']:
            return [1, 2]
        if contains_trema(chunk_text):
            return [2]
        chunk_text = strip_accents(chunk_text, True)
        if chunk_text in ['ai', 'ou', 'eu', 'ei', 'eau', 'eoi', 'eui', 'au', 'oi',
                          'oie', 'œi', 'œu', 'eaie', 'aie', 'oei', 'oeu', 'ea', 'ae', 'eo',
                          'eoie', 'oe', 'eai', 'eue', 'aa', 'oo', 'ee', 'ii', 'aii',
                          'yeu', 'ye', 'you']:
            return [1]
        if chunk_text == "oua":
            return [1, 2]  # "pouah"
        if chunk_text == "ao":
            return [1, 2]  # "paon"
        for x in ['oa', 'ea', 'eua', 'euo', 'ua', 'uo', 'yau']:
            if x in chunk_text:
                return [2]
        # beware of "déesse"
        if chunk_text == 'ée':
            return [1, 2]
        if chunk_text[0] == 'i':
            return [1, 2]
        if chunk_text[0] == 'u' and (strip_accents(chunk_text[1]) in ['i', 'e']):
            return [1, 2]
        if chunk_text[0] == 'o' and chunk_text[1] == 'u' and len(chunk_text) >= 3 and\
                strip_accents(chunk_text[2]) in ['i', 'e']:
            return [1, 2]
        if 'é' in chunk_text or 'è' in chunk_text:
            return [2]
        # we can't tell
        return [1, 2]

    def clear(self):
        if self.word_end is None or not self.word_end:
            return self.text
        return self.text + ' '

    def set_possible_weights_from_context(self, chunks_before, chunks_after, template, threshold):
        if self.weights is not None:
            return
        if len(chunks_after) > 0:
            next_chunk = chunks_after[0]
        else:
            next_chunk = None

        if len(chunks_before) > 0:
            previous_chunk = chunks_before[-1]
        else:
            previous_chunk = None

        if len(chunks_before) > 1:
            previous_previous_chunk = chunks_before[-2]
        else:
            previous_previous_chunk = None

        if ((len(chunks_after) <= 1 and self.is_e())
                and not (next_chunk is not None and next_chunk.is_vowels())
                and not (previous_chunk is None or previous_chunk.contains_break())
                and not (previous_previous_chunk is None or previous_previous_chunk.contains_break())):
            # special case for verse endings, which can get elided (or not)
            # but we don't elide lone syllables ("prends-le", etc.)

            if next_chunk is None:
                self.weights = [0]  # ending 'e' is elided
            elif next_chunk.text == 's':
                self.weights = [0]  # ending 'es' is elided
            elif next_chunk.text == 'nt':
                # ending 'ent' is sometimes elided, try to use pronunciation
                # actually, this will have an influence on the rhyme's gender
                # see feminine
                possible = []
                if not self.verse.phon or len(self.verse.phon) == 0:
                    self.weights = [0, 1]  # do something reasonable without pron
                else:
                    for possible_phon in self.verse.phon:
                        if possible_phon.endswith(')') or possible_phon.endswith('#'):
                            possible.append(1)
                        else:
                            possible.append(0)
                    self.weights = possible
            else:
                self.weights = self.possible_weights(chunks_before, chunks_after, template, threshold)
        elif (next_chunk is None and self.text == 'e' and
                previous_chunk is not None and (previous_chunk.text.endswith('-c')
                                                or previous_chunk.text.endswith('-j')
                                                or (previous_chunk.text == 'c'
                                                    and previous_chunk.had_hyphen is not None)
                                                or (previous_chunk.text == 'j'
                                                    and previous_chunk.had_hyphen is not None))):
            self.weights = [0]  # -ce and -je are elided
        elif next_chunk is None and self.text in ['ie', 'ée']:
            self.weights = [1]
        # elide "-ée" and "-ées", but be specific (beware of e.g. "réel")
        elif (len(chunks_after) <= 1
                and self.text == 'ée'
                and (next_chunk is None or chunks_after[-1].text == 's')):
            self.weights = [1]
        elif self.elidable is not None:
            self.weights = [int(not x) for x in self.elidable]
        else:
            self.weights = self.possible_weights(chunks_before, chunks_after, template, threshold)

    def possible_weights(self, chunks_before, chunks_after, template, threshold):
        if template.options['diaeresis'] == "classical":
            return self.possible_weights_ctx(chunks_before, chunks_after, threshold=threshold)
        elif template.options['diaeresis'] == "permissive":
            return self.possible_weights_approx()

    def possible_weights_ctx(self, chunks_before, chunks_after, threshold=None):
        if not threshold:
            threshold = DEFAULT_THRESHOLD
        q = self.make_query(chunks_before, chunks_after)
        v = diaeresis.diaeresis_finder.lookup(q)
        if len(v.keys()) == 1 and v[list(v.keys())[0]] > threshold:
            return [int(list(v.keys())[0])]
        else:
            return self.possible_weights_seed()

    def make_query(self, chunks_before, chunks_after):
        cleaned_before = [chunk.clear() for chunk in chunks_before]
        cleaned_after = [chunk.clear() for chunk in chunks_after]
        current_clear = self.clear()
        if current_clear.endswith(' '):
            current_clear = current_clear.rstrip()
            if len(cleaned_after) > 0:
                cleaned_after[0] = " " + cleaned_after[0]
            else:
                cleaned_after.append(' ')
        ret2 = intersperse(
            ''.join(cleaned_after),
            ''.join([x[::-1] for x in cleaned_before[::-1]]))
        ret = [current_clear] + ret2
        return ret

    def possible_weights_seed(self):
        """Return the possible number of syllabes taken by a vowel chunk"""
        if len(self.text) == 1:
            return [1]
        # dioïde, maoïste, taoïste
        if (self.text[-1] == 'ï' and len(self.text) >= 3 and not
                self.text[-3:-1] == 'ou'):
            return [3]
        # ostéoarthrite
        if "éoa" in self.text:
            return [3]
        # antiaérien; but let's play it safe
        if "iaé" in self.text:
            return [2, 3]
        # giaour, miaou, niaouli
        if "iaou" in self.text:
            return [2, 3]
        # bioélectrique
        if "ioé" in self.text:
            return [2, 3]
        # méiose, nucléion, etc.
        if "éio" in self.text:
            return [2, 3]
        # radioactif, radioamateur, etc.
        if "ioa" in self.text:
            return [2, 3]
        # pléiade
        if "éio" in self.text:
            return [2, 3]
        # pompéien, tarpéien...
        # in theory the "-ie" should give a diaeresis, so 3 syllabes
        # let's keep the benefit of the doubt...
        # => this also gives 3 as a possibility for "obéie"...
        if "éie" in self.text:
            return [2, 3]
        # tolstoïen
        # same remark
        if "oïe" in self.text:
            return [2, 3]
        # shanghaïen (diaeresis?), but also "aië"
        if "aïe" in self.text:
            return [1, 2, 3]
        if self.text in ['ai', 'ou', 'eu', 'ei', 'eau', 'au', 'oi']:
            return [1]
        # we can't tell
        return [1, 2]

    def set_hemistiche_from_context(self, previous_previous_chunk, previous_chunk, next_chunk):
        if self.hemistiche is not None:
            return
        ending = self.text
        if not (self.word_end or False) and next_chunk is not None:
            if not (next_chunk.word_end or False):
                self.hemistiche = "cut"
                return
            ending += next_chunk.text
        if ending in SURE_END_FEM and previous_previous_chunk is not None and previous_chunk is not None:
            # check that this isn't a one-syllabe wourd (which is allowed)
            ok = False
            try:
                if '-' in previous_chunk.original or (previous_chunk.word_end or False):
                    ok = True
                if '-' in previous_previous_chunk.original or (previous_previous_chunk.word_end or False):
                    ok = True
            except IndexError:
                pass
            if not ok:
                # hemistiche ends in feminine
                if any(self.elidable or [False]):
                    self.hemistiche = "elid"  # elidable final -e, but only OK if actually elided
                    return
                else:
                    self.hemistiche = "fem"
                    return
        self.hemistiche = "ok"

    def normalize(self):
        if self.text_pron is None:
            return normalize(self.original, strip=False, rm_apostrophe_end=False)
        else:
            return self.text

    def get_original_text(self):
        return self.original

    def get_errors_set(self, forbidden_ok, hiatus_ok):
        errors_chunk = set()
        if self.error is not None:
            if self.error == "ambiguous" and not forbidden_ok:
                errors_chunk.add(error.ErrorForbiddenPattern)
            if self.error == "hiatus" and not hiatus_ok:
                errors_chunk.add(error.ErrorHiatus)
            if self.error == "illegal":
                errors_chunk.add(error.ErrorBadCharacters)
        return errors_chunk

    def is_masculine(self):
        return (self.had_hyphen or False) or (self.word_end or False)

    def render(self, key):
        if key == 'error' and self.error == 'illegal':
            return self.illegal_str
        if key == 'original':
            return str(self.original)
        elif key == 'weights':
            return '-'.join([str(a) for a in self.weights or []])
        elif key == 'error':
            return ErrorCollection.keys.get(self.error, '') * len(self.original)
        elif key == 'hemis':
            return str(self.hemistiche or "")
        else:
            print(key, file=sys.stderr)
            assert False

    def get_normalized_rendering(self, key, keys):
        return ('{:^' + str(self.get_max_render_size(keys)) + '}').format(self.render(key))

    def get_min_weight(self):
        return min(self.weights or [0])

    def get_max_weight(self):
        return max(self.weights or [0])

    def get_max_render_size(self, keys):
        return max(len(self.render(key)) for key in keys)

    def print_query(self, chunks_after, chunks_before, output_file):
        if (self.weights is not None and len(self.weights) > 1
                and self.weight is not None and self.weight > 0):
            print(str(self.weight) + ' ' +
                  ' '.join(self.make_query(chunks_before, chunks_after)), file=output_file)


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
