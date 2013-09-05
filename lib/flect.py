#!/usr/bin/env python
# coding=utf-8

"""
Inflection according to diff scripts.
"""

from __future__ import unicode_literals

import re
from varutil import first
from lib.model import Model


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
    # return the resulting word form
    return form


class SentenceInflector(object):
    """\
    A simple object that accepts sentences (with lemmas and morphological
    information) and inflect the words in them according
    to the given model and configuration.
    """

    def __init__(self, config):
        """\
        Initialize the object with the given configuration.

        Configuration items (in a hash):

        model_file: path to a lib.model.Model in a pickle to be used for
                    classification
        """
        # TODO handle features config (now dummy, preset for English)
        self.__model_file = config['model_file']
        self.__model = Model.load_from_file(self.__model_file)

    def inflect_sent(self, sent):
        """\
        Inflect a sentence, given as a list of tuples, or a string in
        factored format.

        The first factor (or tuple member) is expected to be the lemma,
        the other factors are the POS tag and POS features.

        Returns a single string if given strings in factored format, a list
        of word forms otherwise.
        """
        return_string = False
        if isinstance(sent, basestring):
            sent = self.__parse_factored(sent)
            return_string = True
        # obtain lemmas
        lemmas = [word[0] for word in sent]
        # obtain features for classification
        instances = [self.__get_features(word) for word in sent]
        # classify: obtain inflection rules
        inflections = self.model.classify(instances)
        # inflect according to the rules
        forms = [inflect(lemma, inflection)
                 for lemma, inflection in zip(lemmas, inflections)]
        # return the result
        return ' '.join(forms) if return_string else forms

    def __get_features(self, sent, word_no):
        """\
        Retrieve all the features needed for morphological inflection
        of word at the given position in the given sentence and return
        them as a dictionary.
        """
        # add lemma and morphological information (current and previous word)
        feats = {
                 'Lemma': sent[word_no][0],
                 'Tag_POS': sent[word_no][1],
                 'Tag_CPOS': sent[word_no][1][1],
                 'Tag_FEAT1': '',
                 'NEIGHBOR-1_Lemma': sent[word_no - 1][0]
                    if word_no > 0 else '',
                 'NEIGHBOR-1_Tag_POS': sent[word_no - 1][1]
                    if word_no > 0 else '',
                 'NEIGHBOR-1_Tag_CPOS':  sent[word_no - 1][1][1]
                    if word_no > 0 else '',
                 }
        # lemma suffixes of length 1 - 8 (inclusive)
        for suff_len in xrange(1, 9):
            feats['LemmaSuff_' + str(suff_len)] = feats['Lemma'][-suff_len:]
        return feats
