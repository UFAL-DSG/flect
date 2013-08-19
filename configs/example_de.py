#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from sklearn.feature_extraction.dict_vectorizer import DictVectorizer
from sklearn.feature_selection.univariate_selection import SelectPercentile
from sklearn.linear_model.logistic import LogisticRegression
 

config = {
          # target feature (lemma-form diff)
          'class_attr': 'LemmaFormDiff_Back', 

          # selected features for classification
          'select_attr': ['Lemma',
#                          'Form',
#                          'LemmaFormDiff_Back',   # class
#                          'LemmaFormDiff_Front',  # not used, yet
                          'LemmaSuff_1', 'LemmaSuff_2', 'LemmaSuff_3',
                          'LemmaSuff_4', #'LemmaSuff_5', 'LemmaSuff_6',
                          #'LemmaSuff_7', 'LemmaSuff_8',
                          'Tag_POS', 'Tag_CPOS',
                          'Tag_FEAT1', 'Tag_FEAT2', 'Tag_FEAT3', 'Tag_FEAT4'
                            'Tag_FEAT1+Tag_FEAT2', 'Tag_FEAT1+Tag_FEAT3', 'Tag_FEAT1+Tag_FEAT4', 
                            'Tag_FEAT2+Tag_FEAT3', 'Tag_FEAT2+Tag_FEAT4', 'Tag_FEAT3+Tag_FEAT4', 
                            'Tag_FEAT1+Tag_FEAT2+Tag_FEAT3', 'Tag_FEAT1+Tag_FEAT2+Tag_FEAT4', 
                            'Tag_FEAT1+Tag_FEAT3+Tag_FEAT4', 'Tag_FEAT2+Tag_FEAT3+Tag_FEAT4', 
                            'Tag_FEAT1+Tag_FEAT2+Tag_FEAT3+Tag_FEAT4',
                            'NEIGHBOR-1_Lemma', 'NEIGHBOR-1_Tag_POS', 'NEIGHBOR-1_Tag_CPOS', 
                            ],

          # filtering out feature meaningless values (using an arbitrary function)
#          'filter_attr': lambda key, val: False if key.startswith('Tag') and val in ['.', '-'] else True,

          # binarization setting
          'vectorizer': DictVectorizer(),

          # filtering out features that are not useful
#          'feature_filter': SelectPercentile(percentile=10),

          # sklearn classifier to be used
         'classifier_class': LogisticRegression,

          # classifier parameters to be used (multiple variants)
          'classifier_params': {'penalty': ['l1'],
                                'C': [1, 10, 100, 1000],
                                'tol': [0.01, 0.001, 0.0001]},

          # settings to unfold classifier parameters
         'unfold_pattern': '^(penalty|C|tol)$'
          }
