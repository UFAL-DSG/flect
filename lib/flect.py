#!/usr/bin/env python
# coding=utf-8

"""
Inflection according to diff scripts.
"""

from __future__ import unicode_literals

import codecs
import sys
import re
from varutil import first

__author__ = "Ondřej Dušek"
__date__ = "2012"



def inflect(lemma, inflection):
    """\
    Return the inflected form given lemma and inflection rules.
    Supports front, back and mid changes.
    """
    form = lemma
    # replace irregular
    if inflection.startswith('*'):
        form = inflection[1:]
    # if there are changes, perform them
    elif inflection != '':
        # find out the front, mid, back changes
        diffs = inflection.split(",")
        front = first(lambda x: x.startswith('<'), diffs)
        back = first(lambda x: x.startswith('>'), diffs)
        mid = first(lambda x: '-' in x, diffs)
        # perform the changes
        add_back = ''
        # chop off the things from the back
        if back is not None:
            chop, add_back = re.match(r'^>([0-9]+)(.*)$', back).groups()
            chop = int(chop)
            if chop != 0:
                form = form[0:-chop]
        # changes in the middle
        if mid is not None:
            mids = mid.split(' ')
            search_part = form[0:-1].lower()
            for change in mids:
                orig, changed = change.split('-')
                orig_len = len(orig)
                # numbered change format -- position and length
                if re.match(r'^[0-9]', orig):
                    neg_pos, orig_len = re.match(r'^([0-9]+):([0-9]+)$',
                                                 orig).groups()
                    orig_len = int(orig_len)
                    pos = len(lemma) - int(neg_pos)
                # letter change format: find by adjacent letters
                elif len(search_part) > 0:
                    pos = search_part.rfind(orig, 0)
                else:
                    pos = len(form) - 1
                if pos >= -1:  # TODO what if we prohibit -1 ?
                    form = form[0:pos] + changed + form[pos + orig_len:]
                    search_part = search_part[0:pos]
        # add things to beginning and end
        if front is not None:
            form = front[1:] + form
        form = form + add_back
    # set the resulting form to the anode
    return form

