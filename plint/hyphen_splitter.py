import re

from plint.common import is_consonants, normalize

HYPHEN_REGEX = re.compile("(-+)")


class HyphenSplitter:

    def __init__(self):
        self._missed = ""
        self.tokens = []
        self.just_append = False
        self.initialize()

    def initialize(self):
        self._missed = ""
        self.tokens = []
        self.just_append = False

    def split(self, word):
        """split hyphen-delimited word parts into separate words if they are only
              consonants, so that the sigle code later can deal with them (e.g. "k-way")
              annotates parts with boolean indicating if there is a word end afterward"""
        self.initialize()
        self.complete_tokens(word)
        self.process_remaining_missed()
        return self.get_tokens_with_last_word_indication()

    def complete_tokens(self, word):
        word_split_by_hyphen = re.split(HYPHEN_REGEX, word)
        for i, sub_word in enumerate(word_split_by_hyphen):
            self.add_subword_to_tokens(sub_word)

    def add_subword_to_tokens(self, sub_word):
        if self.just_append:
            self.append_to_last_token(sub_word)
        elif self.is_separator(sub_word):
            self.process_separator(sub_word)
        elif is_consonants(normalize(sub_word)):
            self.append_with_miss(sub_word)
        else:
            self.append_with_miss(sub_word)
            self.just_append = True

    def get_tokens_with_last_word_indication(self):
        return list(zip([False] * (len(self.tokens) - 1) + [True], self.tokens))

    def append_with_miss(self, sub_word):
        self.tokens.append(self._missed + sub_word)
        self._missed = ""

    def process_remaining_missed(self):
        if self._missed:
            if self.tokens:
                self.append_to_last_token(self._missed)
            else:
                self.tokens = [self._missed]

    @staticmethod
    def get_token(before_word_end, word):
        return before_word_end, word

    def process_separator(self, sub_word):
        if self.tokens:
            self.append_to_last_token(sub_word)
        else:
            self._missed += sub_word

    def append_to_last_token(self, sub_word):
        self.tokens[-1] = self.tokens[-1] + sub_word

    @staticmethod
    def is_separator(word):
        return re.match(r"^-*$", word) or re.match(r"^ *$", word)
