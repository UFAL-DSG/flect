#!/usr/bin/env python
# coding=utf-8
#


"""
Pairwise bootstrap comparison of two systems

Usage:
./bootstrap_compare.py [-i] -g gold_attr -p predicted_attr system1-output.arff system2-output.arff
"""

from __future__ import unicode_literals

from flect.dataset import DataSet, Attribute
from flect.logf import log_info
import getopt
import sys
import numpy.random as rnd

def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def pairwise_bootstrap(file1, file2, gold_attr, pred_attr, cmp_func, iters):
    d1, d2 = DataSet(), DataSet()
    log_info('Loading File1: %s' % file1)
    d1.load_from_arff(file1)
    log_info('Loading File2: %s' % file2)
    d2.load_from_arff(file2)
    gold = d1.attrib_as_vect(gold_attr)
    p1 = d1.attrib_as_vect(pred_attr)
    p2 = d2.attrib_as_vect(pred_attr)
    p1_better, p2_better, ties = 0, 0, 0
    for i in xrange(iters):
        sample = rnd.randint(0, len(gold), len(gold))
        s_p1_good = sum(1 if cmp_func(gold[i], p1[i]) else 0 for i in sample)
        s_p2_good = sum(1 if cmp_func(gold[i], p2[i]) else 0 for i in sample)
        log_info('Round %d: File1 - %2.2f vs. File2 - %2.2f' %
                 (i, float(s_p1_good) / len(gold) * 100,
                  float(s_p2_good) / len(gold) * 100))
        if s_p1_good > s_p2_good:
            p1_better += 1
        elif s_p2_good > s_p1_good:
            p2_better += 1
        else:
            ties += 1
    print ('File1 better: %d (%2.2f) | File2 better: %d (%2.2f) |' +
           ' ties: %d (%2.2f)') % (p1_better, float(p1_better) / iters * 100,
                                   p2_better, float(p2_better) / iters * 100,
                                   ties, float(ties) / iters * 100,)


def main():
    """\
    Main application entry: parse command line and run the test.
    """
    rnd.seed(12061985)
    opts, filenames = getopt.getopt(sys.argv[1:], 'g:p:in:')
    show_help = False
    gold = None
    predicted = None 
    ignore_case = False
    iters = 1000
    for opt, arg in opts:
        if opt == '-g':
            gold = arg
        elif opt == '-p':
            predicted = arg
        elif opt == '-i':
            ignore_case = True
        elif opt == '-n':
            iters = int(arg)
    # display help and exit
    if len(filenames) != 2 or not gold or not predicted or show_help:
        display_usage()
        sys.exit(1)
    if ignore_case:
        cmp_func = lambda a, b: a.lower() == b.lower()
    else:
        cmp_func = lambda a, b: a == b
    pairwise_bootstrap(filenames[0], filenames[1], gold, predicted,
                       cmp_func, iters)


if __name__ == '__main__':
    main()
