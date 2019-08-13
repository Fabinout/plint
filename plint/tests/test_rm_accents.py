import unittest

from plint import common


class RmAccents(unittest.TestCase):
    def testSimple(self):
        text = "déjà"
        v = common.strip_accents(text)
        self.assertEqual(v, "deja")


if __name__ == "__main__":
    unittest.main()
