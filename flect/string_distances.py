#!/usr/bin/env python
# coding=utf-8

"""
String distance helper functions and testing.

The main function here is edit_script(), which produces the edit script
given lemma and form.

Many functions use a matching function (match) and gap penalty scores (gap).
The only currently used settings for these functions are
match_levenshtein() and gap_levenshtein(), which are preset as defaults
in edit_script().

This module can be run as a test from the command line.
Usage: ./string_distances [-l] [-c] [-i] [-d]

-l = use Levenshtein distance (default)
-c = use distances tuned on Czech (obsolete)
-i = ignore-case
-d = detailed output

When run, type pairs of words on the command line, press Enter
and their edit scripts will be shown.

Exit with Ctrl-D.

Alternatively, input a pair of words on the command line to just
see their edit script.
"""

from __future__ import unicode_literals
import numpy as np
import getopt
import sys
import codecs
import re

__author__ = "Ondřej Dušek"
__date__ = "2013"


#
# match and gap functions
#

def match_levenshtein(s, t, i, j):
    """\
    Matching function according to Levenshtein distance.
    """
    return 1 if s[i] == t[j] else 0


def gap_levenshtein(s, i, cont):
    """\
    Gap penalty score according to Levenshtein distance.
    """
    return 0


def levenshtein_dist(s, t):
    """\
    Levenshtein distance function.
    """
    return max(len(s), len(t)) - sim_score(s, t, match_levenshtein,
                                           gap_levenshtein)


def match_cstest(s, t, i, j):
    """\
    Matching function designed to work better on Czech. Turns
    out to be unnecessary.
    """
    # TODO possibly make á-a + s-z (ismus), t-th etc. match
    if s[i] == t[j] and (i == 0 or j == 0 or s[i - 1] == t[j - 1]):
        # penalize matching ending of one word and beginning of the other
        if (float(i) / len(s) >= 0.6 and j == 0) or \
                (float(j) / len(t) >= 0.6 and i == 0):
            return -3
        # reward a continuing match
        return 2
    elif s[i] == t[j]:
        # penalize random matching in endings more
        if i >= len(s) - 2 or j >= len(t) - 2:
            return -3
        # penalize for start of a match
        return -1
    # penalize for start of a non-match
    elif s[i] != t[j] and (i == 0 or j == 0 or s[i - 1] == t[j - 1]):
        return -1
    # continuing a non-match -- neither penalize nor reward
    return 0


def gap_cstest(s, i, cont):
    """\
    Gap function to work nicely on Czech. Obsolete.
    """
    if cont:
        return 0
    return -2

#
# helper functions
#


class Dir:
    """\
    Direction to traverse diff matrixes (can be combined with "or").
    """
    UP = 1
    LEFT = 2
    DIAG = 4


def traverse_matrix(s, t, match, gap):
    """\
    Create a diff matrix according to given matching function and gap scores,
    return the matrix and the best path (according to matching function and gap
    scores).
    """
    H = np.zeros((len(s) + 1, len(t) + 1))
    path = np.zeros((len(s) + 1, len(t) + 1), dtype=int)
    for (j, tj) in enumerate(' ' + t):
        for (i, si) in enumerate('_' + s):
            # compute score for all directions
            (left, up, diag) = (float('-Inf'), float('-Inf'), float('-Inf'))
            if i > 0:  # look up
                gap_cont = path[i - 1, j] & Dir.UP != 0
                up = H[i - 1, j] + gap(s, i - 1, gap_cont)
            if j > 0:  # look left
                gap_cont = path[i, j - 1] & Dir.LEFT != 0
                left = H[i, j - 1] + gap(t, j - 1, gap_cont)
            if i > 0 and j > 0:  # look diagonally
                diag = H[i - 1, j - 1] + match(s, t, i - 1, j - 1)
            # find the best score and remember it along with the direction
            best_score = max(left, up, diag)
            if best_score > float('-Inf'):  # i.e. not upper-up corner
                H[i, j] = best_score
                if up == best_score:
                    path[i, j] |= Dir.UP
                if left == best_score:
                    path[i, j] |= Dir.LEFT
                if diag == best_score:
                    path[i, j] |= Dir.DIAG
    return H, path


def alignment(s, t, match, gap):
    """\
    Align two strings using the diff matrix (extract
    the alignment from the best traversal).
    """
    _, path = traverse_matrix(s, t, match, gap)
    ali = []
    i, j = len(s), len(t)
    while i > 0 or j > 0:
        if path[i, j] & Dir.DIAG:
            i -= 1
            j -= 1
            ali.append(s[i] + '=' + t[j])
        elif path[i, j] & Dir.UP:
            i -= 1
            ali.append('-' + s[i])
        else:
            assert path[i, j] & Dir.LEFT
            j -= 1
            ali.append('+' + t[j])
    ali.reverse()
    return ali


ADD_OPEN = '<'
ADD_CLOSE = '>'
REM_OPEN = '`'
REM_CLOSE = '\''


def merged_diff(s, t, match, gap):
    """\
    Create a merged diff of two strings using their alignment.
    The diff consists of common parts (unmarked), parts only present 
    in the first string (marked with `') and parts only present in the
    second string (marked with <>).
    """
    ali = alignment(s, t, match, gap)
    diff = ''
    add = ''
    rem = ''
    for char in ali + [' = ']:
        # same characters
        if len(char) == 3 and char[0] == char[2]:
            if rem:
                diff += REM_OPEN + rem + REM_CLOSE
            if add:
                diff += ADD_OPEN + add + ADD_CLOSE
            rem = ''
            add = ''
            diff += char[0]
        elif len(char) == 3:
            rem += char[0]
            add += char[2]
        elif char[0] == '-':
            rem += char[1]
        else:
            assert char[0] == '+'
            add += char[1]
    return diff[:-1]


