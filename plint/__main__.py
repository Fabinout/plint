#!/usr/bin/python3 -u

from plint import localization, error, template, diaeresis
import sys


def run():
    is_ok = True
    f2 = None
    n_syllables = None
    offset = 0
    if len(sys.argv) >= 4:
        f2 = open(sys.argv[3], 'w')
    if len(sys.argv) >= 5:
        n_syllables = int(sys.argv[4])
    if len(sys.argv) == 6:
        offset = int(sys.argv[5])
    should_end = False
    while True:
        line = sys.stdin.readline()
        if not line:
            should_end = True
            line = ""
        errors = template.check(line, f2, last=should_end, n_syllables=n_syllables, offset=offset)
        if errors:
            print(errors.report(), file=sys.stderr)
            is_ok = False
        if should_end:
            break
    return is_ok


def main():
    global template
    localization.init_locale()
    if len(sys.argv) < 2 or len(sys.argv) > 6:
        print("Usage: %s TEMPLATE [DFILE [OCONTEXT [NSYL [OFFSET]]]]" % sys.argv[0],
              file=sys.stderr)
        print("Check stdin according to TEMPLATE, report errors on stdout",
              file=sys.stderr)
        print("For internal use:",
              file=sys.stderr)
        print("DFILE is the diaeresis file, OCONTEXT is the context output file",
              file=sys.stderr)
        print("NSYL is the assigned weight to the last chunk (diaeresis training)",
              file=sys.stderr)
        print("OFFSET is to add after the last chunk (diaeresis training)",
              file=sys.stderr)
        sys.exit(2)
    template_name = sys.argv[1]
    if len(sys.argv) > 2:
        diaeresis_name = sys.argv[2]
    else:
        diaeresis_name = "../data/diaeresis.json"
    diaeresis.set_diaeresis(diaeresis_name)
    f = open(template_name)
    x = f.read()
    f.close()
    try:
        template = template.Template(x)
    except error.TemplateLoadError as e:
        print("Could not load template %s: %s" % (template_name, e.msg), file=sys.stderr)
        sys.exit(2)
    ok = run()
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
