import unittest

import plint.pattern
from plint import verse, template


class Genders(unittest.TestCase):
    def testSingleSyllJe(self):
        text = "Patati patata patatatah où suis-je"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('F', next(iter(gend)))

    def testSingleSyllJeBis(self):
        text = "Patati patata patatah la verrai-je"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('F', next(iter(gend)))

    def testSingleSyllLe(self):
        text = "Patati patata patatata prends-le"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('F', next(iter(gend)))

    def testSingleSyllCe(self):
        text = "Patati patata patatata mais qu'est-ce"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('F', next(iter(gend)))

    def testSingleSyllHyphen(self):
        text = "Patati patata patata mange-les"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('M', next(iter(gend)))

    def testSingleSyllNoHyphen(self):
        text = "Patati patata patata mange les"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertTrue(v.valid())
        self.assertEqual(1, len(gend))
        self.assertEqual('M', next(iter(gend)))


if __name__ == "__main__":
    unittest.main()
