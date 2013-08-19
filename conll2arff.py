#!/usr/bin/env python
# coding=utf-8

"""
Converting CoNLL 2009 format data sets to ARFF.

Usage: ./conll2arff.py [-c X] [-f X] [-n] input.conll output.arff

-c X = Use CPOSes X characters long

-f X = Expect X POS features (so that the values of non-present
        features are assumed to be defined and empty)

-n   = Use POS feature names (from the data, if they contain them)
        instead of numbers.
"""


from __future__ import unicode_literals

import getopt
import sys
import lib.string_distances as strdist
from lib.varutil import file_stream
from lib.dataset import DataSet, Attribute

__author__ = "Ondřej Dušek"
__date__ = "2013"


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def convert(in_file, out_file, feat_no, use_feat_names, cpos_chars):
    """\
    This does the conversion to ARFF.
    """
    fh_in = file_stream(in_file)
    
    buf = []
    sent_id = 1
    word_id = 1

    for line in fh_in:
        line = line.rstrip('\r\n')
        if not line:
            sent_id += 1
            word_id = 1
            continue
        # split the CoNLL format, removing unwanted stuff
        _, form, lemma, _, pos, _, feat, _ = line.split('\t', 7)
        # copy attributes
        inst = {
                'Form': form, 'Lemma': lemma, 'Tag_POS': pos,
                'word_id': word_id, 'sent_id': in_file + '-' + str(sent_id)
               }
        # computing form-lemma diff (edit script)
        escr_front, escr_midback = strdist.edit_script(lemma, form,
                strdist.match_levenshtein, strdist.gap_levenshtein)
        inst['LemmaFormDiff_Front'] = escr_front
        inst['LemmaFormDiff_Back'] = escr_midback
        # lemma suffixes
        for i in xrange(1, 9):
            inst['LemmaSuff_' + str(i)] = lemma[-i:]
        # coarse POS
        inst['Tag_CPOS'] = pos[:cpos_chars] 
        # POS features        
        feats = feat.split('|', feat_no-1)
        feats += ['']*(feat_no-len(feats))
        for feat_ord, feat in enumerate(feats, start=1):
            if use_feat_names:
                feat_name, feat_val = feat.split('=', 1)
                inst['Tag_' + feat_name] = feat_val
            else:
                inst['Tag_FEAT' + str(feat_ord)] = feat
        # increase word number
        word_id += 1
        # save the instance to the buffer
        buf.append(inst)
    # write this all out as ARFF
    data = DataSet()
    attr_order = ['sent_id', 'word_id', 'Lemma', 'Form', 
            'LemmaFormDiff_Front', 'LemmaFormDiff_Back']
    for i in xrange(1, 9):
        attr_order.append('LemmaSuff_' + str(i))
    attr_order.extend(['Tag_POS', 'Tag_CPOS'])
    data.load_from_dict(buf, {'word_id': 'numeric'}, attr_order)
    data.save_to_arff(out_file)

    
def main():
    """\
    Main program entry point.
    """
    # parse options
    opts, filenames = getopt.getopt(sys.argv[1:], 'hc:f:n')
    show_help = False
    feat_no = 0
    use_feat_names = False
    cpos_chars = 1
    for opt, arg in opts:
        if opt == '-f':
            feat_no = int(arg)
        elif opt == '-c':
            cpos_chars = int(arg)
        elif opt == '-n':
            use_feat_names = True
        elif opt == '-h':
            show_help = True
    # display help and exit
    if len(filenames) != 2 or show_help:
        display_usage()
        sys.exit(1)
    # run the conversion
    convert(filenames[0], filenames[1], feat_no, use_feat_names, cpos_chars)

if __name__ == '__main__':
    main()
