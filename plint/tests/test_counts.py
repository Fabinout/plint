import unittest

from plint import verse, template


class Counts(unittest.TestCase):

    def runCount(self, text, limit=12, hemistiches=None):
        v = verse.Verse(text, template.Template(), template.Pattern(str(limit), hemistiches=hemistiches))
        v.parse()
        return v.possible

    def getWeight(self, align):
        print([x.weight for x in align])
        print(sum([x.weight or 0 for x in align]))
        return sum([x.weight or 0 for x in align])

    def achievesPossibility(self, aligns, target):
        for align in aligns:
            if self.getWeight(align) == target:
                return True
        return False


if __name__ == "__main__":
    unittest.main()
