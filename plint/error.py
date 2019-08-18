from plint import common


class ReportableError:

    def report(self, pattern):
        raise NotImplementedError


class ErrorCollection(ReportableError):
    keys = {'hiatus': 'H', 'ambiguous': 'A', 'illegal': 'I'}

    @property
    def prefix(self):
        return "stdin:%d: " % self.line_no

    def __init__(self, line_no, line, pattern, verse, errors=None):
        self.line_no = line_no
        self.line = line
        self.errors = errors or []
        self.pattern = pattern
        self.verse = verse

    def isEmpty(self):
        return len(self.errors) == 0

    def say(self, l, short):
        return l if short else self.prefix + l

    def align(self, fmt="text"):
        return self.verse.align(fmt=fmt)

    def lines(self, short=False, fmt="text"):
        result = []
        if self.verse.possible is not None:
            result.append([self.say(x, short) for x in self.align(fmt=fmt)])
        for e in self.errors:
            result.append([self.say(e.report(self.pattern, fmt=fmt), short)])
        return result

    def report(self, short=False, fmt="text"):
        if fmt == "text":
            return '\n'.join(sum(self.lines(short, fmt=fmt), []))
        elif fmt == "json":
            return {
                    'line': self.line,
                    'line_no': self.line_no,
                    'possible_parsings': self.align(fmt=fmt),
                    'errors': [
                        e.report(self.pattern, fmt=fmt)
                        for e in self.errors]
                    }
        else:
            raise ValueError("bad format")


class ErrorBadElement(ReportableError):

    def __init__(self):
        self.message = None
        self.key = None
        self.report_key = None

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            return (self.message
                + _(" (see '%s' above)")) % ErrorCollection.keys[self.key]
        elif fmt == "json":
            return {'error': self.report_key,
                    'error_kind': "local_error_collection"}
        else:
            raise ValueError("bad format")


class ErrorBadCharacters(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = _("Illegal characters")
        self.key = "illegal"
        self.report_key = "illegal_characters"


class ErrorForbiddenPattern(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = _("Illegal ambiguous pattern")
        self.key = "ambiguous"
        self.report_key = "ambiguous_patterns"


class ErrorHiatus(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = _("Illegal hiatus")
        self.key = "hiatus"
        self.report_key = "hiatus"


class ErrorBadRhyme(ReportableError):

    def __init__(self, expected, inferred, old_phon=None):
        self.expected = expected
        self.inferred = inferred
        self.old_phon = old_phon
        self.kind_human = None
        self.kind = None

    def get_id(self, pattern):
        raise NotImplementedError

    def fmt(self, l, fmt="text"):
        raise NotImplementedError

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            return (_("%s for type %s (expected %s, inferred %s)")
                % (self.kind_human, self.get_id(pattern),
                    self.fmt(self.expected, fmt=fmt),
                    self.fmt(self.inferred, fmt=fmt)))
        elif fmt == "json":
            return {
                'error': self.kind, 'error_kind': "rhyme_error",
                'pattern_rhyme_type': self.get_id(pattern),
                'expected': self.fmt(self.expected, fmt=fmt),
                'inferred': self.fmt(self.inferred, fmt=fmt)}
        else:
            raise ValueError("bad format")


class ErrorBadRhymeGenre(ErrorBadRhyme):

    def __init__(self, expected, inferred, old_phon=None):
        super().__init__(expected, inferred, old_phon)
        self.kind_human = _("Bad rhyme genre")
        self.kind = "rhyme_genre"

    def fmt(self, l, fmt="text"):
        if fmt == "text":
            result = _(' or ').join(sorted(list(l)))
            if result == '':
                result = "?"
            return "\"" + result + "\""
        elif fmt == "json":
            return sorted(list(l))
        else:
            raise ValueError("bad format")

    def get_id(self, pattern):
        return pattern.feminine_id


class ErrorBadRhymeObject(ErrorBadRhyme):

    def fmt(self, l):
        raise NotImplementedError

    def get_id(self, pattern):
        return pattern.my_id


class ErrorBadRhymeSound(ErrorBadRhymeObject):

    def __init__(self, expected, inferred, old_phon=None):
        super().__init__(expected, inferred, old_phon)
        self.kind_human = _("Bad rhyme sound")
        self.kind = "rhyme_sound"

    def fmt(self, l, fmt="text"):
        if fmt == "text":
            return ('/'.join("\"" + common.to_xsampa(x) + "\"" 
                    for x in sorted(list(l.sufficient_phon()))))
        elif fmt == "json":
            return (sorted(common.to_xsampa(x)
                    for x in list(l.sufficient_phon())))
        else:
            raise ValueError("bad format")


class ErrorBadRhymeEye(ErrorBadRhymeObject):

    def __init__(self, expected, inferred, old_phon=None):
        super().__init__(expected, inferred, old_phon)
        self.kind_human = _("Bad rhyme ending")
        self.kind = "rhyme_ending"

    def fmt(self, l, fmt="text"):
        if fmt == "text":
            return "\"-" + l.sufficient_eye(self.old_phon) + "\""
        elif fmt == "json":
            return (l.sufficient_eye(self.old_phon))
        else:
            raise ValueError("bad format")


class ErrorBadMetric(ReportableError):

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            plural_hemistiche = '' if len(pattern.hemistiches) == 1 else 's'
            plural_syllable = '' if pattern.length == 1 else 's'
            if len(pattern.hemistiches) == 0:
                hemistiche_string = ""
            else:
                hemistiche_positions = (','.join(str(a)
                            for a in pattern.hemistiches))
                hemistiche_string = ((_(" with hemistiche%s at ")
                            % plural_hemistiche) + hemistiche_positions)
            return (_("Illegal metric: expected %d syllable%s%s") %
                    (pattern.length, plural_syllable, hemistiche_string))
        elif fmt == "json":
            return {
                    'error': "metric", 'error_kind': "metric_error",
                    'expected_syllables': pattern.length,
                    'expected_hemistiches': pattern.hemistiches
                    }
        else:
            raise ValueError("bad format")


class ErrorMultipleWordOccurrence(ReportableError):

    def __init__(self, word, occurrences):
        self.word = word
        self.occurrences = occurrences

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            return (_("Too many occurrences of word \"%s\" for rhyme %s")
                    % (self.word, pattern.my_id))
        elif fmt == "json":
            return {
                'error': "rhyme_occurrences", 'error_kind': "rhyme_error",
                'pattern_rhyme_type': pattern.my_id,
                'word': self.word
                }
        else:
            raise ValueError("bad format")


class ErrorIncompleteTemplate(ReportableError):

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            return _("Poem is not complete")
        elif fmt == "json":
            return {
                'error': "incomplete_poem",
                'error_kind': "global_error"
                }
        else:
            raise ValueError("bad format")



class ErrorOverflowedTemplate(ReportableError):

    def report(self, pattern, fmt="text"):
        if fmt == "text":
            return _("Verse is beyond end of poem")
        elif fmt == "json":
            return {
                'error': "verse_beyond_end_of_poem",
                'error_kind': "global_error"
                }
        else:
            raise ValueError("bad format")


class TemplateLoadError(BaseException):

    def __init__(self, msg):
        self.msg = msg
