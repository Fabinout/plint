import unittest

from plint.template import Template


class TestRhyme(unittest.TestCase):

    def _test_rimes(self):
        template = Template("""6/6 A !X
6/6 A !X""")
        text = """Je te fais plus parfait mille fois que tu n’es :
        Ton feu ne peut aller au point où je le mets ;"""
        should_end = False
        for line in text.split("\n"):
            errors = template.check(line, None, last=should_end, n_syllables=None, offset=0)
            self.assertIsNone(errors, errors.report() if errors is not None else "OK")
        should_end = True
        line = ""
        errors = template.check(line, None, last=should_end, n_syllables=None, offset=0)
        self.assertIsNone(errors)


if __name__ == '__main__':
    unittest.main()
