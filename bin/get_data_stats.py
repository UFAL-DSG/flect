#!/usr/bin/env python
# coding=utf-8
#


"""
Getting data statistics from an ARFF file.

Usage: ./get_data_stats.py [-o train.arff] -s source_attr -t target_attr \
                           input.arff

Prints the percentages of data: 
    * excluding punctuation lemmas
    * non-base forms
    * forms unseen in the training data, if -o is set.

"""

from __future__ import unicode_literals
import sys
import getopt
import regex
from flect.dataset import DataSet
from flect.logf import log_info

__author__ = "Ondřej Dušek"
__date__ = "2013"


def print_feat(data, func, label):
    filtered = data[func]
    print('Data %s: %d (%2.2f)' %
          (label, len(filtered), float(len(filtered)) / len(data) * 100))


def get_stats(data_file, train_file, source_attr, target_attr):
    """\
    """
    data = DataSet()
    log_info('Loading data from %s...' % data_file)
    data.load_from_arff(data_file)
    print_feat(data, lambda a, b: True, 'total')
    print_feat(data, lambda _, i: not regex.match(r'^\p{P}', i[source_attr]),
               'excluding punctuation')
    print_feat(data, lambda _, i: i[source_attr].lower() != \
               i[target_attr].lower(), 'inflected forms')
    if train_file is not None:
        log_info('Loading known data from %s...' % train_file)
        train = DataSet()
        train.load_from_arff(train_file)
        known = {i[target_attr].lower() for i in train}
        print_feat(data, lambda _, i: not i[target_attr].lower() in known,
                   'unknown')


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def main():
    """\
    Main application entry.
    """
    opts, filenames = getopt.getopt(sys.argv[1:], 't:o:s:')
    train_file = None
    source_attr = None
    target_attr = None
    for opt, arg in opts:
        if opt == '-o':
            train_file = arg
        if opt == '-s':
            source_attr = arg
        if opt == '-t':
            target_attr = arg
    if len(filenames) != 1 or not source_attr or not target_attr:
        display_usage()
        sys.exit(1)
    get_stats(filenames[0], train_file, source_attr, target_attr)


if __name__ == '__main__':
    main()
