import copy
import re

from plint import error, rhyme
from plint.common import normalize
from plint.nature import nature_count
from plint.options import default_options
from plint.pattern import Pattern
from plint.verse import Verse


OPTION_ALIASES = {
        'fusionner': 'merge',
        'ambiguous_ok': 'forbidden_ok',
        'ambigu_ok': 'forbidden_ok',
        'dierese': 'diaeresis',
        'verifie_occurrences': 'check_occurrences',
        'repetition_ok': 'repeat_ok',
        'incomplet_ok': 'incomplete_ok',
        'phon_supposee_ok': 'phon_supposed_ok',
        'oeil_supposee_ok': 'eye_supposed_ok',
        'oeil_tolerance_ok': 'eye_tolerance_ok',
        'pauvre_oeil_requise': 'poor_eye_required',
        'pauvre_oeil_supposee_ok': 'poor_eye_supposed_ok',
        'pauvre_oeil_vocalique_ok': 'poor_eye_vocalic_ok',
    }


def reset_conditional(d):
    return dict((k, v) for k, v in d.items() if len(k) > 0 and k[0] == '!')


class Template:

    def __init__(self, template_string=None):
        self.template = []
        self.pattern_line_no = 0
        self.options = dict(default_options)
        self.mergers = []
        self.old_position = None
        self.old_env = None
        self.old_femenv = None
        self.old_occenv = None
        self.overflowed = False
        if template_string is not None:
            self.load(template_string)
        self.line_no = 0
        self.position = 0
        self.prev = None
        self.env = {}
        self.feminine_environment = {}
        self.occurrence_environment = {}
        self.reject_errors = False

    def load(self, template_string):
        """Load from a string"""
        for line in template_string.split('\n'):
            line = line.strip()
            self.pattern_line_no += 1
            if len(line) != 0 and line[0] != '#':
                if line[0] == '!':
                    # don't count the '!' in the options, that's why we use [1:]
                    for option_string in line.split()[1:]:
                        self.read_option(option_string)
                else:
                    self.template.append(self.parse_line(line.strip()))
        if len(self.template) == 0:
            raise error.TemplateLoadError("Template is empty")

    def read_option(self, option_string):
        try:
            key, value = option_string.split(':')
        except ValueError:
            raise error.TemplateLoadError("Global options must be provided as key-value pairs")
        if key in OPTION_ALIASES:
            key = OPTION_ALIASES[key]
        if key == 'merge':
            self.mergers.append(value)
        elif key == 'diaeresis':
            if value == "classique":
                value = "classical"
            if value not in ["permissive", "classical"]:
                raise error.TemplateLoadError("Bad value for global option %s" % key)
            self.options['diaeresis'] = value
        elif key in self.options:
            self.options[key] = str2bool(value)
        else:
            raise error.TemplateLoadError("Unknown global option")

    def parse_line(self, line):
        """Parse template line from a line"""
        split = line.split(' ')
        metric = split[0]
        if len(split) >= 2:
            my_id = split[1]
        else:
            my_id = str(self.pattern_line_no)  # unique
        if len(split) >= 3:
            feminine_id = split[2]
        else:
            feminine_id = str(self.pattern_line_no)  # unique
        id_split = my_id.split(':')
        classical = True
        n_common_suffix_phones = 1
        if len(id_split) >= 2:
            constraint = id_split[-1].split('|')
            if len(constraint) > 0:
                classical = False if constraint[0] in ["no", "non"] else constraint[0]
            if len(constraint) > 1:
                n_common_suffix_phones = int(constraint[1])
        else:
            constraint = []
        if len(constraint) == 0:
            n_common_suffix_phones = 1
        if len(constraint) < 2:
            classical = True
        return Pattern(metric, my_id, feminine_id, rhyme.Constraint(classical, n_common_suffix_phones))

    def match(self, line, output_file=None, last=False, n_syllables=None, offset=0):
        """Check a line against current pattern, return errors"""

        was_incomplete = last and not self.beyond

        errors = []
        pattern = self.get()

        line_with_case = normalize(line, downcase=False)

        verse = Verse(line, self, pattern)

        if n_syllables:
            verse.print_n_syllables(n_syllables, offset, output_file)
            return errors, pattern, verse

        if last:
            if was_incomplete and not self.options['incomplete_ok'] and not self.overflowed:
                return [error.ErrorIncompleteTemplate()], pattern, verse
            return [], pattern, verse

        if self.overflowed:
            return [error.ErrorOverflowedTemplate()], pattern, verse

        rhyme_failed = False
        # rhymes
        if pattern.my_id not in self.env:
            # initialize the rhyme
            # last_count is passed later
            self.env[pattern.my_id] = rhyme.Rhyme(verse.normalized, pattern.constraint, self.mergers, self.options)
        else:
            # update the rhyme
            self.env[pattern.my_id].feed(verse.normalized, pattern.constraint)
            if not self.env[pattern.my_id].satisfied_phon():
                # no more possible rhymes, something went wrong, check phon
                self.env[pattern.my_id].rollback()
                rhyme_failed = True
                errors.append(error.ErrorBadRhymeSound(self.env[pattern.my_id],
                                                       self.env[pattern.my_id].new_rhyme))

        # occurrences
        if self.options['check_occurrences']:
            if pattern.my_id not in self.occurrence_environment.keys():
                self.occurrence_environment[pattern.my_id] = {}
            last_word = re.split(r'[- ]', line_with_case)[-1]
            if last_word not in self.occurrence_environment[pattern.my_id].keys():
                self.occurrence_environment[pattern.my_id][last_word] = 0
            self.occurrence_environment[pattern.my_id][last_word] += 1
            if self.occurrence_environment[pattern.my_id][last_word] > nature_count(last_word):
                errors.insert(0,
                              error.ErrorMultipleWordOccurrence(last_word,
                                                                self.occurrence_environment[pattern.my_id][last_word]))

        verse.phon = self.env[pattern.my_id].phon
        verse.parse()

        # now that we have parsed, adjust rhyme to reflect last word length
        # and check eye
        if not rhyme_failed:
            self.env[pattern.my_id].adjust_last_count(verse.get_last_count())
            if not self.env[pattern.my_id].satisfied_eye():
                old_phon = len(self.env[pattern.my_id].phon)
                self.env[pattern.my_id].rollback()
                errors.append(error.ErrorBadRhymeEye(self.env[pattern.my_id],
                                                     self.env[pattern.my_id].new_rhyme, old_phon))

        errors = verse.problems() + errors

        verse.print_possible(output_file)

        # rhyme genres
        # inequality constraint
        # TODO this is simplistic and order-dependent
        if pattern.feminine_id.swapcase() in self.feminine_environment.keys():
            new = {'M', 'F'} - self.feminine_environment[pattern.feminine_id.swapcase()]
            if len(new) > 0:
                self.feminine_environment[pattern.feminine_id] = new
        if pattern.feminine_id not in self.feminine_environment.keys():
            if pattern.feminine_id == 'M':
                x = {'M'}
            elif pattern.feminine_id == 'F':
                x = {'F'}
            else:
                x = {'M', 'F'}
            self.feminine_environment[pattern.feminine_id] = x
        old = list(self.feminine_environment[pattern.feminine_id])
        new = verse.genders()
        self.feminine_environment[pattern.feminine_id] &= set(new)
        if len(self.feminine_environment[pattern.feminine_id]) == 0:
            errors.append(error.ErrorBadRhymeGenre(old, new))

        return errors, pattern, verse

    def reset_state(self):
        """Reset our state, except ids starting with '!'"""
        self.position = 0
        self.env = reset_conditional(self.env)
        self.feminine_environment = reset_conditional(self.feminine_environment)
        self.occurrence_environment = {}  # always reset

    @property
    def beyond(self):
        return self.position >= len(self.template)

    def get(self):
        """Get next state, resetting if needed"""
        self.old_position = self.position
        self.old_env = copy.deepcopy(self.env)
        self.old_femenv = copy.deepcopy(self.feminine_environment)
        self.old_occenv = copy.deepcopy(self.occurrence_environment)
        if self.beyond:
            if not self.options['repeat_ok']:
                self.overflowed = True
            self.reset_state()
        result = self.template[self.position]
        self.position += 1
        return result

    def back(self):
        """Revert to previous state"""
        self.position = self.old_position
        self.env = copy.deepcopy(self.old_env)
        self.feminine_environment = copy.deepcopy(self.old_femenv)
        self.occurrence_environment = copy.deepcopy(self.old_occenv)

    def check(self, line, output_file=None, last=False, n_syllables=None, offset=0):
        """Check line (wrapper)"""
        self.line_no += 1
        line = line.rstrip()
        if normalize(line) == '' and not last:
            return None

        errors, pattern, verse = self.match(line, output_file, last=last, n_syllables=n_syllables, offset=offset)
        if len(errors) > 0:
            if self.reject_errors:
                self.back()
                self.line_no -= 1
            return error.ErrorCollection(self.line_no, line, pattern, verse, errors)
        return None


def str2bool(x):
    if x.lower() in ["yes", "oui", "y", "o", "true", "t", "vrai", "v"]:
        return True
    if x.lower() in ["no", "non", "n", "false", "faux", "f"]:
        return False
    raise error.TemplateLoadError("Bad value in global option")