#
# Main function: edit scripts
#

def edit_script(lemma, form, match=match_levenshtein, gap=gap_levenshtein):
    """\
    Compute the edit script of two strings.
    """
    # TODO there should be some escaping.
    diff = merged_diff(lemma, form, match, gap)
    front, mid, back = '', '', ''

    # no change
    if not re.search(r'[`\'<>]', diff):
        pass
    # total change
    elif re.match(r'^`', diff):
        back = '*' + form
    # just parts changed
    else:
        # changes in the back
        m = re.search(r'(?:`([^\']+)\')?(?:<([^>]+)>)?$', diff)
        if m:
            length = len(m.group(1) or '')
            add = m.group(2) or ''
            if length or add:
                back = '>' + str(length) + add
        # changes in the middle
        for m in re.finditer(r'(?:[^\'`<>])(?:`([^\']+)\'|<([^>]+)>){1,2}(?=[^\'`<>])', diff):
            orig, new = m.groups()
            if not orig and not new:
                continue
            orig = orig or ''
            new = new or ''
            tail = re.sub('([`\']|<[^>]*>)', '', diff[m.end():])
            orig = str(len(tail) + len(orig)) + ':' + str(len(orig))
            mid = (orig + '-' + new + ' ' + mid) if mid else (orig + '-' + new)
        # additions to the beginning
        m = re.search('^<([^>]*)>', diff)
        if m:
            front = '<' + m.group(1)
    # merge middle and back changes
    midback = ''
    if back and mid:
        midback = back + ',' + mid
    else:
        midback = back if back else mid
    # return the result
    return front, midback


def inv_edit_script(form, lemma, match=match_levenshtein, gap=gap_levenshtein):
    """\
    Compute the edit script of two strings.
    """
    # TODO there should be some escaping.
    diff = merged_diff(form, lemma, match, gap)
    front, mid, back = '', '', ''

    # no change
    if not re.search(r'[`\'<>]', diff):
        pass
    # total change
    elif re.match(r'(?:^`([^\']+)\')?<([^>]+)>', diff):
        back = '*' + lemma
    # just parts changed
    else:
        # changes in the back
        m = re.search(r'(?:`([^\']+)\')?(?:<([^>]+)>)?$', diff)
        if m:
            length = len(m.group(1) or '')
            add = m.group(2) or ''
            if length or add:
                back = '>' + str(length) + add
        # changes in the middle
        for m in re.finditer(r'(?:[^\'`<>])(?:`([^\']+)\'|<([^>]+)>){1,2}(?=[^\'`<>])', diff):
            orig, new = m.groups()
            if not orig and not new:
                continue
            orig = orig or ''
            new = new or ''
            tail = re.sub('([`\']|<[^>]*>)', '', diff[m.end():])
            orig = str(len(tail) + len(orig)) + ':' + str(len(orig))
            mid = (orig + '-' + new + ' ' + mid) if mid else (orig + '-' + new)
        # additions to the beginning
        m = re.search('^`([^\']*)\'', diff)
        if m:
            front = '<' + m.group(1)
    # merge middle and back changes
    midback = ''
    if back and mid:
        midback = back + ',' + mid
    else:
        midback = back if back else mid
    # return the result
    return front, midback


#
# Testing
#


def sim_score(s, t, match, gap):
    """\
    Compute similarity score of two strings according
    to their diff matrix.
    """
    H, _ = traverse_matrix(s, t, match, gap)
    return H[len(s), len(t)]


def compare(s, t, match, gap, details):
    """\
    Testing function.
    """
    out = codecs.getwriter('utf-8')(sys.stdout)
    if details:
        H, path = traverse_matrix(s, t, match, gap)
        print >> out, H
        print >> out, path
        print >> out, 'Similarity:', sim_score(s, t, match, gap)
        print >> out, 'Alignment:', alignment(s, t, match, gap)
    print >> out, 'Diff:', merged_diff(s, t, match, gap), 'Edit script:', \
            edit_script(s, t, match, gap)
    print >> out, 'Diff:', merged_diff(t, s, match, gap), \
            'Inverse edit script:', inv_edit_script(t, s, match, gap)


if __name__ == '__main__':
    # default
    gap = gap_levenshtein
    match = match_levenshtein
    details = False
    ignore_case = False
    # test
    opts, words = getopt.getopt(sys.argv[1:], 'lcdi')
    # set options
    for opt, arg in opts:
        if opt == '-l':
            gap = gap_levenshtein
            match = match_levenshtein
        elif opt == '-c':
            gap = gap_cstest
            match = match_cstest
        elif opt == '-i':
            ignore_case = True
        elif opt == '-d':
            details = True
    # run the test
    if len(words) == 2:
        s = codecs.decode(words[0], 'utf-8')
        t = codecs.decode(words[1], 'utf-8')
        if ignore_case:
            s = s.lower()
            t = t.lower()
        compare(s, t, match, gap, details)
    else:
        while True:
            line = raw_input()
            line = codecs.decode(line.strip(), 'utf-8')
            if not line:
                break
            if ignore_case:
                line = line.lower()
            s, t = line.split(None, 1)
            compare(s, t, match, gap, details)
