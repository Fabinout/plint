#!/usr/bin/python3 -u

import re
import sys
import unicodedata
import aspire
from pprint import pprint

consonants = "[bcçdfghjklmnpqrstvwxz*-]"
vowels = 'aeiouyœæ'

# TODO -ment at hemistiche
# TODO diaresis
# TODO rhymes
# TODO vers en -es sont masc, pas fém
sure_end_fem = ['es', 'e']
end_fem = sure_end_fem + ['ent']

count_two = ['aë', 'aï', 'ao', 'éa', 'éi', 'éo', 'éu', 'êa', 'êi',
'êo', 'êu', 'èa', 'èi', 'èo', 'èu', 'oa', 'oya' , 'ueu', 'euâ', 'éâ',
'oï', 'aïeu', 'oüoi', 'ouï', 'aïe', 'oè', 'oüé', 'ii', 'uau', 'oé',
'uï', 'uïe']
# TODO 'ée' ? ('déesse')
can_count_two = ['ia', 'ée', 'ieue', 'ieu', 'ua', 'ié', 'iée', 'io', 'iu',
'iue', 'ue', 'ui', 'ie', 'oue', 'oua', 'oueu', 'ouaie', 'ouai', 'oui', 'iè',
'oué', 'ué', 'uée', 'uia', 'iai', 'yau', 'uo', 'yo']

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents(s):
  return ''.join(
      (c for c in unicodedata.normalize('NFD', s)
      if unicodedata.category(c) != 'Mn'))

def norm_spaces(text):
  return re.sub("\s+", ' ', text)

def rm_punct(text):
  text = re.sub("'", '', text)
  pattern = re.compile('[^\w -]', re.UNICODE)
  return pattern.sub(' ', text)

def annotate_aspirated(word):
  if word[0] != 'h':
    return word
  if aspire.lookup(word):
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

def possible_weights(chunk):
  if chunk in count_two:
    return [2]
  if chunk in can_count_two:
    return [1,2]
  return [1]

def fit(chunks, left, past):
  if left == 7 and (len(chunks) < 2 or chunks[0] + chunks[1] in
      sure_end_fem):
    # no feminine at hemistiche
    # maybe it's a lone word?
    ok = False
    for i in range(2):
      for j in ' -':
        if j in past[-i]:
          ok = True
    if not ok:
      print ("refuse hemistiche", file=sys.stderr)
      return None
  weights = possible_weights(chunks[0])
  for weight in weights:
    nleft = left - weight
    print("Take %s with weight %d, left %d" % (chunks[0], weight,
      nleft), file=sys.stderr)
    result = maybe_sum([(chunks[0], weight)], skip(chunks[1:], nleft,
      past+[chunks[0]], nleft == 6))
    if result != None:
      return result
    print("FAIL!", file=sys.stderr)
  return None

def maybe_sum(a, b):
  if b == None or a == None:
    return None
  else:
    return a + b
  
def skip(chunks, left, past, expect_space=False):
  result = []
  chunks = list(chunks)
  if len(chunks) > 0 and not is_vowels(chunks[0]):
    return maybe_sum([chunks[0]], skip(chunks[1:], left, past +
      [chunks[0]], expect_space and not chunks[0] == ' '))
  if len(chunks) == 0:
    if left == 0:
      print("OK", file=sys.stderr)
      return []
    else:
      print("out of chunks", file=sys.stderr)
      return None
  if expect_space:
    # we wanted a space and haven't got it, fail
    print("wanted space", file=sys.stderr)
    return None
  return fit(chunks, left, past)

def get_feminine(text):
  for end in end_fem:
    if text.endswith(end):
      return end
  return ''

def nullify(chunk):
  if is_vowels(chunk):
    return (chunk, 0)
  else:
    return chunk

def align(result):
  align, feminine = result
  if align == None:
    return "Non."
  l1 = ['F  '] if feminine else ["M  "]
  l2 = ['12 ']
  for x in align:
    if isinstance(x, tuple):
      l1 += x[0]
      l2 += ('{:^'+str(len(x[0]))+'}').format(str(x[1]))
    else:
      l1 += x
      l2 += ' ' * len(x)
  return ''.join(l1) + '\n' + ''.join(l2)

def parse(text):
  text = norm_spaces(rm_punct(text.lower())).rstrip().lstrip()
  oend = get_feminine(text)
  feminine = oend != ''
  end = oend
  text = re.sub("qu", 'q', text)
  text = re.sub("gue", 'ge', text)
  print(text, file=sys.stderr)
  words = text.split(' ')
  words = [annotate_aspirated(word) for word in words]
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
          # TODO ouais c'est foutu là...
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
 
  ochunks = list(chunks)
  end = [chunk for chunk in re.split(pattern, end)
          if chunk != '']
  if len(chunks) >= 2 and chunks[-(len(end)+1)] != ' ' and chunks[-(len(end)+2)] != ' ' :
    if end != []:
      # drop end
      end.reverse()
      nend = []
      for x in end:
        if chunks[-1] == x:
          chunks.pop()
          nend.append(nullify(x))
      nend.reverse()
      end = nend
  else:
    try:
      if end[-1] == chunks[-1] and chunks[-1] == 'nt':
        feminine = False # OK this looks like fem but isnt (" cent$")
    except IndexError:
      pass
    end = []

  print('/'.join(chunks), file=sys.stderr)
  result = (maybe_sum(skip(chunks, 12, []), end), feminine)
  if result[0] == None and oend == 'ent':
    #super-ugly hack because ending 'ent' sometimes isn't dropped
    return (maybe_sum(skip(ochunks, 12, []), end), False)
  else:
    return result

while True:
  line = sys.stdin.readline()
  if not line:
    break
  if line.rstrip() != '':
    line = line.rstrip()
    print(align(parse(line)))
  else:
    print()

