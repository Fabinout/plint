import unittest

from plint import template


class TemplateTest(unittest.TestCase):
    def testSingleHyphens(self):
        t = template.Template("12")
        text = "-"
        t.check(text)


if __name__ == "__main__":
    unittest.main()
