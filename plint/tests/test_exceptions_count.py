from _pytest import unittest

from plint.tests.test_counts import Counts


class ExceptionCounts(Counts):
    def testPays(self):
        f = self.runCount("pays abbaye alcoyle", limit=8)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 8)

    def testPorteAvions(self):
        f = self.runCount("porte-avions porte-avions", limit=8)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 8)

    def testSainteHelene(self):
        # from "Les Trophées", José-Maria de Heredia
        text = "Le navire, doublant le cap de Sainte-Hélène,"
        f = self.runCount(text, limit=12)
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 12)

    def testHemisticheElide(self):
        text1 = "Tatata ta verre un tata tatata"
        text2 = "Tatata tata verre un tata tatata"
        f1 = self.runCount(text1, limit=12, hemistiches=[6])
        self.assertEqual(0, len(f1))
        f2 = self.runCount(text2, limit=12, hemistiches=[6])
        self.assertEqual(1, len(f2))
        self.assertEqual(self.getWeight(f2[0]), 12)

    def testConcluera(self):
        text = "Concluera l'examen. Venez, je vous invite"
        f = self.runCount(text, limit=12, hemistiches=[6])
        self.assertEqual(1, len(f))
        self.assertEqual(self.getWeight(f[0]), 12)

if __name__ == "__main__":
    unittest.main()
