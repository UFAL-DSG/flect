#!/usr/bin/env python
# coding=utf-8
#

"""
Testing trained models on given data.

Usage: ./flect_test.py -h for this help
       ./flect_test.py -s source_attr -t target_attr -m model1 \\
                        [-m model2 ...] [-o [perc:]train_set.arff] \\
                        [-i] [-p] \\
                        test_set.arff output.arff

-s = name of the source ARFF attribute (lemma)

-t = name of the (gold) target ARFF attribute (form)

-m = list of trained  model files to be used (may be repeated)

-o = training data file (you may prepend a percentage
     so that only a part of data is used, e.g. "0.5:train.arff".

-i = evaluate individual models (if more models are used)

-p = POS attribute (to evaluate performance in individual POSes)

"""

from __future__ import unicode_literals
import sys
import getopt
import regex
from lib.dataset import DataSet, Attribute
from lib.model import Model
from lib.flect import inflect
from lib.logf import log_info

__author__ = "Ondřej Dušek"
__date__ = "2013"


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def evaluate_oov(data, source_attr, target_attr, forms_attr,
                 oov_test_file, oov_part):
    """\
    Out-of-vocabulary evaluation
    """
    log_info('Loading known lemmas and forms from: ' + oov_test_file)
    train = DataSet()
    train.load_from_arff(oov_test_file)
    if oov_part < 1:
        log_info('Using only %f-part of the file.' % oov_part)
        train = train.subset(0, int(round(oov_part * len(train))), copy=False)
    known_forms = {i[target_attr].lower() for i in train}
    known_lemmas = {i[source_attr].lower() for i in train}
    oov_forms = [1 if i[target_attr].lower() not in known_forms else 0
                 for i in data]
    oov_lemmas = [1 if i[source_attr] not in known_lemmas else 0
                  for i in data]
    data.add_attrib(Attribute('OOV_FORM', 'numeric'), oov_forms)
    data.add_attrib(Attribute('OOV_LEMMA', 'numeric'), oov_lemmas)
    oov_forms_count = sum(oov_forms)
    oov_forms_good = count_correct(data, target_attr, forms_attr,
                                   lambda i: i['OOV_FORM'])
    print_score(oov_forms_good, oov_forms_count, 'OOV forms')
    oov_lemmas_count = sum(oov_lemmas)
    oov_lemmas_good = count_correct(data, target_attr, forms_attr,
                                    lambda i: i['OOV_LEMMA'])
    print_score(oov_lemmas_good, oov_lemmas_count, 'OOV lemmas')


def evaluate_poses(data, gold_attr, predict_attr, pos_attr):
    """\
    Print scores for different POSes.
    """
    poses = data.split(lambda _, i: i[pos_attr])
    for pos, pos_data in poses.iteritems():
        good = count_correct(pos_data, gold_attr, predict_attr)
        print_score(good, len(pos_data), 'POS = ' + pos)


def evaluate_nopunct(data, lemma_attr, gold_attr, predict_attr):
    """\
    Evaluate on data excluding punctuation.
    """
    nopunct = data[lambda _, i: not regex.match(r'^\p{P}', i[lemma_attr])]
    good = count_correct(nopunct, gold_attr, predict_attr)
    print_score(good, len(nopunct), 'Excluding punctuation lemmas')


def evaluate_nolemma(data, lemma_attr, gold_attr, predict_attr):
    """\
    Evaluate on data where the target forms are not equal to lemmas.
    """
    nolemma = data[lambda _, i: i[lemma_attr].lower() != i[gold_attr].lower()]
    good = count_correct(nolemma, gold_attr, predict_attr)
    print_score(good, len(nolemma), 'Target forms not equal to lemma')


def count_correct(data, gold_attr, predict_attr, cond=lambda _: True):
    """\
    Return the number of correctly predicted forms on the given data set.
    If cond is set, count only the instances that satisfy cond.
    """
    return sum(1 for i in data if cond(i) and
               i[gold_attr].lower() == i[predict_attr].lower())


def print_score(good, total, label):
    """\
    Prints the accuracy score given the number of correctly predicted and
    all items, plus a label.
    """
    score = good / float(total)
    log_info('Score (%s): %d / %d = %f' % (label, good, total, score))


def test_models(file_in, file_out, model_files, source_attr, target_attr,
                oov_test_file, oov_part, pos_attr, test_indiv):
    """\
    Test all the given models on the selected file and save the target.

    If oov_test_file is set, performs also OOV evaluation.
    If test_pos is True, prints detailed results for various POSs.
    """
    # load testing data
    log_info('Loading data: ' + file_in)
    data = DataSet()
    data.load_from_arff(file_in)
    forms = data[source_attr]
    # apply all models
    for model_num, model_file in enumerate(model_files, start=1):
        model = Model.load_from_file(model_file)
        log_info('Applying model: ' + model_file)
        rules = model.classify(data)
        output_attr = 'OUTPUT_M' + str(model_num)
        data.add_attrib(Attribute(output_attr, 'string'), rules)
        if test_indiv:
            good = count_correct(data, model.class_attr, output_attr)
            print_score(good, len(data), 'Model accuracy')
        forms = [inflect(form, rule) for form, rule in zip(forms, rules)]
        forms_attr = 'FORMS_M' + str(model_num)
        data.add_attrib(Attribute(forms_attr, 'string'), forms)
    # test the final performance
    log_info('Evaluating...')
    good = count_correct(data, target_attr, forms_attr)
    print_score(good, len(data), 'ALL')
    # evaluate without punctuation
    evaluate_nopunct(data, source_attr, target_attr, forms_attr)
    # evaluate forms different from lemma
    evaluate_nolemma(data, source_attr, target_attr, forms_attr)
    # load training data for OOV tests, evaluate on OOV
    if oov_test_file:
        evaluate_oov(data, source_attr, target_attr, forms_attr,
                     oov_test_file, oov_part)
    # test on different POSes
    if pos_attr:
        evaluate_poses(data, target_attr, forms_attr, pos_attr)
    # save the classification results
    log_info('Saving data: ' + file_out)
    data.save_to_arff(file_out)


def main():
    """\
    Main application entry: parse command line and run the test.
    """
    opts, filenames = getopt.getopt(sys.argv[1:], 'm:s:t:hio:p:')
    show_help = False
    models = []
    source_attr = None
    target_attr = None
    train_file = None
    train_part = 1.0
    pos_attr = None
    eval_indiv = False
    for opt, arg in opts:
        if opt == '-m':
            models.append(arg)
        elif opt == '-h':
            show_help = True
        elif opt == '-s':
            source_attr = arg
        elif opt == '-t':
            target_attr = arg
        elif opt == '-o':
            if ':' in arg:
                train_part, train_file = arg.split(':', 1)
                train_part = float(train_part)
            else:
                train_file = arg
        elif opt == '-p':
            pos_attr = arg
        elif opt == '-i':
            eval_indiv = True
    # display help and exit
    if not models or len(filenames) != 2 or \
            not source_attr or not target_attr or show_help:
        display_usage()
        sys.exit(1)
    # run the training
    test_models(filenames[0], filenames[1], models, source_attr, target_attr,
                train_file, train_part, pos_attr, eval_indiv)


if __name__ == '__main__':
    main()
