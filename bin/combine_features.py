#!/usr/bin/env python
# coding=utf-8
#

"""
Various functions to generate new features using existing ones.

Usage on ARFF files from the command line:

    ./combine_features.py [-s N:attr|-c|-a N:attr1,...|-n N:attr1,...] \\
            in.arff out.arff

-s = add substrings of up to N characters from the given attribute
     (negative = from the end)
-c = combine Tag_Cas,Tag_Num,Tag_Gen
-a = combine subsets of up to N attributes from the list
-n = add neighboring word's features; N specifies the distance.
     The word must stay in the same sentence.

The switches may be combined and will be applied in the above order.
"""

from __future__ import unicode_literals

import re
import flect.flect
from flect.dataset import Attribute, DataSet
from flect.logf import log_info
from itertools import combinations
import getopt
import sys


__author__ = "Ondřej Dušek"
__date__ = "2013"


SENT_ID_ATTR = 'sent_id'  # sentence ID attribute


def concat_attrib(data, attribs, new_name=None, divider='', nonempty=False):
    """\
    Concatenate the selected attributes to form a new one (attributes
    should be specified by name or number).

    If an attribute is not defined, its value is replaced by '?'.
    """
    attrib_list = [data.get_attrib(a).name for a in attribs]
    if new_name is None:
        new_name = '+'.join(attrib_list)
    values = []
    for inst in data:
        val = [inst[a] if inst[a] is not None else '?' for a in attrib_list]
        if not nonempty or '' not in val:
            values.append(divider.join(val))
        else:
            values.append('')
    data.add_attrib(Attribute(new_name, 'string'), values)


def combine_tag_num_gen_cas(data):
    """\
    Given a data set that has the attributes Tag_Cas, Tag_Num and Tag_Gen,
    combine these attributes in pairs and all together.
    """
    concat_attrib(data, ['Tag_Cas', 'Tag_Num', 'Tag_Gen'], 'Tag_Cas-Num-Gen')
    concat_attrib(data, ['Tag_Num', 'Tag_Gen'], 'Tag_Num-Gen')
    concat_attrib(data, ['Tag_Cas', 'Tag_Gen'], 'Tag_Cas-Gen')
    concat_attrib(data, ['Tag_Cas', 'Tag_Num'], 'Tag_Cas-Num')


def combine_subsets(data, attribs, up_to_size):
    """\
    Combine all subsets of the given attribute list, up no given
    size.
    """
    for size in range(1, up_to_size + 1):
        for attr_set in combinations(attribs, size):
            concat_attrib(data, attr_set, divider='|', nonempty=True)


def inflect(data, attrib_lemma, attrib_infl, attrib_form):
    """\
    Given a data set with the lemma and inflection rules attributes, this will
    add the resulting inflected forms as a new attribute.
    """
    attrib_lemma = data.get_attrib(attrib_lemma).name
    attrib_infl = data.get_attrib(attrib_infl).name
    values = [flect.flect.inflect(inst[attrib_lemma], inst[attrib_infl])
              for inst in data]
    data.add_attrib(Attribute(attrib_form, 'string'), values)


def add_neighbor_attributes(data, shift, attribs):
    """\
    Add the given attributes of a neighbor in the distance given by shift.
    The values are set as unknown if the neighbor does not exist within the
    same sentence.
    """
    attrib_list = [data.get_attrib(a).name for a in attribs]
    for attrib in attrib_list:
        values = []
        for idx, inst in enumerate(data):
            if idx + shift >= 0 and idx + shift < len(data):
                ngb_inst = data[idx + shift]
                values.append(ngb_inst[attrib]
                              if ngb_inst[SENT_ID_ATTR] == inst[SENT_ID_ATTR]
                              else None)
            else:
                values.append(None)
        new_name = 'NEIGHBOR' + ('+' if shift > 0 else '') + \
                str(shift) + '_' + attrib
        data.add_attrib(Attribute(new_name, 'string'), values)


def add_substr_attributes(data, sub_len, attrib):
    """\
    Add substrings of the given attribute as separate attributes.
    The sub_len parameter controls the maximum length and
    the position of the substrings (negative = end, positive = beginning)
    """
    attrib = data.get_attrib(attrib).name
    for l in xrange(1, abs(sub_len) + 1):
        values = [inst[attrib][:l].lower() if sub_len > 0
                  else inst[attrib][-l:].lower()
                  for inst in data]
        new_name = attrib + '_SUBSTR' + ('+' if sub_len > 0 else '-') + \
                str(l)
        data.add_attrib(Attribute(new_name, 'string'), values)


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def main():
    """\
    Main application entry: parse command line and run the test.
    """
    opts, filenames = getopt.getopt(sys.argv[1:], 'ca:s:n:')
    show_help = False
    combine_cng = False
    subsets = []
    neighbors = []
    substrs = []
    for opt, arg in opts:
        if opt == '-c':
            combine_cng = True
        elif opt == '-s':
            sub_len, attr = arg.split(':', 1)
            substrs.append((int(sub_len), attr))
        elif opt == '-a':
            size, attrs = arg.split(':', 1)
            subsets.append((int(size), re.split(r'[, ]+', attrs)))
        elif opt == '-n':
            shift, attrs = arg.split(':', 1)
            neighbors.append((int(shift), re.split(r'[, ]+', attrs)))
    # display help and exit
    if len(filenames) != 2 or not (combine_cng or substrs or
                                   subsets or neighbors) or show_help:
        display_usage()
        sys.exit(1)
    # run the training
    filename_in, filename_out = filenames
    data = DataSet()
    log_info('Loading data: ' + filename_in)
    data.load_from_arff(filename_in)
    if substrs:
        for (sub_len, attr) in substrs:
            log_info(('Adding substrings from the %s of %s ' +
                      'up to %d characters long ...') %
                     (('beginning' if sub_len > 0 else 'end'),
                      attr, abs(sub_len)))
            add_substr_attributes(data, sub_len, attr)
    if combine_cng:
        log_info('Combining case, number, gender ...')
        combine_tag_num_gen_cas(data)
    if subsets:
        for (set_size, set_attrs) in subsets:
            log_info('Combining up to %d attributes from [%s] ...' %
                     (set_size, ','.join(set_attrs)))
            combine_subsets(data, set_attrs, set_size)
    if neighbors:
        for (shift, attrs) in neighbors:
            log_info('Adding neighbor %d\'s attributes [%s] ...' %
                     (shift, ','.join(attrs)))
            add_neighbor_attributes(data, shift, attrs)
    log_info('Saving data: ' + filename_out)
    data.save_to_arff(filename_out)


if __name__ == '__main__':
    main()
