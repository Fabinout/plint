import unittest

from plint.tests.test_counts import Counts


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

    def testResplit1(self):
        f = self.runCount("k-fêt", limit=2)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 2)

    def testResplit1b(self):
        f = self.runCount("K-Fêt", limit=2)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 2)

    def testResplit2(self):
        f = self.runCount("sp-algèbre", limit=4)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 4)

    def testResplit3(self):
        f = self.runCount("k-raté k-way", limit=5)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 5)


if __name__ == "__main__":
    unittest.main()
