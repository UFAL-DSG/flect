#!/usr/bin/env python
# coding=utf-8

"""
Using Flect for inflection according to predicted edit scripts.
"""

from __future__ import unicode_literals
import re
from varutil import first
from functools import partial
from classif import FlectClassifier


__author__ = "Ondřej Dušek"
__date__ = "2014"


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
                orig, changed = change.split('-', 1)
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


class SentenceInflector(FlectClassifier):
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
        # load the model and setup basic features
        super(SentenceInflector, self).__init__(config)
        # setup further features created on-the-fly
        self.additional_features = self.__init_additional_features(config.get('additional_features', []))

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
            sent = self.parse_factored(sent)
            return_string = True
        if sent == '' or sent is None:  # rule out weird cases
            return ''
        # obtain features for classification
        instances = self.create_features(sent)
        # classify: obtain inflection rules
        inflections = self.model.classify(instances)
        # inflect according to the rules
        lemmas = [word[0] for word in sent]
        forms = [inflect(lemma, inflection)
                 for lemma, inflection in zip(lemmas, inflections)]
        # return the result
        return ' '.join(forms) if return_string else forms

    def create_features(self, sent):
        """\
        Create all features needed for the given sentence (using the
        input features given directly in the sentence as well as any
        additional features defined in the configuration).

        @param sent: The input sentence (as an array of arrays, each corresponding \
            to all input features for one word)
        @return: An array of dictionaries, each representing all output features \
            for one word
        """
        instances = super(SentenceInflector, self).create_features(sent)
        # insert additional features
        for feat_name, feat_func in self.additional_features:
            for word_no, inst in enumerate(instances):
                inst[feat_name] = feat_func(insts=instances, word_no=word_no)
        # return the result
        return instances

    def __init_additional_features(self, input_list):
        """\
        Precompiles given additional feature functions.

        The functions are defined in a list of strings of the following form:

            FeatureLabel: neighbor|substr|combine param1 param2 ...

        For 'neighbor' features, the parameters are the relative shift from
        the original word and the name of the target feature.

        For 'substr' features the parameters are the length of the substring
        (counted from the end if negative) and the target feature.

        The 'combine' features require a list of target features from the same
        word to be combined.
        """
        output_list = []
        for feat in input_list:
            # parse the input
            label, func_name, func_params = re.split(r'[:\s]+', feat, 2)
            func_params = re.split(r'[,\s]+', func_params)
            feat_func = None
            # create substring feature functions
            if func_name.lower() == 'substr':
                feat_func = partial(self.substr, sublen=int(func_params[0]), orig_feat=func_params[1])
            # create neighbor feature functions
            elif func_name.lower() == 'neighbor':
                feat_func = partial(self.neighbor, shift=int(func_params[0]), orig_feat=func_params[1])
            # create combining feature functions
            elif func_name.lower() == 'combine':
                feat_func = partial(self.combine, orig_feats=func_params)
            else:
                raise Exception('Unknown feature format:' + feat)
            # store the result
            output_list.append((label, feat_func))
        return output_list

    @staticmethod
    def substr(sublen, orig_feat, insts, word_no):
        """Returns a substring of the original feature.

        @param sublen: Substring length (positive = from the beginning, negative = from the end)
        @param orig_feat: Names of the original feature
        @param insts: Data instances
        @param word_no: Index of the target word
        @return: The substring of the given feature of the given word
        """
        if sublen < 0:
            return insts[word_no][orig_feat][sublen:]
        return insts[word_no][orig_feat][:sublen]

    @staticmethod
    def neighbor(shift, orig_feat, insts, word_no):
        """Returns features from a word's neighbor.

        @param shift: Distance from the original word to the neighbor
        @param orig_feats: Names of the features
        @param insts: Data instances
        @param word_no: Index of the original word
        @return: The value of the given feature at word_no + shift, or '' if out of range
        """
        if word_no + shift < 0 or word_no + shift >= len(insts):
            return ''
        return insts[word_no + shift][orig_feat]

    @staticmethod
    def combine(orig_feats, insts, word_no):
        """Combine the given features into one string.

        @param orig_feats: Names of features to combine
        @param insts: Data instances
        @param word_no: Word index
        @return: A concatenation of the values of the given features \
            at the given position in the insts array.
        """
        inst = insts[word_no]
        val = [inst[feat] if inst[feat] is not None else '' for feat in orig_feats]
        if '' in val:
            return None
        return '|'.join(val)
