from common import sure_end_fem

hemis_types = {
  'ok' : '/', # correct
  'bad' : '!', # something wrong
  'cut' : '?', # falls at the middle of a word
  'fem' : '\\', # preceding word ends by a mute e
  }


def check_spaces(align, pos):
  if pos >= len(align):
   # not enough syllabes for hemistiche
    return "bad"
  if align[pos] == ' ' or '-' in align[pos]:
    # word boundary here, so this is ok
    return "ok"
  # skip consonants
  if not isinstance(align[pos], tuple):
    return check_spaces(align, pos + 1)
  # hemistiche falls at the middle of a word
  return "cut"

def check_hemistiche(align, pos, hem):
  if pos >= len(align):
   # not enough syllabes for hemistiche
    return ("bad", pos)
  if hem == 0:
    # hemistiche should end here, check that this is a word boundary
    return (check_spaces(align, pos), pos)
  if hem < 0:
    # hemistiche falls at the middle of a vowel cluster
    return ("cut", pos)
  # skip consonants
  if not isinstance(align[pos], tuple):
    return check_hemistiche(align, pos +1, hem)
  # hemistiche is there, we should not have a feminine ending here
  if hem == 1:
    if pos + 1 >= len(align):
      # not enough syllabes for hemistiche
      return ("bad", pos)
    if ((align[pos][0] + align[pos+1]).rstrip() in sure_end_fem):
      # check that this isn't a one-syllabe wourd (which is allowed)
      ok = False
      for i in range(2):
        for j in ' -':
          if j in align[pos-i-1]:
            ok = True
      if not ok:
        # hemistiche ends in feminine
        return ("fem", pos)
  return check_hemistiche(align, pos+1, hem - align[pos][1])

def check_hemistiches(align, hems):
  """From a sorted list of distinct hemistiche positions, return a
  dictionary which maps each position to the status of this
  hemistiche"""
  
  result = {}
  pos = 0
  h2 = 0
  for h in hems:
    r, pos = check_hemistiche(align, pos, h-h2)
    h2 = h
    result[h] = r
  return result

