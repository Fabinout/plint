#!/usr/bin/python3 -u

from plint import localization, error, template, diaeresis
import sys
import argparse
import json


def run(ocontext=None, weight=None, offset=0, fmt="text"):
    is_ok = True
    f2 = None
    n_syllables = None
    if ocontext:
        f2 = open(ocontext, 'w')
    if weight:
        n_syllables = int(weight)
    should_end = False
    ret = []
    while True:
        line = sys.stdin.readline()
        if not line:
            should_end = True
            line = ""
        errors = template.check(line, f2, last=should_end, n_syllables=n_syllables, offset=offset)
        if errors:
            if not errors.isEmpty():
                is_ok = False
            if not errors.isEmpty():
                if fmt == "text":
                    print(errors.report(fmt=fmt), file=sys.stderr)
                elif fmt == "json":
                    ret.append(errors.report(fmt=fmt))
                else:
                    raise ValueError("bad format")
        if should_end:
            break
    if fmt == "json":
        print(json.dumps(ret, sort_keys=True, indent=4,
            separators={',', ': '}))
    return is_ok


def main():
    global template
    localization.init_locale()
    parser = argparse.ArgumentParser(
            description=_("Check poem on stdin according to a template"))
    parser.add_argument("template",
            help=_("the file containing the template for the input poem"),
            type=str)
    parser.add_argument("--format", type=str,
            help=_("error output format (text or json)"),
            choices = ["text", "json"],
            default="text")
    parser.add_argument("--diaeresis", type=str,
            help=_("diaeresis training: diaeresis file to use"),
            default="data/diaeresis.json")
    parser.add_argument("--ocontext", type=str,
            help=_("diaeresis training: output file where to write the contexts"),
            default=None)
    parser.add_argument("--weight", type=int,
            help=_("diaeresis training: fixed weight for a specific chunk"),
            default=None)
    parser.add_argument("--offset", type=int,
            help=_("diaeresis training: position of the specific chunk from the end"),
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
        print(_("Could not load template %s: %s") % (template_name, e.msg), file=sys.stderr)
        sys.exit(2)
    ok = run(ocontext=args.ocontext, weight=args.weight, offset=args.offset,
            fmt=args.format)
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
