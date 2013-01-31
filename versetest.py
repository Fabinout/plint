#!/usr/bin/python3

import verse
import unittest

class SanityCheck(unittest.TestCase):
  def testSimple(self):
    text = "Hello World!!  This is a test"
    v = verse.Verse(text)
    self.assertEqual(text, v.text)

  def testComplex(self):
    text = "Aye AYAYE   aye  gue que geque AYAYAY a prt   sncf bbbéé"
    v = verse.Verse(text)
    self.assertEqual(text, v.text)

  def testLeadingSpace(self):
    text = " a"
    v = verse.Verse(text)
    self.assertEqual(text, v.text)

class Eliminate(unittest.TestCase):
  def testEliminateGue(self):
    text = "gue gue GUE ogues"
    v = verse.Verse(text)
    c = [x['text'] for x in v.chunks]
    self.assertEqual("ue" in c, False)

class Counts(unittest.TestCase):
  def runCount(self, text, limit=12, diaeresis="permissive"):
    v = verse.Verse(text)
    return v.fits(limit, diaeresis)

  def getWeight(self, align):
    return sum(x.get('weight', 0) for x in align)

class SimpleCounts(Counts):
  def testTrivialMonovoc(self):
    f = self.runCount("Ba")
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 1)

  def testMonovoc(self):
    f = self.runCount("Babababa")
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 4)

class RealCounts(Counts):
  half1 = "Je veux, pour composer"
  half2 = " chastement mes églogues,"
  def testBaudelaire1half(self):
    f = self.runCount(self.half1)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 6)

  def testBaudelaire1half2(self):
    f = self.runCount(self.half2)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 6)

  def testBaudelaire1(self):
    f = self.runCount(self.half1 + self.half2)
    self.assertEqual(1, len(f))
    self.assertEqual(self.getWeight(f[0]), 12)

if __name__ == "__main__":
    unittest.main()

