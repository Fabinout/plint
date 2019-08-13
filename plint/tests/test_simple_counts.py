import unittest

from plint.tests.test_counts import Counts


class SimpleCounts(Counts):
    def testTrivialMonovoc(self):
        f = self.runCount("Ba", limit=1)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 1)

    def testMonovoc(self):
        f = self.runCount("Babababa", limit=4)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 4)


if __name__ == "__main__":
    unittest.main()
