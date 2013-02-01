from common import sure_end_fem

hemis_types = {
  'ok': '/', # correct
  'bad': '!', # something wrong
  'cut': '?', # falls at the middle of a word
  'fem': '\\', # preceding word ends by a mute e
  'forbidden': '#', # last word of hemistiche cannot occur at end of hemistiche
  }

# these words are forbidden at hemistiche
forbidden_hemistiche = [
    "le",
    "la",
    ]

def align2str(align):
  return ''.join([x['text'] for x in align])

def check_spaces(align, pos):
  if pos >= len(align):
   # not enough syllabes for hemistiche
    return "bad"
  if align[pos]['text'] == ' ' or '-' in align[pos]['text'] or 'wordend' in align[pos]:
    # word boundary here, so this is ok
    return "ok"
  # skip consonants
  if not isinstance(align[pos], tuple):
    return check_spaces(align, pos + 1)
  # hemistiche falls at the middle of a word
  return "cut"

def check_hemistiche(align, pos, hem, check_end_hemistiche):
  if pos >= len(align):
   # not enough syllabes for hemistiche
    while len(align) <= pos:
      align.append({'original': "", 'text': ""})
    align[pos]['hemis'] = "bad"
    return pos
  if hem == 0:
    # hemistiche should end here, check that this is a word boundary
    if check_end_hemistiche:
      if (align2str(align[:pos+1]).split()[-1]) in forbidden_hemistiche:
        align[pos]['hemis'] = "forbidden"
        return pos
    align[pos]['hemis'] = check_spaces(align, pos)
    return pos
  if hem < 0:
    # hemistiche falls at the middle of a vowel cluster
    align[pos]['hemis'] = 'cut'
    return pos
  # skip consonants
  if not 'weight' in align[pos]:
    return check_hemistiche(align, pos +1, hem, check_end_hemistiche)
  # hemistiche is there, we should not have a feminine ending here
  if hem == 1:
    if pos + 1 >= len(align):
      # not enough syllabes for hemistiche
      align[pos]['hemis'] = 'bad'
      return pos
    if ((align[pos]['text'] + align[pos+1]['text']).rstrip() in sure_end_fem):
      # check that this isn't a one-syllabe wourd (which is allowed)
      ok = False
      for i in range(2):
        for j in ' -':
          if j in align[pos-i-1]:
            ok = True
      if not ok:
        # hemistiche ends in feminine
        align[pos]['hemis'] = 'fem'
        return pos
  return check_hemistiche(align, pos+1, hem - align[pos]['weight'],
      check_end_hemistiche)

def check_hemistiches(align, hems, check_end_hemistiche):
  """From a sorted list of distinct hemistiche positions, return a
  dictionary which maps each position to the status of this
  hemistiche"""

  pos = 0
  h2 = 0
  align, fem = align
  for h in hems:
    pos = check_hemistiche(align, pos, h-h2, check_end_hemistiche)
    h2 = h

