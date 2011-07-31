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

  def report(self, s, t = []):
    l = []
    l.append(self.say("error: %s" % (s)))
    l.append(self.say("Line is: %s" % (self.line)))
    for x in t:
      l.append(self.say(x))
    return '\n'.join(l)
    
class ErrorBadRhyme(Error):
  def __init__(self, expected, inferred):
    Error.__init__(self)
    self.expected = expected
    self.inferred = inferred

  def report(self):
    return Error.report(self, "Bad rhyme %s for type %s (expected %s, inferred %s)"
        % (self.kind, self.get_id(), self.fmt(self.expected),
          self.fmt(self.inferred)))

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
    pron, spel, constraint = l
    ok = []
    if len(pron) > 0:
      ok.append("")
    return '/'.join(list(pron))

  def get_id(self):
    return self.pattern.myid

  def report(self):
    return Error.report(self, "Bad rhyme %s for type %s (expected %s)"
        % (self.kind, self.pattern.myid, self.fmt(self.expected)))

  @property
  def kind(self):
    return "value"

class ErrorBadMetric(Error):
  def __init__(self, possible):
    Error.__init__(self)
    self.possible = possible

  def align(self, align):
    score, align = align
    align, feminine, hemis = align
    line = self.line
    l2 = []
    count = 0
    ccount = 0
    summary = []
    done = False
    for x in [''] + align:
      if isinstance(x, tuple):
        orig = ""
        while len(line) > 0 and common.is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        l2 += ('{:^'+str(len(orig))+'}').format(str(x[1]))
        count += x[1]
        ccount += x[1]
        done = False
      else:
        orig = ""
        while len(line) > 0 and not common.is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        if count in hemis.keys() and not done:
          done = True
          summary.append(str(ccount))
          ccount = 0
          summary.append(hemistiches.hemis_types[hemis[count]])
          l2 += ('{:^'+str(len(orig))+'}'
              ).format(hemistiches.hemis_types[hemis[count]])
        else:
          l2 += ' ' * len(orig)
    summary.append(str(ccount)+':')
    result = ''.join(l2)
    summary = ('{:^9}').format(''.join(summary))
    return summary + result

  def report(self):
    num = min(len(self.possible), 4)
    return Error.report(
        self,
        ("Bad metric (expected %s, inferred %d option%s)" %
        (self.pattern.metric, num, ('s' if len(self.possible) != 1 else
          ''))),
        list(map(self.align, self.possible[:num]))
        )

