import unittest

import plint.pattern
from plint import verse, template


class BadChars(unittest.TestCase):
    def testBadAlone(self):
        v = verse.Verse("42", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertFalse(v.valid())

    def testBadAndGood(self):
        v = verse.Verse("bla h42 blah ", template.Template(), plint.pattern.Pattern("12"))
        v.parse()
        self.assertFalse(v.valid())

    def getWeight(self, align):
        return sum(x.get('weight', 0) for x in align)

    def achievesPossibility(self, aligns, target):
        for align in aligns:
            if self.getWeight(align) == target:
                return True
        return False


if __name__ == "__main__":
    unittest.main()