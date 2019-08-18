#!/usr/bin/perl

# This file fixes Lexique's pronunciation info from the home-grown
# format described in
# http://www.lexique.org/outils/Manuel_Lexique.htm#_Toc108519023 to a
# variation of the X-SAMPA standard


sub subst {
  my $a = shift;
  # substitutions to apply
  my @s = (
    ['§', '$'],
    ['@', '#'],
    ['1', '('],
    ['5', ')'],
    ['°', '@'],
    ['3', '@'],
    ['H', '8'],
    ['N', 'J'],
    ['G', 'N'],
  );
  foreach my $t (@s) {
    $a =~ s/${$t}[0]/${$t}[1]/g
  }
  return $a;
}

while (<>) {
  chop;
  if (/^([^\t]*)\t([^\t]*)(.*)$/) {
    my $repl = subst $2;
    print "$1\t$repl$3\n";
  } else {
    die "Cannot process line: $_\n";
  }
}

