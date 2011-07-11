#!/usr/bin/python3 -uO

import re
import sys
import unicodedata
import haspirater
import rhyme
import error
from pprint import pprint
from vowels import possible_weights
from common import strip_accents, normalize, is_vowels, consonants, \
  sure_end_fem
from hemistiches import check_hemistiches

def annotate_aspirated(word):
  """Annotate aspirated 'h'"""
  if word[0] != 'h':
    return word
  if haspirater.lookup(word):
    return '*'+word
  else:
    return word

def fit(chunks, pos, left):
  if pos >= len(chunks):
    return [[]]
  if left < 0:
    return []
  if (not is_vowels(chunks[pos])):
    return [[chunks[pos]] + x for x in fit(chunks, pos+1, left)]
  else:
    if (pos >= len(chunks) - 2 and chunks[pos] == 'e'):
      # special case for endings
      if pos == len(chunks) - 1:
        weights = [0]
      elif chunks[pos+1] == 's':
        weights = [0]
      elif chunks[pos+1] == 'nt':
        weights = [0, 1]
      else:
        weights = possible_weights(chunks[pos])
    else:
      weights = possible_weights(chunks[pos])
    result = []
    for weight in weights:
      #print("Take %s with weight %d" % (chunks[pos], weight), file=sys.stderr)
      result += [[(chunks[pos], weight)] + x for x in fit(chunks, pos+1,
        left - weight)]
    return result

def feminine(align, verse):
  for a in sure_end_fem:
    if verse.endswith(a):
      return True
  #pprint(align)
  if verse.endswith('ent') and align[-2][1] != 1:
    return True
  return False

def parse(text, bound):
  original_text = normalize(text)
  text = re.sub("qu", 'q', original_text)
  text = re.sub("gue", 'ge', text)
  text = re.sub("gué", 'gé', text)
  text = re.sub("guè", 'gè', text)
  text = re.sub("gua", 'ga', text)
  #print(text, file=sys.stderr)
  words = text.split(' ')
  words = [annotate_aspirated(word) for word in words if word != '']
  pattern = re.compile('('+consonants+'*)', re.UNICODE)
  for i in range(len(words)):
    words[i] = re.split(pattern, words[i])
    words[i] = [chunk for chunk in words[i] if chunk != '']
    nwords = []
    for chunk in words[i]:
      if 'y' not in chunk or len(chunk) == 1 or chunk[0] == 'y':
        nwords.append(chunk)
      else:
        a = chunk.split('y')
        nwords.append(a[0])
        nwords.append('Y')
        if a[1] != '':
          nwords.append(a[1])
        else:
          # very special case :-/
          if words[i] == ['p', 'ay', 's']:
            nwords.append('y')
    words[i] = nwords
    if i > 0:
      if sum([1 for chunk in words[i-1] if is_vowels(chunk)]) > 1:
        if words[i-1][-1] == 'e' and is_vowels(words[i][0], True):
          words[i-1].pop(-1)
          words[i-1][-1] = words[i-1][-1]+"'"
  for word in words:
    word.append(' ')
  chunks = sum(words, [])[:-1]
 
  return list(map((lambda x : (x, feminine(x, original_text))),
    fit(chunks, 0, bound)))

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
    for line in f.readlines():
      line = line.strip()
      self.pattern_line_no += 1
      if line != '' and line[0] != '#':
        self.template.append(self.parse_template(line.lstrip().rstrip()))

  def count(self, align):
    #TODO cleanup
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
    """Check a line"""
    pattern = self.get()
    # compute alignments, check hemistiches, sort by score
    possible = parse(line, pattern.length + 2)
    possible = list(map((lambda p : (p[0], p[1],
      check_hemistiches(p[0], pattern.hemistiches))), possible))
    possible = map((lambda x : (self.rate(pattern, x), x)), possible)
    possible = sorted(possible, key=(lambda x : x[0]))

    errors = []
    if len(possible) == 0 or possible[0][0] != 0:
      errors.append(error.ErrorBadMetric(possible))
    if len(possible) == 0:
      return errors, pattern
    possible2 = []
    for (score, x) in possible:
      possible2.append((score, x))
      if score != possible[0][0]:
        break
    possible = possible2

    if pattern.myid not in self.env.keys():
      #print(normalize(line))
      self.env[pattern.myid] = rhyme.init_rhyme(normalize(line),
          pattern.rhyme)
      #print("nVALUE")
      #pprint(self.env[pattern.myid])
      #pprint(self.env[pattern.myid])
    else:
      old = list(self.env[pattern.myid])
      self.env[pattern.myid] = rhyme.check_rhyme(self.env[pattern.myid],
          (normalize(line), pattern.rhyme))
      #print("nVALUE")
      #pprint(self.env[pattern.myid])
      if (self.env[pattern.myid][1] == None and
          len(self.env[pattern.myid][0]) == 0):
        errors.append(error.ErrorBadRhymeSound(old, None))
    if pattern.femid not in self.femenv.keys():
      if pattern.femid == 'M':
        x = set(['M'])
      elif pattern.femid == 'F':
        x = set(['F'])
      else:
        x = set(['M', 'F']) 
      self.femenv[pattern.femid] = x
    # TODO this is simplistic and order-dependent
    if pattern.femid.swapcase() in self.femenv.keys():
      new = set(['M', 'F']) - self.femenv[pattern.femid.swapcase()]
      if len(new) > 0:
        self.femenv[pattern.femid] = new
    old = list(self.femenv[pattern.femid])
    #pprint(possible)
    new = list(set(['F' if x[1] else 'M' for (score, x) in possible]))
    self.femenv[pattern.femid] &= set(new)
    #print(old)
    #print(new)
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
    """Reset our state"""
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


if len(sys.argv) != 2:
  print("Usage: %s TEMPLATE" % sys.argv[0], file=sys.stderr)
  print("Check stdin according to template, report errors on stdout"
      % sys.argv[0], file=sys.stderr)
  sys.exit(1)

f = open(sys.argv[1])
template = Template(f)
f.close()

def run():
  while True:
    line = sys.stdin.readline()
    if not line:
      break
    for error in template.check(line):
      error.report()

run()

