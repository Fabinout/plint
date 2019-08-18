#!/usr/bin/python3 -u

from plint import localization, error, template, diaeresis
import sys
import argparse


def run(ocontext=None, weight=None, offset=0):
    is_ok = True
    f2 = None
    n_syllables = None
    if ocontext:
        f2 = open(ocontext, 'w')
    if weight:
        n_syllables = int(weight)
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
    parser = argparse.ArgumentParser(
            description="Check poem on stdin according to a template")
    parser.add_argument("template",
            help="the file containing the template for the input poem",
            type=str)
    parser.add_argument("--diaeresis", type=str,
            help="diaeresis training: diaeresis file to use",
            default="../data/diaeresis.json")
    parser.add_argument("--ocontext", type=str,
            help="diaeresis training: output file where to write the contexts",
            default=None)
    parser.add_argument("--weight", type=int,
            help="diaeresis training: fixed weight for a specific chunk",
            default=None)
    parser.add_argument("--offset", type=int,
            help="diaeresis training: position of the specific chunk from the end",
            default=0)
    args = parser.parse_args()

    template_name = args.template
    diaeresis.set_diaeresis(args.diaeresis)
    f = open(template_name)
    x = f.read()
    f.close()
    try:
        template = template.Template(x)
    except error.TemplateLoadError as e:
        print("Could not load template %s: %s" % (template_name, e.msg), file=sys.stderr)
        sys.exit(2)
    ok = run(ocontext=args.ocontext, weight=args.weight, offset=args.offset)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
