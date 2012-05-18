import common
import hemistiches

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

  def report(self, s, short=False, t = []):
    l = []
    if short:
      l.append(s)
    else:
      l.append(self.say("error: %s" % (s)))
    if short:
      if t != []:
        l.append("Line is: %s" % (self.line))
        for x in t:
          l.append(x)
    else:
      l.append(self.say("Line is: %s" % (self.line)))
      for x in t:
        l.append(self.say(x))
    return '\n'.join(l)

class ErrorBadCharacters(Error):
  def __init__(self, characters):
    self.characters = characters

  def report(self):
    return Error.report(self, "Illegal character: %s"
        % ', '.join(["'" + a + "'" for a in self.characters]))

class ErrorForbiddenPattern(Error):
  def __init__(self):
    # TODO give more info
    pass

  def report(self):
    return Error.report(self, "Illegal ambiguous pattern")

class ErrorBadRhyme(Error):
  def __init__(self, expected, inferred):
    Error.__init__(self)
    self.expected = expected
    self.inferred = inferred

  def report(self, short=False):
    # TODO indicate eye rhyme since this is also important
    # TODO don't indicate more than the minimal required rhyme (in length and
    # present of a vowel phoneme)
    return Error.report(self, "Bad rhyme %s for type %s (expected %s, inferred %s)"
        % (self.kind, self.get_id(), self.fmt(self.expected),
          self.fmt(self.inferred)), short)

class ErrorBadRhymeGenre(ErrorBadRhyme):
  def fmt(self, l):
    result = ' or '.join(list(l))
    if result == '':
      result = "?"
    return result

  def get_id(self):
    return self.pattern.femid

  @property
  def kind(self):
    return "genre"

class ErrorBadRhymeSound(ErrorBadRhyme):
  def fmt(self, l):
    #TODO handle other types
    pron = l.phon
    ok = []
    if len(pron) > 0:
      ok.append("")
    return '/'.join(list(set([common.to_xsampa(x[-4:]) for x in pron])))

  def get_id(self):
    return self.pattern.myid

  def report(self, short=False):
    return Error.report(self, "Bad rhyme %s for type %s (expected %s)"
        % (self.kind, self.pattern.myid, self.fmt(self.expected)), short)

  @property
  def kind(self):
    return "value"

class ErrorBadMetric(Error):
  def __init__(self, possible):
    Error.__init__(self)
    self.possible = possible

  def restore_elid(self, chunk):
    if isinstance(chunk, tuple):
      return [chunk]
    try:
      if chunk[-1] != "`":
        return [chunk]
    except KeyError:
      return [chunk]
    return [chunk[:-1], ("e", 0)]

  def align(self, align):
    score, align = align
    align, feminine, hemis = align
    align = sum([self.restore_elid(chunk) for chunk in align], [])
    line = self.line
    l2 = []
    count = 0
    ccount = 0
    last_he = 0
    summary = []
    offset = 0
    done = False
    for x in align:
      if isinstance(x, tuple):
        orig = ""
        while len(line) > 0 and common.is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        add = ('{:^'+str(len(orig))+'}').format(str(x[1]))
        if offset > 0 and len(add) > 0 and add[-1] == ' ':
          offset -= 1
          add = add[:-1]
        l2 += add
        if len(add) > len(orig):
          offset = len(add) - len(orig)
        count += x[1]
        ccount += x[1]
        done = False
      else:
        orig = ""
        while len(line) > 0 and not common.is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        if count in hemis.keys() and not done and last_he < count:
          done = True
          summary.append(str(ccount))
          ccount = 0
          summary.append(hemistiches.hemis_types[hemis[count]])
          l2 += ('{:^'+str(len(orig))+'}'
              ).format(hemistiches.hemis_types[hemis[count]])
          last_he = count
        else:
          l2 += ' ' * len(orig)
    summary.append(str(ccount)+':')
    result = ''.join(l2)
    summary = ('{:^9}').format(''.join(summary))
    return summary + result

  def report(self, short=False):
    num = min(len(self.possible), 4)
    truncated = num < len(self.possible)
    return Error.report(
        self,
        ("Bad metric (expected %s, inferred %d option%s)" %
        (self.pattern.metric,
          len(self.possible), ('s' if len(self.possible) != 1 else
          ''))),
        short,
        list(map(self.align, self.possible[:num]))
        + (["... other options omitted ..."] if truncated else [])
        )

