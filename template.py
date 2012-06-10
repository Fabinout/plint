import error
from metric import parse
from hemistiches import check_hemistiches
import copy
import rhyme
from common import normalize, legal, strip_accents_one
from nature import nature_count
from vowels import possible_weights_ctx, make_query


def handle(poss):
  l = []
  #print(poss)
  for i in range(len(poss)):
    if isinstance(poss[i], tuple):
      #print(cleared[:i][::-1])
      #print(cleared[i+1:])
      # print(poss)
      # print (make_query(poss, i))
      if len(possible_weights_ctx(poss, i)) > 1:
        l.append((poss[i][1], make_query(poss, i)))
  return l

class Pattern:
  def __init__(self, metric, myid, femid, constraint):
    self.metric = metric
    self.parse_metric()
    self.myid = myid
    self.femid = femid
    self.constraint = constraint

  def parse_metric(self):
    """Parse from a metric description"""
    verse = [int(x) for x in self.metric.split('/')]
    if sum(verse) > 16:
      raise ValueError
    self.hemistiches = []
    self.length = 0
    for v in verse:
      self.length += v
      self.hemistiches.append(self.length)
    self.length = self.hemistiches.pop()

class Template:
  def __init__(self, string):
    self.template = []
    self.pattern_line_no = 0
    self.forbidden_ok = False
    self.normande_ok = True
    self.diaeresis = "classical"
    self.mergers = []
    self.load(string)
    self.line_no = 0
    self.position = 0
    self.prev = None
    self.env = {}
    self.femenv = {}
    self.occenv = {}
    self.reject_errors = False

  def read_option(self, x):
    key, value = x.split(':')
    if key == "merge":
      self.mergers.append(value)
    elif key == "forbidden_ok":
      self.forbidden_ok = str2bool(value)
    elif key == "normande_ok":
      self.normande_ok = str2bool(value)
    elif key == "diaeresis":
      self.diaeresis = value # TODO: "none"
    else:
      raise ValueError

  def load(self, s):
    """Load from a string"""
    for line in s.split('\n'):
      line = line.strip()
      self.pattern_line_no += 1
      if line != '' and line[0] != '#':
        if line[0] == '!':
          # don't count the '!' in the options, that's why we use [1:]
          for option in line.split()[1:]:
            self.read_option(option)
        else:
          self.template.append(self.parse_line(line.strip()))

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
    return ((1+len(hemis.keys()))*abs(pattern.length - c)
        + sum([1 for x in hemis.values() if x != "ok"]))

  def match(self, line, ofile=None):
    """Check a line against current pattern, return errors"""

    line_with_case = normalize(line, downcase=False)
    line = normalize(line)
    pattern = self.get()

    errors = []

    # rhymes
    if pattern.myid not in self.env.keys():
      # initialize the rhyme
      self.env[pattern.myid] = rhyme.Rhyme(line, pattern.constraint,
          self.mergers, self.normande_ok)
    else:
      # update the rhyme
      old_p = self.env[pattern.myid].phon
      old_e = self.env[pattern.myid].eye
      self.env[pattern.myid].feed(line, pattern.constraint)
      # no more possible rhymes, something went wrong
      if not self.env[pattern.myid].satisfied():
        self.env[pattern.myid].phon = old_p
        self.env[pattern.myid].eye = old_e
        errors.append(error.ErrorBadRhymeSound(self.env[pattern.myid], None))

    # compute alignments, check hemistiches, sort by score
    possible = parse(line, self.env[pattern.myid].phon, pattern.length + 2,
        self.forbidden_ok, self.diaeresis)
    if not possible:
      errors.append(error.ErrorForbiddenPattern())
      possible = []
      return errors, pattern
    possible = list(map((lambda p: (p[0], p[1],
      check_hemistiches(p[0], pattern.hemistiches))), possible))
    possible = map((lambda x: (self.rate(pattern, x), x)), possible)
    possible = sorted(possible, key=(lambda x: x[0]))

    # check characters
    illegal = set()
    for x in line:
      if not strip_accents_one(x)[0] in legal:
        illegal.add(x)
    if len(illegal) > 0:
      errors.append(error.ErrorBadCharacters(illegal))

    # check metric
    if len(possible) == 0 or possible[0][0] != 0:
      errors.append(error.ErrorBadMetric(possible))
    if len(possible) == 0:
      return errors, pattern
    # keep the best alignment as hypotheses
    possible = [(score, align) for (score, align) in possible
        if score == possible[0][0]]
    if ofile:
      if len(possible) == 1 and possible[0][0] == 0:
        l = [(x[1][0]) for x in possible]
        poss = []
        for p in l:
          c = []
          while len(p) > 0:
            x = p.pop()
            if x == ' ':
              poss.append(c[::-1])
              c = []
            else:
              c.append(x)
          if len(c) > 0:
            poss.append(c[::-1])
        for w in poss:
          l = handle(w)
          for x in l:
            # print(x)
            print((str(x[0]) + ' ' + ' '.join(x[1])), file=ofile)

    # occurrences
    if pattern.myid not in self.occenv.keys():
      self.occenv[pattern.myid] = {}
    last_word = line_with_case.split(' ')[-1]
    if last_word not in self.occenv[pattern.myid].keys():
      self.occenv[pattern.myid][last_word] = 0
    self.occenv[pattern.myid][last_word] += 1
    if self.occenv[pattern.myid][last_word] > nature_count(last_word):
      errors.append(error.ErrorMultipleWordOccurrence(last_word,
        self.occenv[pattern.myid][last_word]))

    # rhyme genres
    # inequality constraint
    # TODO this is simplistic and order-dependent
    if pattern.femid.swapcase() in self.femenv.keys():
      new = set(['M', 'F']) - self.femenv[pattern.femid.swapcase()]
      if len(new) > 0:
        self.femenv[pattern.femid] = new
    if pattern.femid not in self.femenv.keys():
      if pattern.femid == 'M':
        x = set(['M'])
      elif pattern.femid == 'F':
        x = set(['F'])
      else:
        x = set(['M', 'F'])
      self.femenv[pattern.femid] = x
    else:
      old = list(self.femenv[pattern.femid])
      new = list(set(sum([x[1] for (score, x) in possible], [])))
      self.femenv[pattern.femid] &= set(new)
      if len(self.femenv[pattern.femid]) == 0:
        errors.append(error.ErrorBadRhymeGenre(old, new))

    return errors, pattern

  def parse_line(self, line):
    """Parse template line from a line"""
    split = line.split(' ')
    metric = split[0]
    if len(split) >= 2:
      myid = split[1]
    else:
      myid = str(self.pattern_line_no) # unique
    if len(split) >= 3:
      femid = split[2]
    else:
      femid = str(self.pattern_line_no) # unique
    idsplit = myid.split(':')
    if len(idsplit) >= 2:
      constraint = idsplit[-1].split('|')
      if len(constraint) > 0:
        constraint[0] = False if constraint[0] == "no" else constraint[0]
      if len(constraint) > 1:
        constraint[1] = int(constraint[1])
    else:
      constraint = []
    if len(constraint) == 0:
      constraint.append(1)
    if len(constraint) < 2:
      constraint.append(True)
    return Pattern(metric, myid, femid, rhyme.Constraint(*constraint))

  def reset_conditional(self, d):
    return dict((k, v) for k, v in d.items() if k[0] == '!')

  def reset_state(self, with_femenv=False):
    """Reset our state, except ids starting with '!'"""
    self.position = 0
    self.env = self.reset_conditional(self.env)
    self.femenv = self.reset_conditional(self.femenv)
    self.occenv = {} # always reset

  def get(self):
    """Get next state, resetting if needed"""
    self.old_position = self.position
    self.old_env = copy.deepcopy(self.env)
    self.old_femenv = copy.deepcopy(self.femenv)
    if self.position >= len(self.template):
      self.reset_state()
    result = self.template[self.position]
    self.position += 1
    return result

  def back(self):
    """Revert to previous state"""
    self.position = self.old_position
    self.env = copy.deepcopy(self.old_env)
    self.femenv = copy.deepcopy(self.old_femenv)

  def check(self, line, ofile=None):
    """Check line (wrapper)"""
    self.line_no += 1
    line = line.rstrip()
    if normalize(line) == '':
      return []
    #possible = [compute(p) for p in possible]
    #possible = sorted(possible, key=rate)
    errors, pattern = self.match(line, ofile)
    for error in errors:
      # update errors with line position and pattern
      error.pos(line, self.line_no, pattern)
    if len(errors) > 0 and self.reject_errors:
      self.back()
      self.line_no -= 1
    return errors

def str2bool(x):
  if x == "yes":
    return True
  if x == "no":
    return False
  raise ValueError

