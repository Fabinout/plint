#!/usr/bin/python3
# -*- coding: utf-8

import os
from common import normalize
from nltk.tag.stanford import POSTagger
from pprint import pprint

def postag(l):
  l2 = []
  idxes = []
  for (b, w, a) in l:
    for i, x in enumerate([b, w, a]):
      if (i == 1):
       idxes.append(len(l2))
      if (len(x.strip()) > 0) or i == 1:
        l2.append(x)
  tags = st.tag(l2)
  l3 = []
  for idx in idxes:
    l3.append(tags[idx][1])
  #pprint(l)
  #pprint(tags)
  #pprint(l3)
  return l3

os.environ['JAVAHOME'] = '/usr/bin'
# depends on http://nltk.org/nltk3-alpha/ and stanfond pos tagger
# st = POSTagger('stanford-postagger-full-2013-11-12/models/english-bidirectional-distsim.tagger', 'stanford-postagger-full-2013-11-12/stanford-postagger.jar')
st = POSTagger('stanford-postagger-full-2013-11-12/models/french.tagger',
'stanford-postagger-full-2013-11-12/stanford-postagger.jar', encoding='utf-8')
x = "Rome à qui vient ton bras d' immoler mon amant".split()
print( st.tag(x))
#x = "L' autre mime en riant l' infirme qui volait".split()
#print( st.tag(x))
#x = "Quelle est la vitesse aérienne d' une hirondelle à vide ?".split()
#x = "La souffleuse, , , l'hindoue, elle a lentement péché, l' autre l autre l'autre la belle lésine,".split()
#print( st.tag('What is the airspeed of an unladen swallow ?'.split()))
