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

    def say(self, l, short):
        return l if short else self.prefix + l

    def align(self):
        return self.verse.align()

    def lines(self, short=False):
        result = []
        if self.verse.possible is not None:
            result.append([self.say(x, short) for x in self.align()])
        for e in self.errors:
            result.append([self.say(e.report(self.pattern), short)])
        return result

    def report(self, short=False):
        return '\n'.join(sum(self.lines(short), []))


class ErrorBadElement(ReportableError):

    def __init__(self):
        self.message = None
        self.key = None

    def report(self, pattern):
        return (self.message
                + " (see '%s' above)") % ErrorCollection.keys[self.key]


class ErrorBadCharacters(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = "Illegal Characters"
        self.key = "illegal"


class ErrorForbiddenPattern(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = "Illegal ambiguous pattern"
        self.key = "ambiguous"


class ErrorHiatus(ErrorBadElement):

    def __init__(self):
        super().__init__()
        self.message = "Illegal hiatus"
        self.key = "hiatus"


class ErrorBadRhyme(ReportableError):

    def __init__(self, expected, inferred, old_phon=None):
        self.expected = expected
        self.inferred = inferred
        self.old_phon = old_phon
        self.kind = None

    def get_id(self, pattern):
        raise NotImplementedError

    def fmt(self, l):
        raise NotImplementedError

    def report(self, pattern):
        return ("%s for type %s (expected %s, inferred %s)"
                % (self.kind, self.get_id(pattern), self.fmt(self.expected),
                   self.fmt(self.inferred)))


class ErrorBadRhymeGenre(ErrorBadRhyme):

    def __init__(self, expected, inferred, old_phon=None):
        super().__init__(expected, inferred, old_phon)
        self.kind = "Bad rhyme genre"

    def fmt(self, l):
        result = ' or '.join(sorted(list(l)))
        if result == '':
            result = "?"
        return "\"" + result + "\""

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
        self.kind = "Bad rhyme sound"

    def fmt(self, l):
        return '/'.join("\"" + common.to_xsampa(x) + "\"" for x in
                        sorted(list(l.sufficient_phon())))


class ErrorBadRhymeEye(ErrorBadRhymeObject):

    def __init__(self, expected, inferred, old_phon=None):
        super().__init__(expected, inferred, old_phon)
        self.kind = "Bad rhyme ending"

    def fmt(self, l):
        return "\"-" + l.sufficient_eye(self.old_phon) + "\""


class ErrorBadMetric(ReportableError):

    def report(self, pattern):
        plural_hemistiche = '' if len(pattern.hemistiches) == 1 else 's'
        plural_syllable = '' if pattern.length == 1 else 's'
        if len(pattern.hemistiches) == 0:
            hemistiche_string = ""
        else:
            hemistiche_positions = ','.join(str(a) for a in pattern.hemistiches)
            hemistiche_string = (" with hemistiche%s at " % plural_hemistiche) + hemistiche_positions
        return ("Illegal metric: expected %d syllable%s%s" %
                (pattern.length, plural_syllable, hemistiche_string))


class ErrorMultipleWordOccurrence(ReportableError):

    def __init__(self, word, occurrences):
        self.word = word
        self.occurrences = occurrences

    def report(self, pattern):
        return "Too many occurrences of word \"%s\" for rhyme %s" % (self.word, pattern.my_id)


class ErrorIncompleteTemplate(ReportableError):

    def report(self, pattern):
        return "Poem is not complete"


class ErrorOverflowedTemplate(ReportableError):

    def report(self, pattern):
        return "Verse is beyond end of poem"


class TemplateLoadError(BaseException):

    def __init__(self, msg):
        self.msg = msg
