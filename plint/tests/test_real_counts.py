import unittest

from plint.tests.test_counts import Counts


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


if __name__ == "__main__":
    unittest.main()