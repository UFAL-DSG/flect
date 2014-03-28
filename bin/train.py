#!/usr/bin/env python
# coding=utf-8
#

"""
Training sklearn models with flect.model.

Usage: ./train.py work-dir config.py train-data.arff.gz \\
                  model-file.pickle.gz \\
                  [test-data.arff.gz classif-file.arff.gz]

Configuration files examples are shown in configs/.

Locations of config.py, model-file.pickle.gz and classif-file are assumed
to be relative to the work-dir.

If divide_func is specified in the configuration file, a SplitModel is
trained instead of Model.

If unfold_pattern is specified, subdirectories are created in the main
working directory for each model variant.
"""

from __future__ import unicode_literals

import sys
import getopt

from flect.experiment.train_model import run_training
from flect.experiment.fnames import get_files

__author__ = "Ondřej Dušek"
__date__ = "2012"


# default cluster memory reservation setting (16 GB)
MEMORY = 16


def display_usage():
    """\
    Display program usage information.
    """
    print >> sys.stderr, __doc__


def main():
    """\
    Main program entry point.
    """
    opts, filenames = getopt.getopt(sys.argv[1:], 'm:hn:l')
    show_help = False
    memory = MEMORY
    job_name = 'train'
    filelist = False
    for opt, arg in opts:
        if opt == '-m':
            memory = int(arg)
        elif opt == '-h':
            show_help = True
        elif opt == '-n':
            job_name = arg
        elif opt == '-l':
            filelist = True
    # special training: using filelist
    if filelist:
        if len(filenames) != 4 or show_help:
            display_usage()
            sys.exit(1)
        work_dir, config, train_pattern, model_pattern = filenames
        train_files = get_files(train_pattern)
        for key, train_file in train_files:
            print >> sys.stderr, key
            model_file = model_pattern.replace('*', key)
            run_training(work_dir, config, train_file, model_file, memory=memory, name=(job_name + key))
        sys.exit(0)
    # display help and exit
    if len(filenames) not in [4, 6] or show_help:
        display_usage()
        sys.exit(1)
    # run the training
    run_training(*filenames, memory=memory, name=job_name)

if __name__ == '__main__':
    main()
