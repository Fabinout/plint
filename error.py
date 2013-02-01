import common

class Error:
  def __init__(self):
    self.line = None
    self.line_no = None
    self.pattern = None
    self.prefix = None

  def pos(self, line, line_no, pattern):
    self.line = line
    self.line_no = line_no
    self.pattern = pattern
    self.prefix = "stdin:%d: " % self.line_no

  def say(self, l):
    return self.prefix + l

  def report(self, s, short=False, t = [], ):
    l = []
    if short:
      l.append(s)
    else:
      l.append(self.say(_("error: %s") % (s)))
    msg = _("Line is: %s") % (self.line)
    if short:
      if t != []:
        if self.line.strip() != "":
          l.append(msg)
        for x in t:
          l.append(x)
    else:
      if self.line.strip() != "":
        l.append(self.say(msg))
      for x in t:
        l.append(self.say(x))
    return '\n'.join(l)

class ErrorBadCharacters(Error):
  def __init__(self, characters):
    self.characters = characters

  def report(self, short=False):
    return Error.report(self, _("Illegal character%s: %s")
        % ('' if len(self.characters) == 1 else 's',
          ', '.join(["'" + a + "'" for a in self.characters])), short)

class ErrorForbiddenPattern(Error):
  def __init__(self, forbidden):
    self.forbidden = forbidden

  def report(self, short=False):
    return Error.report(self, _("Illegal ambiguous pattern: %s") % self.forbidden,
        short)

class ErrorHiatus(Error):
  def __init__(self, hiatus):
    self.hiatus = hiatus

  def report(self, short=False):
    return Error.report(self, _("Illegal hiatus: %s") % self.hiatus, short)

class ErrorBadRhyme(Error):
  def __init__(self, expected, inferred):
    Error.__init__(self)
    self.expected = expected
    self.inferred = inferred

  def report(self, short=False):
    # TODO indicate eye rhyme since this is also important
    # TODO don't indicate more than the minimal required rhyme (in length and
    # present of a vowel phoneme)
    return Error.report(self,
        _("%s for type %s (expected %s, inferred \"%s\")")
        % (self.kind, self.get_id(), self.fmt(self.expected),
          self.fmt(self.inferred)), short)

class ErrorBadRhymeGenre(ErrorBadRhyme):
  def fmt(self, l):
    result = _(' or ').join(list(l))
    if result == '':
      result = "?"
    return result

  def get_id(self):
    return self.pattern.femid

  @property
  def kind(self):
    return _("Bad rhyme genre")

class ErrorBadRhymeSound(ErrorBadRhyme):
  def fmt(self, l):
    pron = l.phon
    ok = []
    if len(pron) > 0:
      ok.append("")
    return ("\"" + '/'.join(list(set([common.to_xsampa(x[-4:]) for x in pron])))
        + "\"" + _(" (ending: \"") + l.eye + "\")")

  def get_id(self):
    return self.pattern.myid

  def report(self, short=False):
    return Error.report(self, _("%s for type %s (expected %s)")
        % (self.kind, self.pattern.myid, self.fmt(self.expected)), short)

  @property
  def kind(self):
    return _("Bad rhyme")

class ErrorBadVerse(Error):
  def __init__(self, verse):
    Error.__init__(self)
    self.verse = verse

  def align(self):
    chunks = self.verse.chunks
    keys = ['original', 'text', 'weights', 'error', 'hemis']
    lines = {}
    for key in keys:
      lines[key] = ""
    for chunk in chunks:
      l = max(len(str(chunk.get(key, ""))) for key in keys)
      for key in keys:
        lines[key] += ' ' + ('{:^'+str(l)+'}').format(chunk.get(key, ""))
    return [lines[key] for key in keys if len(lines[key].strip()) > 0]

  def report(self, short=False):
    return Error.report(
        self,
        _("Bad verse:"),
        short,
        self.align()
        )

class ErrorBadMetric(ErrorBadVerse):
  def __init__(self, possible):
    Error.__init__(self)
    self.possible = possible

  def report(self, short=False):
    num = min(len(self.possible), 4)
    truncated = num < len(self.possible)
    return Error.report(
        self,
        (_("Bad metric (expected %s, inferred %d illegal option%s)") %
        (self.pattern.metric,
          len(self.possible), ('s' if len(self.possible) != 1 else
          ''))),
        short,
        sum(map(self.align, self.possible[:num]), [])
        + ([_("... worse options omitted ...")] if truncated else [])
        )

class ErrorMultipleWordOccurrence(Error):
  def __init__(self, word, occurrences):
    self.word = word
    self.occurrences = occurrences

  def get_id(self):
    return self.pattern.myid

  def report(self, short=False):
    return Error.report(self, _("Too many occurrences of word %s for rhyme %s")
        % (self.word, self.get_id()), short)

class ErrorIncompleteTemplate(Error):
  def report(self, short=False):
    return Error.report(self, _("Poem is not complete"),
        short)

class ErrorOverflowedTemplate(Error):
  def report(self, short=False):
    return Error.report(self, _("Verse is beyond end of poem"),
        short)

class TemplateLoadError(BaseException):
  def __init__(self, msg):
    self.msg = msg

