#!/usr/bin/env python3

import re
import sys
import unicodedata
import aspire
from pprint import pprint

consonants = "[bcçdfghjklmnpqrstvwxz*]"
vowels = 'aeiouyœæ'

# TODO -ment at hemistiche
# TODO diaresis
# TODO rhymes
sure_end_fem = ['es', 'e']
end_fem = sure_end_fem + ['ent']

count_two = ['aë', 'aï', 'ao', 'ea', 'éa', 'éi', 'éo', 'éu', 'êa', 'êi',
'êo', 'êu', 'èa', 'èi', 'èo', 'èu', 'oa', 'ua', 'oya']
can_count_two = ['ia', 'ieue', 'ié', 'iées', 'io', 'iu', 'iue', 'ue']

# http://stackoverflow.com/questions/517923/what-is-the-best-way-to-remove-accents-in-a-python-unicode-string
def strip_accents(s):
  return ''.join(
      (c for c in unicodedata.normalize('NFD', s)
      if unicodedata.category(c) != 'Mn'))

def norm_spaces(text):
  return re.sub("\s+", ' ', text)

def rm_punct(text):
  text = re.sub("'", '', text)
  pattern = re.compile('[^\w ]', re.UNICODE)
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

def fit(chunks, left):
  if left == 7 and (len(chunks) < 2 or chunks[0] + chunks[1] in
      sure_end_fem):
    # no feminine at hemistiche
    print ("refuse hemistiche")
    return None
  weights = possible_weights(chunks[0])
  for weight in weights:
    nleft = left - weight
    #print("Take %s with weight %d, left %d" % (chunks[0], weight,
      #nleft))
    result = maybe_sum([(chunks[0], weight)], skip(chunks[1:], nleft,
      nleft == 6))
    if result != None:
      return result
    #print ("FAIL!")
  return None

def maybe_sum(a, b):
  if b == None or a == None:
    return None
  else:
    return a + b
  
def skip(chunks, left, expect_space=False):
  result = []
  chunks = list(chunks)
  if len(chunks) > 0 and not is_vowels(chunks[0]):
    return maybe_sum([chunks[0]], skip(chunks[1:], left, expect_space
      and not chunks[0] == ' '))
  if len(chunks) == 0:
    if left == 0:
      #print("OK")
      return []
    else:
      #print("out of chunks")
      return None
  if expect_space:
    # we wanted a space and haven't got it, fail
    #print("wanted space")
    return None
  return fit(chunks, left)

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
  end = get_feminine(text)
  feminine = end != ''
  text = re.sub("qu", 'q', text)
  words = text.split(' ')
  words = [annotate_aspirated(word) for word in words]
  pattern = re.compile('('+consonants+'*)', re.UNICODE)
  for i in range(len(words)):
    words[i] = re.split(pattern, words[i])
    words[i] = [chunk for chunk in words[i] if chunk != '']
    nwords = []
    for chunk in words[i]:
      if 'y' not in chunk or len(chunk) == 1:
        nwords.append(chunk)
      else:
        a = chunk.split('y')
        nwords.append(a[0])
        nwords.append('Y')
        nwords.append(a[1])
    words[i] = nwords
    if i > 0:
      if count_vowel_chunks(words[i-1]) > 1:
        if words[i-1][-1] == 'e' and is_vowels(words[i][0], True):
          words[i-1].pop(-1)
          words[i-1][-1] = words[i-1][-1]+"'"
  for word in words:
    word.append(' ')
  chunks = sum(words, [])[:-1]
  
  end = [chunk for chunk in re.split(pattern, end)
          if chunk != '']
  if chunks[-(len(end)+1)] != ' ' and chunks[-(len(end)+2)] != ' ' :
    if end != []:
      # drop end
      end.reverse()
      nend = []
      for x in end:
        #print (chunks[-1])
        if chunks[-1] == x:
          chunks.pop()
          nend.append(nullify(x))
      nend.reverse()
      end = nend
  else:
    end = []

  #pprint(chunks)
  return (maybe_sum(skip(chunks, 12), end), feminine)

while True:
  line = sys.stdin.readline()
  if not line:
    break
  if line.rstrip() != '':
    line = line.rstrip()
    print(align(parse(line)))
  else:
    print()

