import error
import copy
import rhyme
from verse import Verse
from common import normalize, legal, strip_accents_one, rm_punct
from nature import nature_count
from vowels import possible_weights_ctx, make_query
from pprint import pprint


def handle(poss):
  l = []
  for i in range(len(poss)):
    if isinstance(poss[i], tuple):
      if len(possible_weights_ctx(poss, i)) > 1:
        l.append((poss[i][1], make_query(poss, i)))
  return l

class Pattern:
  def __init__(self, metric, myid="", femid="", constraint=None):
    self.metric = metric
    self.parse_metric()
    self.myid = myid
    self.femid = femid
    self.constraint = constraint

  def parse_metric(self):
    """Parse from a metric description"""
    verse = [int(x) for x in self.metric.split('/')]
    if sum(verse) > 16:
      raise error.TemplateLoadError(_("Metric length limit exceeded"))
    self.hemistiches = []
    self.length = 0
    for v in verse:
      self.length += v
      self.hemistiches.append(self.length)
    self.length = self.hemistiches.pop()

class Template:
  def __init__(self, string=None):
    self.template = []
    self.pattern_line_no = 0
    self.forbidden_ok = False
    self.hiatus_ok = False
    self.normande_ok = True
    self.repeat_ok = True
    self.overflowed = False
    self.incomplete_ok = True
    self.check_end_hemistiche = True
    self.check_occurrences = True
    self.diaeresis = "classical"
    self.mergers = []
    if string:
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
    if key in ["merge", "fusionner"]:
      self.mergers.append(value)
    elif key in ["forbidden_ok", "ambiguous_ok", "ambigu_ok"]:
      self.forbidden_ok = str2bool(value)
    elif key in ["hiatus_ok"]:
      self.hiatus_ok = str2bool(value)
    elif key in ["normande_ok"]:
      self.normande_ok = str2bool(value)
    elif key in ["diaeresis", "dierese"]:
      if value == "classique":
        value = "classical"
      self.diaeresis = value
      if value not in ["permissive", "classical"]:
        raise error.TemplateLoadError(_("Bad value for global option %s") % key)
    elif key in ["check_end_hemistiche", "verifie_fin_hemistiche"]:
      self.check_end_hemistiche = str2bool(value)
    elif key in ["check_occurrences", "verifie_occurrences"]:
      self.check_occurrences = str2bool(value)
    elif key in ["repeat_ok"]:
      self.repeat_ok = str2bool(value)
    elif key in ["incomplete_ok"]:
      self.incomplete_ok = str2bool(value)
    else:
      raise error.TemplateLoadError(_("Unknown global option"))

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
    if len(self.template) == 0:
      raise error.TemplateLoadError(_("Template is empty"))

  def match(self, line, ofile=None, quiet=False, last=False):
    """Check a line against current pattern, return errors"""

    was_incomplete = last and not self.beyond

    errors = []
    pattern = self.get()

    line_with_case = normalize(line, downcase=False)
    line_normalize = normalize(line)

    v = Verse(line, self, pattern)

    if last:
      if was_incomplete and not self.incomplete_ok and not self.overflowed:
        return [error.ErrorIncompleteTemplate()], pattern, v
      return [], pattern, v

    if self.overflowed:
      return [error.ErrorOverflowedTemplate()], pattern, verse

    # rhymes
    if pattern.myid not in self.env.keys():
      # initialize the rhyme
      self.env[pattern.myid] = rhyme.Rhyme(line_normalize, pattern.constraint,
          self.mergers, self.normande_ok)
    else:
      # update the rhyme
      old_p = self.env[pattern.myid].phon
      old_e = self.env[pattern.myid].eye
      self.env[pattern.myid].feed(line_normalize, pattern.constraint)
      # no more possible rhymes, something went wrong
      if not self.env[pattern.myid].satisfied():
        self.env[pattern.myid].phon = old_p
        self.env[pattern.myid].eye = old_e
        errors.append(error.ErrorBadRhymeSound(self.env[pattern.myid], None))

    errors += v.problems()

    if ofile:
      possible = v.possible
      if len(possible) == 1:
        l = list(possible[0])
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
            # TODO update this code
            print((str(x[0]) + ' ' + ' '.join(x[1])), file=ofile)

    # occurrences
    if self.check_occurrences:
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
      new = v.genders(self.env[pattern.myid].phon)
      self.femenv[pattern.femid] &= set(new)
      if len(self.femenv[pattern.femid]) == 0:
        errors.append(error.ErrorBadRhymeGenre(old, new))

    return errors, pattern, v

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
        constraint[0] = False if constraint[0] in ["no", "non"] else constraint[0]
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

  @property
  def beyond(self):
    return self.position >= len(self.template)

  def get(self):
    """Get next state, resetting if needed"""
    self.old_position = self.position
    self.old_env = copy.deepcopy(self.env)
    self.old_femenv = copy.deepcopy(self.femenv)
    self.old_occenv = copy.deepcopy(self.occenv)
    if self.beyond:
      if not self.repeat_ok:
        self.overflowed = True
      self.reset_state()
    result = self.template[self.position]
    self.position += 1
    return result

  def back(self):
    """Revert to previous state"""
    self.position = self.old_position
    self.env = copy.deepcopy(self.old_env)
    self.femenv = copy.deepcopy(self.old_femenv)
    self.occenv = copy.deepcopy(self.old_occenv)

  def check(self, line, ofile=None, quiet=False, last=False):
    """Check line (wrapper)"""
    self.line_no += 1
    line = line.rstrip()
    if normalize(line) == '' and not last:
      return None
    #possible = [compute(p) for p in possible]
    #possible = sorted(possible, key=rate)
    errors, pattern, verse = self.match(line, ofile, quiet=quiet, last=last)
    if len(errors) > 0:
      if self.reject_errors:
        self.back()
        self.line_no -= 1
      return error.ErrorCollection(self.line_no, line, pattern, verse, errors)
    return None

def str2bool(x):
  if x.lower() in ["yes", "oui", "y", "o"]:
    return True
  if x.lower() in ["no", "non", "n"]:
    return False
  raise error.TemplateLoadError(_("Bad value in global option"))

