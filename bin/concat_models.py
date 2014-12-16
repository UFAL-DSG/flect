#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Creating a combined ConcatModel from multiple separately trained models.

Usage: ./concat_models.py -c <config.py> -o <output_model.pickle> model1.pickle model2.pickle

Just one of the configuration files is needed (for data headers, which must be
the same for all models).
"""

from __future__ import unicode_literals
from flect.config import Config
from flect.model import ConcatModel
import sys
from getopt import getopt


__author__ = "Ondřej Dušek"
__date__ = "2014"


def main(argv):
    opts, filenames = getopt(argv, 'c:o:')
    config_filename = None
    output_filename = None
    for opt, arg in opts:
        if opt == '-c':
            config_filename = arg
        elif opt == '-o':
            output_filename = arg

    if not config_filename or not output_filename or not filenames:
        sys.exit(__doc__)

    cfg = Config(config_filename)
    m = ConcatModel.load_from_files(cfg, filenames)
    m.save_to_file(output_filename)


if __name__ == '__main__':
    main(sys.argv[1:])
