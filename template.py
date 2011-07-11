import error
from metric import parse
from hemistiches import check_hemistiches
import rhyme
from common import normalize

class Pattern:
  def __init__(self, metric, myid, femid, rhyme):
    self.metric = metric
    self.parse_metric()
    self.myid = myid
    self.femid = femid
    self.rhyme = rhyme

  def parse_metric(self):
    """Parse from a metric description"""
    verse = [int(x) for x in self.metric.split('/')]
    self.hemistiches = []
    self.length = 0
    for v in verse:
      self.length += v
      self.hemistiches.append(self.length)
    self.length = self.hemistiches.pop()

class Template:
  def __init__(self, stream):
    self.template = []
    self.pattern_line_no = 0
    self.load(stream)
    self.line_no = 0
    self.position = 0
    self.env = {}
    self.femenv = {}

  def load(self, stream):
    """Load from a stream"""
    for line in stream.readlines():
      line = line.strip()
      self.pattern_line_no += 1
      if line != '' and line[0] != '#':
        self.template.append(self.parse_template(line.lstrip().rstrip()))

  def count(self, align):
    """total weight of an align"""
    return sum([x[1] for x in align if isinstance(x, tuple)])

  def rate(self, pattern, align):
    """Rate align according to pattern"""
    align, fem, hemis = align
    c = self.count(align)
    ok = True
    for h in hemis.values():
      if h != "ok":
        ok = False
    if ok and c == pattern.length:
      return 0
    return (len(hemis.keys())*abs(pattern.length - c)
        + sum([1 for x in hemis.values() if x != "ok"]))

  def match(self, line):
    """Check a line against current pattern, return errors"""
    pattern = self.get()
    # compute alignments, check hemistiches, sort by score
    possible = parse(line, pattern.length + 2)
    possible = list(map((lambda p : (p[0], p[1],
      check_hemistiches(p[0], pattern.hemistiches))), possible))
    possible = map((lambda x : (self.rate(pattern, x), x)), possible)
    possible = sorted(possible, key=(lambda x : x[0]))

    errors = []
    
    # check metric
    if len(possible) == 0 or possible[0][0] != 0:
      errors.append(error.ErrorBadMetric(possible))
    if len(possible) == 0:
      return errors, pattern
    # keep the best alignment as hypotheses
    possible = [(score, align) for (score, align) in possible
        if score == possible[0][0]]

    # rhymes
    if pattern.myid not in self.env.keys():
      # initialize the rhyme
      self.env[pattern.myid] = rhyme.init_rhyme(normalize(line),
          pattern.rhyme)
    else:
      # update the rhyme
      old = list(self.env[pattern.myid])
      self.env[pattern.myid] = rhyme.check_rhyme(self.env[pattern.myid],
          (normalize(line), pattern.rhyme))
      # no more possible rhymes, something went wrong
      if (self.env[pattern.myid][1] == None and
          len(self.env[pattern.myid][0]) == 0):
        errors.append(error.ErrorBadRhymeSound(old, None))

    # rhyme genres
    # TODO refactor this
    if pattern.femid not in self.femenv.keys():
      if pattern.femid == 'M':
        x = set(['M'])
      elif pattern.femid == 'F':
        x = set(['F'])
      else:
        x = set(['M', 'F']) 
      self.femenv[pattern.femid] = x
    else:
      # TODO this is simplistic and order-dependent
      if pattern.femid.swapcase() in self.femenv.keys():
        new = set(['M', 'F']) - self.femenv[pattern.femid.swapcase()]
        if len(new) > 0:
          self.femenv[pattern.femid] = new

      old = list(self.femenv[pattern.femid])
      new = list(set(['F' if x[1] else 'M' for (score, x) in possible]))
      self.femenv[pattern.femid] &= set(new)
      if len(self.femenv[pattern.femid]) == 0:
        errors.append(error.ErrorBadRhymeGenre(old, new))

    return errors, pattern

  def parse_template(self, l):
    """Parse template from a line"""
    split = l.split(' ')
    metric = split[0]
    if len(split) >= 2:
      myid = split[1]
    else:
      myid = str(self.pattern_line_no)
    if len(split) >= 3:
      femid = split[2]
    else:
      femid = str(self.pattern_line_no)
    if len(split) >= 4:
      rhyme = [int(x) for x in split[3].split('|')]
    else:
      rhyme = []
    if len(rhyme) == 0:
      rhyme.append(1)
    while len(rhyme) < 3:
      rhyme.append(-1)
    return Pattern(metric, myid, femid, rhyme)

  def reset_conditional(self, d):
    return dict((k, v) for x, v in d.items() if x[-1] == '!')

  def reset_state(self, with_femenv=False):
    """Reset our state, except ids ending with '!'"""
    self.position = 0
    self.env = self.reset_conditional(self.env)
    self.femenv = self.reset_conditional(self.femenv)

  def get(self):
    """Get next state, resetting if needed"""
    if self.position >= len(self.template):
      self.reset_state()
    result = self.template[self.position]
    self.position += 1
    return result

  def check(self, line):
    """Check line (wrapper)"""
    self.line_no += 1
    line = line.rstrip()
    if line == '':
      return []
    #possible = [compute(p) for p in possible]
    #possible = sorted(possible, key=rate)
    errors, pattern = self.match(line)
    for error in errors:
      error.pos(line, self.line_no, pattern)
    return errors

