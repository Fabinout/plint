#!/usr/bin/perl

use HTML::Entities;

my $actor;
my $indent;
my $first = 1;
my %actions;

while (<STDIN>) {
  chop;
  if (/^<([^>]*)> \/me plint (.*)$/) {
    if ($1 ne $actor) {
      $actions{$1} = $2;
    } else {
      my $did = encode_entities($2, '<>&"');
      print "</p>\n";
      print "<p class=\"did\">Il $did</p>\n";
      print "<p class=\"speech\">\n";
    }
  } elsif (/^<([^>]*)> (.*)$/) {
    if ($1 ne $actor) {
      print "</p>\n" unless $first;
      $first = 0;
      $actor = $1;
      my $eactor = encode_entities($actor, '<>&"');
      print "<p class=\"actor\"><span class=\"actor\">$eactor</span>";
      if (exists $actions{$1}) {
        my $did = encode_entities($actions{$1}, '<>&"');
        print ", <span class=\"did\">$did</span>";
        delete $actions{$1};
      }
      print "</p>\n";
      print "<p class=\"speech\">\n";
    }
    my $rawverse = $2;
    if ($2 =~ m/^ *\.\.\./) {
      $indent++;
    } else {
      $indent = 0;
    }
    my $verse = encode_entities($rawverse, '<>&"');
    if ($indent) {
      my $offset = 4 * $indent . "em";
      print "<span style=\"margin-left: $offset;\">$verse</span><br />\n";
    } else {
      print "$verse<br />\n";
    }
  }
}

print "</p>\n" unless $first;
