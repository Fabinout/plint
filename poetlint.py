#!/usr/bin/python3 -uO

import re
import sys
import unicodedata
import haspirater
import rhyme
#import cProfile
from pprint import pprint

#TODO no clear femid env for implicit repeat
#TODO femid pattern groups (not all the same)


consonants = "[bcçdfghjklmnpqrstvwxz*-]"
vowels = 'aeiouyœæ'

# TODO -ment at hemistiche
sure_end_fem = ['es', 'e']
end_fem = sure_end_fem + ['ent']

hemistiche_pos = 6
num_verse = 12

def contains_trema(chunk):
  for x in ['ä', 'ï', 'ö', 'ü', 'ÿ']:
    if x in chunk:
      return True
  return False

def possible_weights(chunk):
  if len(chunk) == 1:
    return [1]
  # old spelling and weird exceptions
  if chunk in ['ouï']:
    return [2]
  if chunk in ['eüi', 'aoû']:
    return [1]
  if contains_trema(chunk):
    return [2]
  chunk = strip_accents(chunk, True)
  # TODO 'ée' ? ('déesse')
  if chunk in ['ai', 'ou', 'eu', 'ei', 'eau', 'eoi', 'eui', 'au', 'oi',
      'oie', 'œi', 'œu', 'eaie', 'aie', 'oei', 'oeu', 'ea', 'ae', 'eo',
      'eoie', 'oe', 'eai', 'eue', 'aa', 'oo', 'ee', 'ii', 'aii',
      'yeu', 'ye']:
    return [1]
  for x in ['oa', 'ea', 'eua', 'ao', 'euo', 'ua', 'uo', 'yo', 'yau']:
    if x in chunk:
      return [2]
  if chunk == 'ée':
    return [1, 2]
  if chunk[0] == 'i':
    return [1, 2]
  if chunk[0] == 'u' and (strip_accents(chunk[1]) in ['i', 'e']):
    return [1, 2]
  if chunk[0] == 'o' and chunk[1] == 'u' and len(chunk) >= 3 and strip_accents(chunk[2]) in ['i', 'e']:
    return [1, 2]
  if 'é' in chunk or 'è' in chunk:
    return [2]
  # only non-accented left
  
  # TODO hmm
  return [99]

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents_one(s, with_except):
  r = []
  for x in s:
    if with_except and x in ['è', 'é']:
      r.append(x)
    else:
      r += unicodedata.normalize('NFD', x)
  return r

def strip_accents(s, with_except=False):
  return ''.join(
      (c for c in strip_accents_one(s, with_except)
      if unicodedata.category(c) != 'Mn'))

def norm_spaces(text):
  return re.sub("\s+-*\s*", ' ', text)

def rm_punct(text):
  text = re.sub("'", '', text)
  #TODO rather: keep only good chars
  pattern = re.compile('[^\w -]', re.UNICODE)
  return pattern.sub(' ', text)

def annotate_aspirated(word):
  if word[0] != 'h':
    return word
  if haspirater.lookup(word):
    return '*'+word
  else:
    return word

def is_vowels(chunk, with_h = False, with_y = True):
  if not with_y and chunk == 'y':
    return False
  for char in strip_accents(chunk):
    if char not in vowels:
      if char != 'h' or not with_h:
        return False
  return True

def count_vowel_chunks(word):
  return sum([1 for chunk in word if is_vowels(chunk)])

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

def normalize(text):
  return norm_spaces(rm_punct(text.lower())).rstrip().lstrip()

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
      if count_vowel_chunks(words[i-1]) > 1:
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
      self.say("         " + l)
    
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
    #TODO
    return 'TODO'

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
    align, feminine = align
    l2 = []
    count = 0
    for x in align:
      if isinstance(x, tuple):
        l2 += ('{:^'+str(len(x[0]))+'}').format(str(x[1]))
        count += x[1]
      else:
        if x == ' ' and count in self.pattern.hemistiches:
          l2 += '/'
        else:
          l2 += ' ' * len(x)
    l2 += ' (%d)' % score
    return ''.join(l2)

  def report(self):
    num = min(len(self.possible), 4)
    Error.report(
        self,
        ("Bad metric (expected %s, inferred the %d following)" %
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
    for line in f.readlines():
      line = line.strip()
      if line != '' and line[0] != '#':
        self.template.append(self.parse_template(line.lstrip().rstrip()))
    self.reset_state()
    self.line_no = 0

  def count(self, align):
    return sum([x[1] for x in align if isinstance(x, tuple)])

  def rate(self, pattern, align):
    align, fem = align
    c = self.count(align)
    #print("%d is len" % c)
    #TODO one pass would be enough
    hemis = []
    ok = True
    #print ("HEMIS")
    pos = 0
    h2 = 0
    for h in pattern.hemistiches:
      r, pos = check_hemistiche(align, pos, h-h2)
      h2 = h
      hemis.append(r)
      #print (hemis[-1])
      if hemis[-1] != "ok":
        ok = False
    if ok and c == pattern.length:
      return 0
    return (len(hemis)*abs(pattern.length - c)
        + sum([1 for x in hemis if x == "ok"]))

  def match(self, line):
    pattern = self.get()
    possible = parse(line, pattern.length + 2)
    #pprint("POSSIBLE")
    #pprint(possible)
    errors = []

    possible = map((lambda x : (self.rate(pattern, x), x)), possible)
    possible = sorted(possible, key=(lambda x : x[0]))
    if len(possible) == 0 or possible[0][0] != 0:
      errors.append(ErrorBadMetric(possible))
    if len(possible) == 0:
      return errors
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
    else:
      self.env[pattern.myid] = rhyme.check_rhyme(self.env[pattern.myid],
          (normalize(line), pattern.rhyme))
      #print("nVALUE")
      #pprint(self.env[pattern.myid])
      if (self.env[pattern.myid][1] == None and
          len(self.env[pattern.myid][0]) == 0):
        errors.append(ErrorBadRhymeSound(None, None))
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
      errors.append(ErrorBadMetric(possible))

    return errors, pattern

  def parse_template(self, l):
    split = l.split(' ')
    metric = split[0]
    myid = split[1]
    femid = split[2]
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
    self.position = 0
    self.env = {}
    self.femenv = {}

  def get(self):
    if self.position >= len(self.template):
      self.reset_state()
    result = self.template[self.position]
    self.position += 1
    return result

  def check(self, line):
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

#cProfile.run('run()', 'poetlint.prof')
run()

