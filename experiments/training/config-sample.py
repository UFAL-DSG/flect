#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Example configuration file for Flect training.
#

from __future__ import unicode_literals

# You need to import all classes that you use within the settings below
from sklearn.feature_extraction.dict_vectorizer import DictVectorizer
from sklearn.feature_selection.univariate_selection import SelectPercentile
from sklearn.linear_model.logistic import LogisticRegression
 

config = {
          # This is the target class fetaure. Change to LemmaFormDiff_Front 
          # in models that predict the changes in beginning of the words.
          'class_attr': 'LemmaFormDiff_Back',
          
          # This controls which features of the input ARFF file will be actually
          # used in training (do not select the target class feature!)
          'select_attr': ['Lemma',
                          'LemmaSuff_1', 'LemmaSuff_2', 'LemmaSuff_3',
                          'LemmaSuff_4', 'LemmaSuff_5', 'LemmaSuff_6',
                          'LemmaSuff_7', 'LemmaSuff_8',
                          'Tag_POS', 'Tag_SubPOS', 'Tag_Gen', 'Tag_Num',
                          'Tag_Cas', 'Tag_PGe', 'Tag_PNu', 'Tag_Per',
                          'Tag_Ten', 'Tag_Gra', 'Tag_Neg', 'Tag_Voi',
                          'Tag_Var'],
          
          # This filters out some feature values (here 'Tag_*' values equal to '.' or '-'.
          # You can use an arbitrary lambda function here (or None if you don't want it).
          'filter_attr': lambda key, val: False if key.startswith('Tag') and val in ['.', '-'] else True,
          
          'vectorizer': DictVectorizer(),
          
          # Feature filtering using ANOVA (recommended)
          'feature_filter': SelectPercentile(percentile=10),
          
          # You can use any Scikit-Learn classifier here
          'classifier_class': LogisticRegression,
          
          # Classifier parameter settings (see Scikit-Learn documentation for the list of parameters).
          # If you use lists instead of single values and specify the unfold_pattern, all the values
          # in the lists will be tried in parallel on a cluster using qsub).
          # Do not use lists of values and the unfold_pattern setting if you don't have access to 
          # cluster/qsub.
          'classifier_params': {'penalty': ['l1', 'l2'],
                                'C': [1, 10, 100, 1000],
                                'tol': [0.01, 0.001, 0.0001]},
          'unfold_pattern': '^(penalty|C|tol)$'
          }
