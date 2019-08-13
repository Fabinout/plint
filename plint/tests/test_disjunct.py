import unittest

from plint.tests.test_counts import Counts


class Disjunct(Counts):
    # inspired by Grevisse, Le Bon usage, 14th ed., paragraphs 49-50
    d = {
        "hiérarchie": 4,
        "yeux": 1,
        "yeuse": 1,
        "yodel": 3,
        "yacht": 2,
        "York": 1,
        "yole": 2,
        "Yourcenar": 4,
        "Yvelines": 3,
        "Ypres": 1,
        "ypérite": 3,
        "Ysaÿe": 3,
        "Ionesco": 4,
        "Yahvé": 3,
        "Yungfrau": 3,
        "yodler": 3,
        "oui": 2,
        "ouïe": 2,
        "ouïr": 2,
        "ouest": 1,
        "Ouagadougou": 6,
        "oisif": 2,
        "huis": 2,
        "huit": 2,
        "huissier": 2,
        "uhlan": 3,
        "ululer": 4,
        "ululement": 5,
        "onze": 2,
        "onzième": 3,
        # both are possible for 'un' and 'une'
        "Un": 2,
        "un": 2,
        "Une": 2,
        "une": 1,
        # too weird to figure out correct counts in poems
        # "Yolande"
        # "ouistiti"
    }

    def testDisjunct(self):
        for k in self.d.keys():
            v = self.d[k] + 1
            vv = "belle " + k
            possible = self.runCount(vv, limit=v)
            self.assertTrue(self.achievesPossibility(possible, v))


if __name__ == "__main__":
    unittest.main()
