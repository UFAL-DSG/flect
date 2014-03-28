#!/usr/bin/env python
# coding=utf-8
#

"""
Helper function for models split using ML-Process (http://code.google.com/p/en-deep).
"""

from __future__ import unicode_literals
import re
import sys
from glob import iglob


def get_files(pattern):
    pattern_re = re.sub(r'\*', '(.*)', pattern)
    files = []
    for fname in iglob(pattern):
        key = re.match(pattern_re, fname).group(1)
        files.append((key, fname))
    return files


def filename_decode(fname):
    fname_dec = ''
    for part in re.split(r'(\[[0-9a-f]+\])', fname):
        if part.startswith('['):
            fname_dec += unichr(int(part.strip('[]'), 16))
        else:
            fname_dec += part
    return fname_dec


def build_model_keyset(pattern, files):
    keys = {}
    pattern = re.sub(r'\*', '(.*)', pattern)
    for f in files:
        m = re.match(pattern, f)
        if not m:
            print >> sys.stderr, 'File does not match pattern:', f
            continue
        key = filename_decode(m.group(1))
        keys[key] = f
    return keys
