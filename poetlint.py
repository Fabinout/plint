#!/usr/bin/python3 -uO

import re
import sys
import unicodedata
import haspirater
import rhyme
from pprint import pprint
from vowels import possible_weights
from common import strip_accents, normalize, is_vowels

#TODO no clear femid env for implicit repeat
#TODO femid pattern groups (not all the same)

consonants = "[bcçdfghjklmnpqrstvwxz*-]"

# Forbidden at the end of a hemistiche. "-ent" would also be forbidden
# in some cases but not others...
sure_end_fem = ['es', 'e']

hemis_short = {'ok' : '/', 'bad' : '!', 'cut' : ':', 'fem' : '\\'}

def annotate_aspirated(word):
  if word[0] != 'h':
    return word
  if haspirater.lookup(word):
    return '*'+word
  else:
    return word

def check_spaces(align, pos):
  if pos >= len(align):
    return "bad"
  if align[pos] == ' ':
    return "ok"
  if not isinstance(align[pos], tuple):
    return check_spaces(align, pos + 1)
  return "cut"

def check_hemistiche(align, pos, hem):
  if pos >= len(align):
    return ("bad", pos)
  if hem == 0:
    return (check_spaces(align, pos), pos)
  if hem < 0:
    return ("cut", pos)
  if not isinstance(align[pos], tuple):
    return check_hemistiche(align, pos +1, hem)
  if hem == 1:
    if pos + 1 >= len(align):
      # this is weird
      return ("bad", pos)
    if ((align[pos][0] + align[pos+1]).rstrip() in sure_end_fem):
      # no feminine at hemistiche
      # maybe it's a lone word?
      ok = False
      for i in range(2):
        for j in ' -':
          if j in align[pos-i-1]:
            ok = True
      if not ok:
        #print ("refuse hemistiche", file=sys.stderr)
        return ("fem", pos)
  return check_hemistiche(align, pos+1, hem - align[pos][1])

def fit(chunks, pos, left):
  if pos >= len(chunks):
    return [[]]
  if left < 0:
    return []
  if (not is_vowels(chunks[pos])):
    return prepend([chunks[pos]], fit(chunks, pos+1, left))
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
      result += prepend([(chunks[pos], weight)], fit(chunks, pos+1,
        left - weight))
    return result

def feminine(align, verse):
  for a in sure_end_fem:
    if verse.endswith(a):
      return True
  #pprint(align)
  if verse.endswith('ent') and align[-2][1] != 1:
    return True
  return False

def nullify(chunk):
  if is_vowels(chunk):
    return (chunk, 0)
  else:
    return chunk

def align2(result):
  align, feminine, c, hemi = result
  l2 = [('{:^2}').format(str(c))]
  l2 += ['f'] if feminine else ["m"]
  l2 += '-H'
  l2 += [('{:^3}').format(hemi)]
  l2 += ' '
  count = 0
  for x in align:
    if isinstance(x, tuple):
      l2 += ('{:^'+str(len(x[0]))+'}').format(str(x[1]))
      count += x[1]
    else:
      if x == ' ' and count == hemistiche_pos:
        l2 += '/'
      else:
        l2 += ' ' * len(x)
  return ''.join(l2)

def align1(result, success):
  l1 = '-------- ' if success else '!!!ERROR '
  for x in result[0]:
    if isinstance(x, tuple):
      l1 += x[0]
    else:
      l1 += x
  return ''.join(l1)

def append(ls, l):
  r = []
  for x in ls:
    r.append(x + l)
  return r
def prepend(l, ls):
  r = []
  for x in ls:
    r.append(l + x)
  return r

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
          # TODO very special case :-/
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
    print(self.prefix + l)

  def report(self, s, t = []):
    self.say("error: %s" % (s))
    #TODO optional
    self.say("Line is: %s" % (self.line))
    for l in t:
      self.say(l)
    
class ErrorBadRhyme(Error):
  def __init__(self, expected, inferred):
    Error.__init__(self)
    self.expected = expected
    self.inferred = inferred

  def report(self):
    Error.report(self, "Bad rhyme %s for type %s (expected %s, inferred %s)"
        % (self.kind, self.pattern.myid, self.fmt(self.expected),
          self.fmt(self.inferred)))

class ErrorBadRhymeGenre(ErrorBadRhyme):
  def fmt(self, l):
    return ' or '.join(list(l))

  @property
  def kind(self):
    return "genre"

class ErrorBadRhymeSound(ErrorBadRhyme):
  def fmt(self, l):
    pron, spel, constraint = l
    ok = []
    if len(pron) > 0:
      ok.append("")


  def report(self):
    Error.report(self, "Bad rhyme %s for type %s (expected %s)"
        % (self.kind, self.pattern.myid, self.fmt(self.expected)))

  @property
  def kind(self):
    return "value"

class ErrorBadMetric(Error):
  def __init__(self, possible):
    Error.__init__(self)
    self.possible = possible

  def align(self, align):
    #TODO include a summary
    #TODO match to real line
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
        while len(line) > 0 and is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        l2 += ('{:^'+str(len(orig))+'}').format(str(x[1]))
        count += x[1]
        ccount += x[1]
        done = False
      else:
        orig = ""
        while len(line) > 0 and not is_vowels(line[0]):
          orig += line[0]
          line = line[1:]
        if count in hemis.keys() and not done:
          done = True
          summary.append(str(ccount))
          ccount = 0
          summary.append(hemis_short[hemis[count]])
          l2 += ('{:^'+str(len(orig))+'}'
              ).format(hemis_short[hemis[count]])
        else:
          l2 += ' ' * len(orig)
    summary.append(str(ccount))
    result = ''.join(l2)
    summary = ('{:^9}').format(''.join(summary))
    return summary + result

  def report(self):
    num = min(len(self.possible), 4)
    Error.report(
        self,
        ("Bad metric (expected %s, inferred %d options)" %
        (self.pattern.metric, num)),
        list(map(self.align, self.possible[:num])))

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
    self.reset_state()
    self.line_no = 0

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

  def check_hemis(self, pattern, align):
    hemis = {}
    pos = 0
    h2 = 0
    for h in pattern.hemistiches:
      r, pos = check_hemistiche(align, pos, h-h2)
      h2 = h
      hemis[h] = r
    return hemis

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
    possible = parse(line, pattern.length + 2)
    possible = list(map((lambda p : (p[0], p[1],
      self.check_hemis(pattern, p[0]))), possible))
    #pprint("POSSIBLE")
    #pprint(possible)
    errors = []

    possible = map((lambda x : (self.rate(pattern, x), x)), possible)
    possible = sorted(possible, key=(lambda x : x[0]))
    if len(possible) == 0 or possible[0][0] != 0:
      errors.append(ErrorBadMetric(possible))
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
        errors.append(ErrorBadRhymeSound(old, None))
    if pattern.femid not in self.femenv.keys():
      if pattern.femid == 'M':
        x = set(['M'])
      elif pattern.femid == 'F':
        x = set(['F'])
      else:
        x = set(['M', 'F'])
      self.femenv[pattern.femid] = x
    old = list(self.femenv[pattern.femid])
    #pprint(possible)
    new = list(set(['F' if x[1] else 'M' for (score, x) in possible]))
    self.femenv[pattern.femid] &= set(new)
    #print(old)
    #print(new)
    if len(self.femenv[pattern.femid]) == 0:
      errors.append(ErrorBadRhymeGenre(old, new))
      #TODO debug
      #errors.append(ErrorBadMetric(possible))

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

  def reset_state(self):
    """Reset our state"""
    self.position = 0
    self.env = {}
    self.femenv = {}

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

