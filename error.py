import common


class ErrorCollection:
  keys = {'hiatus': 'H', 'ambiguous': 'A', 'illegal': 'I'}

  @property
  def prefix(self):
    return "stdin:%d: " % self.line_no

  def __init__(self, line_no, line, pattern, verse, errors=[]):
    self.line_no = line_no
    self.line = line
    self.errors = errors
    self.pattern = pattern
    self.verse = verse

  def say(self, l, short):
    return l if short else self.prefix + l

  def align(self):
    chunks = self.verse.chunks
    keys = ['original', 'error']
    if len(self.verse.possible) == 0:
      keys.append('weights')
      if len(self.pattern.hemistiches) > 0:
        keys.append('hemis')
    formatters = {'weights': lambda x, y: '-'.join([str(a) for a in x]),
        'error': lambda x, y: ErrorCollection.keys.get(x, '') *
        len(chunk['original'])}
    def render(chunk, key):
      return (formatters.get(key, lambda x, y: str(x)))(chunk.get(key, ""), chunk)
    lines = {}
    for key in keys:
      lines[key] = ""
    for chunk in chunks:
      l = max(len(render(chunk, key)) for key in keys)
      for key in keys:
        lines[key] += ('{:^'+str(l)+'}').format(render(chunk, key))
    return ["> " + lines[key] for key in keys if len(lines[key].strip()) > 0]

  def lines(self, short=False):
    l = []
    l.append([self.say(x, short) for x in self.align()])
    for e in self.errors:
      l.append([self.say(e.report(self.pattern), short)])
    return l

  def report(self, short=False):
    return '\n'.join(sum(self.lines(short), []))

class ErrorBadElement:
  def report(self, pattern):
    return (self.message
        + _(" (see '%s' above)") % ErrorCollection.keys[self.key])

class ErrorBadCharacters(ErrorBadElement):
  @property
  def message(self):
    return _("Illegal characters")
  key = "illegal"

class ErrorForbiddenPattern(ErrorBadElement):
  @property
  def message(self):
    return _("Illegal ambiguous pattern")
  key = "ambiguous"

class ErrorHiatus(ErrorBadElement):
  @property
  def message(self):
    return _("Illegal hiatus")
  key = "hiatus"

class ErrorBadRhyme:
  def __init__(self, expected, inferred):
    self.expected = expected
    self.inferred = inferred

  def report(self, pattern):
    # TODO indicate eye rhyme since this is also important
    # TODO don't indicate more than the minimal required rhyme (in length and
    # present of a vowel phoneme)
    return (_("%s for type %s (expected \"%s\", inferred \"%s\")")
        % (self.kind, self.get_id(pattern), self.fmt(self.expected),
          self.fmt(self.inferred)))

class ErrorBadRhymeGenre(ErrorBadRhyme):
  @property
  def kind(self):
    return _("Bad rhyme genre")

  def fmt(self, l):
    result = _(' or ').join(list(l))
    if result == '':
      result = "?"
    return result

  def get_id(self, pattern):
    return pattern.femid

class ErrorBadRhymeSound(ErrorBadRhyme):
  @property
  def kind(self):
    return _("Bad rhyme")

  def fmt(self, l):
    pron = l.phon
    ok = []
    if len(pron) > 0:
      ok.append("")
    return ("\"" + '/'.join(list(set([common.to_xsampa(x[-4:]) for x in pron])))
        + "\"" + _(", ending: \"") + l.eye + "\"")

  def get_id(self, pattern):
    return pattern.myid

  def report(self, pattern):
    return (_("%s for type %s (expected %s)")
        % (self.kind, pattern.myid, self.fmt(self.expected)))

class ErrorBadMetric:
  def report(self, pattern):
    return (_("Illegal metric: expected %d syllable%s%s") %
        (pattern.length, '' if pattern.length == 1 else 's',
          '' if len(pattern.hemistiches) == 0
            else (_(" with hemistiche%s at ") %
            '' if len(pattern.hemistiches) == 1 else 's')
            + ','.join(str(a) for a in pattern.hemistiches)))

class ErrorMultipleWordOccurrence:
  def __init__(self, word, occurrences):
    self.word = word
    self.occurrences = occurrences

  def get_id(self):
    return self.pattern.myid

  def report(self, pattern):
    return (_("Too many occurrences of word %s for rhyme %s")
        % (self.word, self.get_id()))

class ErrorIncompleteTemplate:
  def report(self, pattern):
    return _("Poem is not complete")

class ErrorOverflowedTemplate:
  def report(self, pattern):
    return _("Verse is beyond end of poem")

class TemplateLoadError(BaseException):
  def __init__(self, msg):
    self.msg = msg

