import unittest

import plint.pattern
from plint import verse, template


class Hiatus(unittest.TestCase):
    def testBadVowel(self):
        v = verse.Verse("patati patata patata arbrisseau", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertFalse(v.valid())

    def testBadUnaspirated(self):
        v = verse.Verse("patati patata patata hirondelle", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertFalse(v.valid())

    def testGoodAspirated(self):
        v = verse.Verse("patati patata patata tata hache", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertTrue(v.valid())

    def testGoodConsonant(self):
        v = verse.Verse("patati patata patatah arbrisseau", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertTrue(v.valid())

    def testGoodMuteE(self):
        v = verse.Verse("patati patata patatue arbrisseau", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertTrue(v.valid())

    def testBadEt(self):
        v = verse.Verse("patati patata patata et avant", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertFalse(v.valid())


if __name__ == "__main__":
    unittest.main()
