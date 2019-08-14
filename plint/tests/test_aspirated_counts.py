from _pytest import unittest

from plint.tests.test_counts import Counts


class AspiratedCounts(Counts):

    def testBaudelaire1half(self):
        possible = self.runCount("funeste hélas", limit=4)
        self.assertTrue(self.achievesPossibility(possible, 4))
        possible = self.runCount("funeste hélas", limit=5)
        self.assertTrue(self.achievesPossibility(possible, 5))

if __name__ == "__main__":
    unittest.main()