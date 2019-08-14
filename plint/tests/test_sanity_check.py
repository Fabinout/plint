import unittest

import plint.pattern
from plint import diaeresis, verse, template, common


class SanityCheck(unittest.TestCase):

    def testSimple(self):
        text = "Hello World!!  This is a test_data"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertEqual(text, v.line)

    def testComplex(self):
        text = "Aye AYAYE   aye  gue que geque AYAYAY a prt   sncf bbbéé"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertEqual(text, v.line)

    def testLeadingSpace(self):
        text = " a"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertEqual(text, v.line)

    def testLeadingSpaceHyphenVowel(self):
        text = " -a"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertEqual(text, v.line)

    def testLeadingSpaceHyphenConsonant(self):
        text = " -c"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertEqual(text, v.line)

    def testLoneHyphens(self):
        text = " - - -- --   - -  - --"
        self.assertEqual(common.normalize(text), "")

    def testOnlyHyphens(self):
        text = "-----"
        self.assertEqual(common.normalize(text), "")


if __name__ == "__main__":
    unittest.main()
