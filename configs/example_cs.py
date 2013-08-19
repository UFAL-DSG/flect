#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from sklearn.feature_extraction.dict_vectorizer import DictVectorizer
from sklearn.feature_selection.univariate_selection import SelectPercentile
from sklearn.linear_model.logistic import LogisticRegression
 

config = {'class_attr': 'LemmaFormDiff_Back',
          'select_attr': ['Lemma',
#                          'Form',
#                          'LemmaFormDiff_Back',   # class
#                          'LemmaFormDiff_Front',  # not used, yet
                          'LemmaSuff_1', 'LemmaSuff_2', 'LemmaSuff_3',
                          'LemmaSuff_4', #'LemmaSuff_5', 'LemmaSuff_6',
                          #'LemmaSuff_7', 'LemmaSuff_8',
                          'Tag_POS', 'Tag_SubPOS', 'Tag_Gen', 'Tag_Num',
                          'Tag_Cas', 'Tag_PGe', 'Tag_PNu', 'Tag_Per',
                          'Tag_Ten', 'Tag_Gra', 'Tag_Neg', 'Tag_Voi',
                          #'Tag_Var',
                          'Tag_Cas-Num-Gen', 'Tag_Num-Gen', 'Tag_Cas-Gen', 'Tag_Cas-Num'],
          'filter_attr': lambda key, val: False if key.startswith('Tag') and val in ['.', '-'] else True,
          'vectorizer': DictVectorizer(),
          'feature_filter': SelectPercentile(percentile=15),
         'classifier_class': LogisticRegression,
          'classifier_params': {'penalty': ['l1'],
                                'C': [10, 100],
                                'tol': [0.001, 0.0001]},
         'unfold_pattern': '^(penalty|C|tol)$'
          }
