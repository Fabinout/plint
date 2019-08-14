import unittest

from plint.tests.test_counts import Counts


class PoemCounts(Counts):
    v1 = "Qui berce longuement notre esprit enchanté"
    v2 = "Qu'avez-vous ? Je n'ai rien. Mais... Je n'ai rien, vous dis-je,"
    v3 = "Princes, toute h mer est de vaisseaux couverte,"
    v4 = "Souvent le car qui l'a ne le sait pas lui-même"
    v5 = "Quand nos États vengés jouiront de mes soins"

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
        possible = self.runCount(self.v4, limit="6/6")
        self.assertTrue(self.achievesPossibility(possible, 12))

    def testV5(self):
        possible = self.runCount(self.v5, limit="6/6")
        self.assertTrue(self.achievesPossibility(possible, 12))

if __name__ == "__main__":
    unittest.main()
