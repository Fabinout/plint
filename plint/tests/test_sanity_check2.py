import unittest

import plint.pattern
from plint import verse, template


class SanityCheck2(unittest.TestCase):
    def testSimple(self):
        text = "Patati patata patata tata vies"
        v = verse.Verse(text, template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        gend = v.genders()
        self.assertEqual(1, len(gend))
        self.assertEqual('F', next(iter(gend)))


if __name__ == "__main__":
    unittest.main()
