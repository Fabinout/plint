import unittest

from plint import verse, template


class Eliminate(unittest.TestCase):
    def testEliminateOneGue(self):
        text = "gue"
        v = verse.Verse(text, template.Template(), template.Pattern("12"))
        v.parse()
        c = ''.join([x['text'] for x in v.chunks])
        self.assertFalse("gue" in c)

    def testEliminateGue(self):
        text = "gue gue GUE ogues longuement la guerre"
        v = verse.Verse(text, template.Template(), template.Pattern("12"))
        v.parse()
        c = ''.join([x['text'] for x in v.chunks])
        self.assertFalse("gue" in c)

if __name__ == "__main__":
    unittest.main()