#!/usr/bin/python3

import template
import verse
import unittest
from pprint import pprint

class SanityCheck(unittest.TestCase):
  def testSimple(self):
    text = "Hello World!!  This is a test"
    v = verse.Verse(text, template.Template(), template.Pattern("12"))
    v.parse()
    self.assertEqual(text, v.line)

  def testComplex(self):
    text = "Aye AYAYE   aye  gue que geque AYAYAY a prt   sncf bbbéé"
    v = verse.Verse(text, template.Template(), template.Pattern("12"))
    v.parse()
    self.assertEqual(text, v.line)

  def testLeadingSpace(self):
    text = " a"
    v = verse.Verse(text, template.Template(), template.Pattern("12"))
    v.parse()
    self.assertEqual(text, v.line)

class Eliminate(unittest.TestCase):
  def testEliminateOneGue(self):
    text = "gue"
    v = verse.Verse(text, template.Template(), template.Pattern("12"))
    v.parse()
    c = ''.join([x['text'] for x in v.chunks])
    self.assertFalse("gue" in c)

  def testEliminateGue(self):
    text = "gue gue GUE ogues longuement la guerre"
    v = verse.Verse(text, template.Template(), template.Pattern("12"))
    v.parse()
    c = ''.join([x['text'] for x in v.chunks])
    self.assertFalse("gue" in c)

class BadChars(unittest.TestCase):
  def testBadAlone(self):
    v = verse.Verse("42", template.Template(), template.Pattern("12"))
    v.parse()
    self.assertFalse(v.valid())

  def testBadAndGood(self):
    v = verse.Verse("bla h42 blah ", template.Template(), template.Pattern("12"))
    v.parse()
    self.assertFalse(v.valid())


  def getWeight(self, align):
    return sum(x.get('weight', 0) for x in align)

  def achievesPossibility(self, aligns, target):
    for align in aligns:
      if self.getWeight(align) == target:
        return True
    return False

class Counts(unittest.TestCase):
  def runCount(self, text, limit=12):
    v = verse.Verse(text, template.Template(), template.Pattern(str(limit)))
    v.parse()
    return v.possible

  def getWeight(self, align):
    return sum(x.get('weight', 0) for x in align)

  def achievesPossibility(self, aligns, target):
    for align in aligns:
      if self.getWeight(align) == target:
        return True
    return False

class SigleCounts(Counts):
  def testW(self):
    f = self.runCount("W", limit=3)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 3)

  def testB(self):
    f = self.runCount("b", limit=1)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 1)

  def testMulti(self):
    f = self.runCount("SNCF WWW", limit=13)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 13)

class SimpleCounts(Counts):
  def testTrivialMonovoc(self):
    f = self.runCount("Ba", limit=1)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 1)

  def testMonovoc(self):
    f = self.runCount("Babababa", limit=4)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 4)

class AspiratedCounts(Counts):
  def testBaudelaire1half(self):
    possible = self.runCount("funeste hélas", limit=4)
    self.assertTrue(self.achievesPossibility(possible, 4))
    possible = self.runCount("funeste hélas", limit=5)
    self.assertTrue(self.achievesPossibility(possible, 5))

class RealCounts(Counts):
  half1 = "Je veux, pour composer"
  half2 = " chastement mes églogues,"
  verse = "Allez. Après cela direz-vous que je l’aime ?"

  def testBaudelaire1half(self):
    f = self.runCount(self.half1, limit=6)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 6)

  def testBaudelaire1half2(self):
    f = self.runCount(self.half2, limit=6)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 6)

  def testBaudelaire1(self):
    f = self.runCount(self.half1 + self.half2, limit=12)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 12)

  def testAndromaque(self):
    f = self.runCount(self.verse, limit=12)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 12)

class BadCounts(Counts):
  def testBad(self):
    f = self.runCount("Cela cela", limit=5)
    self.assertEqual(0, len(f))

class PoemCounts(Counts):
  v1 = "Qui berce longuement notre esprit enchanté"
  v2 = "Qu'avez-vous ? Je n'ai rien. Mais... Je n'ai rien, vous dis-je,"
  v3 = "Princes, toute h mer est de vaisseaux couverte,"
  v4 = "Souvent le car qui l'a ne le sait pas lui-même"
  def testV1(self):
    possible = self.runCount(self.v1, limit=12)
    self.assertTrue(self.achievesPossibility(possible, 12))
  def testV2(self):
    possible = self.runCount(self.v2, limit=12)
    self.assertTrue(self.achievesPossibility(possible, 12))
  def testV3(self):
    possible = self.runCount(self.v3, limit=12)
    self.assertTrue(self.achievesPossibility(possible, 12))
  def testV4(self):
    possible = self.runCount(self.v3, limit="6/6")
    self.assertTrue(self.achievesPossibility(possible, 12))

if __name__ == "__main__":
    unittest.main()

