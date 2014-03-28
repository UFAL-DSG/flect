#!/usr/bin/env python
# coding=utf-8

"""
Using Flect as a general wrapper for Scikit-Learn classifiers. This will just
pass the features to the internal Scikit-Learn classifier; no inflection
is involved.
"""

from __future__ import unicode_literals
from model import Model

__author__ = "Ondřej Dušek"
__date__ = "2014"


class FlectClassifier(object):
    """\
    A general classification using Flect's models. This also serves as a base
    class for SentenceInflector that generates inflection according to model outputs.
    """

    def __init__(self, config):
        """\
        Initialize the object with the given configuration.

        Configuration items (in a hash):

        model_file: path to a lib.model.Model in a pickle to be used for
                    classification
        """
        # load the model
        self.model_file = config['model_file']
        self.model = Model.load_from_file(self.model_file)
        # setup input features
        self.features = config.get('features', 'Lemma|Tag_POS').split('|')
        self.numeric_features = set()
        if 'feature_types' in config:
            feat_types = config['feature_types'].split('|')
            self.numeric_features = set([feat for feat, feat_type in zip(self.features, feat_types)
                                         if feat_type.upper() == 'NUMERIC'])
        self.ctr = 0

    def classify(self, insts):
        """\
        Classify a set of instances, given as a list of tuples, or a string in
        factored format.

        The first factor (or tuple member) is expected to be the lemma,
        the other factors are the POS tag and POS features.

        Returns a single string if given strings in factored format, a list
        of classes otherwise.
        """
        return_string = False
        if isinstance(insts, basestring):
            insts = self.parse_factored(insts)
            return_string = True
        # obtain features for classification
        insts = self.create_features(insts)
        # classify
        classes = self.model.classify(insts)
        # return the result
        return ' '.join(classes) if return_string else classes

    def create_features(self, insts):
        """\
        Create all features needed for the given set of instances

        @param sent: The input instances (as an array of arrays, each corresponding \
            to all input features for one instance)
        @return: An array of dictionaries, each representing all output features \
            for one instance
        """
        instances = []
        # create features
        for word in insts:
            inst = {}
            for feat_name, feat_val in zip(self.features, word):
                if feat_name in self.numeric_features:
                    feat_val = float(feat_val)
                inst[feat_name] = feat_val
            instances.append(inst)
        # return the result
        return instances

    def parse_factored(self, sent):
        """\
        Parse a factored format, i.e. return a list of tuples corresponding
        to words in the sentence.
        """
        return [tuple(word.split('|')) for word in sent.split('\n')]
