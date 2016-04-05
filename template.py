import error
import copy
import re
import rhyme
from verse import Verse
from common import normalize, legal, strip_accents_one, rm_punct
from nature import nature_count
from vowels import possible_weights_ctx, make_query
from pprint import pprint
from options import default_options


class Pattern:
  def __init__(self, metric, myid="", femid="", constraint=None):
    self.metric = metric
    self.parse_metric()
    self.myid = myid
    self.femid = femid
    self.constraint = constraint

  def parse_metric(self):
    """Parse from a metric description"""
    try:
      verse = [int(x) for x in self.metric.split('/')]
      for i in verse:
        if i < 1:
          raise ValueError
    except ValueError:
      raise error.TemplateLoadError(
          _("Metric description should only contain positive integers"))
    if sum(verse) > 16:
      raise error.TemplateLoadError(_("Metric length limit exceeded"))
    self.hemistiches = []
    self.length = 0
    for v in verse:
      self.length += v
      self.hemistiches.append(self.length)
    self.length = self.hemistiches.pop()

class Template:
  option_aliases = {
    'fusionner': 'merge',
    'ambiguous_ok': 'forbidden_ok',
    'ambigu_ok': 'forbidden_ok',
    'dierese': 'diaeresis',
    'verifie_fin_hemistiche': 'check_end_hemistiche',
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


  def __init__(self, string=None):
    self.template = []
    self.pattern_line_no = 0
    self.options = dict(default_options)
    self.mergers = []
    self.overflowed = False
    if string != None:
      self.load(string)
    self.line_no = 0
    self.position = 0
    self.prev = None
    self.env = {}
    self.femenv = {}
    self.occenv = {}
    self.reject_errors = False

  def read_option(self, x):
    try:
      key, value = x.split(':')
    except ValueError:
      raise error.TemplateLoadError(
        _("Global options must be provided as key-value pairs"))
    if key in self.option_aliases.keys():
      key = self.option_aliases[key]
    if key == 'merge':
      self.mergers.append(value)
    elif key == 'diaeresis':
      if value == "classique":
        value = "classical"
      if value not in ["permissive", "classical"]:
        raise error.TemplateLoadError(_("Bad value for global option %s") % key)
      self.options['diaeresis'] = value
    elif key in self.options.keys():
      self.options[key] = str2bool(value)
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

    v = Verse(line, self, pattern)

    if last:
      if was_incomplete and not self.options['incomplete_ok'] and not self.overflowed:
        return [error.ErrorIncompleteTemplate()], pattern, v
      return [], pattern, v

    if self.overflowed:
      return [error.ErrorOverflowedTemplate()], pattern, v

    rhyme_failed = False
    # rhymes
    if pattern.myid not in self.env.keys():
      # initialize the rhyme
      # last_count is passed later
      self.env[pattern.myid] = rhyme.Rhyme(v.normalized,
              pattern.constraint, self.mergers, self.options)
    else:
      # update the rhyme
      self.env[pattern.myid].feed(v.normalized, pattern.constraint)
      if not self.env[pattern.myid].satisfied_phon():
        # no more possible rhymes, something went wrong, check phon
        self.env[pattern.myid].rollback()
        rhyme_failed = True
        errors.append(error.ErrorBadRhymeSound(self.env[pattern.myid],
          self.env[pattern.myid].new_rhyme))

    # occurrences
    if self.options['check_occurrences']:
      if pattern.myid not in self.occenv.keys():
        self.occenv[pattern.myid] = {}
      last_word = re.split(r'[- ]', line_with_case)[-1]
      if last_word not in self.occenv[pattern.myid].keys():
        self.occenv[pattern.myid][last_word] = 0
      self.occenv[pattern.myid][last_word] += 1
      if self.occenv[pattern.myid][last_word] > nature_count(last_word):
        errors.insert(0, error.ErrorMultipleWordOccurrence(last_word,
          self.occenv[pattern.myid][last_word]))

    v.phon = self.env[pattern.myid].phon
    v.parse()

    # now that we have parsed, adjust rhyme to reflect last word length
    # and check eye
    if not rhyme_failed:
      self.env[pattern.myid].adjustLastCount(v.lastCount())
      if not self.env[pattern.myid].satisfied_eye():
        old_phon = len(self.env[pattern.myid].phon)
        self.env[pattern.myid].rollback()
        errors.append(error.ErrorBadRhymeEye(self.env[pattern.myid],
          self.env[pattern.myid].new_rhyme, old_phon))
   
    rhyme_failed = False

    errors = v.problems() + errors

    if ofile:
      possible = v.possible
      if len(possible) == 1:
        for i, p in enumerate(possible[0]):
          if ('weight' in p.keys() and len(p['weights']) > 1
              and p['weight'] > 0):
            print(str(p['weight']) + ' '
                + ' '.join(make_query(possible[0], i)), file=ofile)

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
    old = list(self.femenv[pattern.femid])
    new = v.genders()
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
  if x.lower() in ["yes", "oui", "y", "o", "true", "t", "vrai", "v"]:
    return True
  if x.lower() in ["no", "non", "n", "false", "faux", "f"]:
    return False
  raise error.TemplateLoadError(_("Bad value in global option"))

