#!/usr/bin/env python
# coding=utf-8
#

"""
Helper function for models split using ML-Process (http://code.google.com/p/en-deep).
"""

from __future__ import unicode_literals
from os import listdir
from os.path import isfile, join, sep
from fnames import build_model_keyset
#from sklearn.dummy import DummyClassifier
from flect.config import Config
from flect.model import SplitModel, Model
from flect.dataset import DataSet
import sys


def gather_split_model(in_dir, out_prefix, divide_func, save_nodummy, cfg_file, model_keys):
    """Build a SplitModel out of many trained models, given model key -> file mapping."""
    # load configuration
    if not sep in cfg_file:
        cfg_file = join(in_dir, cfg_file)
    cfg = Config(cfg_file)
    cfg['divide_func'] = divide_func
    # load all models
    tm = SplitModel.load_from_files(cfg, model_keys)
    # train a backoff model
    dummy_data = DataSet()
    dummy_data.load_from_dict([{cfg['select_attr'][0]: '', cfg['class_attr']: 'UNK'}])
    tm.backoff_model = tm.train_backoff_model(dummy_data)
    # save normal model
    tm.save_to_file(out_prefix + '.pickle')
    # create and save no-dummy model
    if save_nodummy:
        for key in tm.models.keys():
            if len(tm.models[key].data_headers.get_attrib(tm.models[key].class_attr).values) == 1:
                del tm.models[key]
        tm.save_to_file(out_prefix + '.nodummy.pickle')


def split_model_by_settings(in_dir, out_prefix, divide_func,
                       save_nodummy=False, cfg_file='config.py',
                       fname_start='model-', fname_end='.pickle.gz'):
    """Build a SplitModel out of trained models with the same parameters."""
    # find model files
    model_files = [f for f in listdir(in_dir)
                   if isfile(join(in_dir, f)) and f.startswith(fname_start) and f.endswith(fname_end)]
    model_keys = build_model_keyset(fname_start + '*' + fname_end, model_files)
    gather_split_model(in_dir, out_prefix, divide_func, save_nodummy, cfg_file, model_keys)


def split_model_best(in_dir, out_prefix, divide_func, dtest_dir,
                            save_nodummy=False, cfg_file='config.py',
                            fname_start='model-', fname_end='.pickle.gz',
                            dtest_start='dtest-', dtest_end='.arff.gz',
                            param_sep='-', default_param='l1_1_001'):
    """Build a SplitModel out of trained models, selecting the best parameters for the data set."""
    model_files = [f for f in listdir(in_dir)
                   if isfile(join(in_dir, f)) and f.startswith(fname_start) and f.endswith(fname_end)]
    model_keys_flat = build_model_keyset(fname_start + '*' + fname_end, model_files)
    model_keys_hier = {}
    for key, model_file in model_keys_flat.iteritems():
        if not param_sep in key:
            print >> sys.stderr, 'No param-sep in file name:', model_file
            continue
        key, param = key.split(param_sep)
        if not key in model_keys_hier:
            model_keys_hier[key] = {}
        model_keys_hier[key][param] = model_file
    model_keys_best = {}
    for key in model_keys_hier.iterkeys():
        print >> sys.stderr, key.encode('utf-8')
        sys.stderr.flush()
        dtest_file = join(dtest_dir, dtest_start + key + dtest_end)
        if isfile(dtest_file):
            best_acc = -1
            best_param = default_param
            for param, model_file in model_keys_hier[key].iteritems():
                m = Model.load_from_file(model_file)
                acc = m.evaluate(dtest_file)
                if acc > best_acc:
                    best_acc = acc
                    best_param = param
            model_keys_best[key] = model_keys_hier[key][best_param]
        else:
            model_keys_best[key] = model_keys_hier[key][default_param]
    gather_split_model(in_dir, out_prefix, divide_func, save_nodummy, cfg_file, model_keys_best)
