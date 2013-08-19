#!/usr/bin/env python
# coding=utf-8
#

"""
Select erroneously classified examples and save them to a separate data set.

Usage:
./select_errors.py [-i] -g gold_attr [-p predict_attr] in.arff out.arff

Predicted attribute name defaults to 'PREDICTED'.
"""

from __future__ import unicode_literals

from lib.dataset import DataSet, Attribute
from lib.logf import log_info
import getopt
import sys


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def main():
    """\
    Main application entry: parse command line and run the test.
    """
    opts, filenames = getopt.getopt(sys.argv[1:], 'g:p:ai')
    show_help = False
    annot_errors = False
    gold = None
    predicted = 'PREDICTED'
    ignore_case = False
    for opt, arg in opts:
        if opt == '-g':
            gold = arg
        elif opt == '-p':
            predicted = arg
        elif opt == '-a':
            annot_errors = True
        elif opt == '-i':
            ignore_case = True
    # display help and exit
    if len(filenames) != 2 or not gold or show_help:
        display_usage()
        sys.exit(1)
    # run the training
    filename_in, filename_out = filenames
    data = DataSet()
    log_info('Loading data: ' + filename_in)
    data.load_from_arff(filename_in)
    if ignore_case:
        cmp_func = lambda a, b: a.lower() != b.lower()
    else:
        cmp_func = lambda a, b: a != b
    if annot_errors:
        log_info('Annotating errors...')
        err_ind = ['ERR' if cmp_func(i[gold], i[predicted]) else ''
                   for i in data]
        data.add_attrib(Attribute('ERROR_IND', 'string'), err_ind)
    else:
        log_info('Selecting errors...')
        data = data[lambda _, i: cmp_func(i[gold], i[predicted])]
    log_info('Saving data: ' + filename_out)
    data.save_to_arff(filename_out)


if __name__ == '__main__':
    main()
