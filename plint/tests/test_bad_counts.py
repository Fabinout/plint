from _pytest import unittest

from plint.tests.test_counts import Counts


class BadCounts(Counts):
    def testBad(self):
        f = self.runCount("Cela cela", limit=5)
        self.assertEqual(0, len(f))

if __name__ == "__main__":
    unittest.main()