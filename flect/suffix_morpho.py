#!/usr/bin/env python
# coding=utf-8

"""
Suffix-based memorizing of morphological information that can be used to learn
morphological analysis to be used with a tagger, such as Featurama
(http://sf.net/projects/featurama).

Usage if run from the command line:

./suffix_morpho.py [-t|-e] [-f format] [-l] [-p prune_threshold] in-file out-file

-t = training
-e = evaluation (producing analyses, expects one word per line)
-f = input format (training only; `factored`, `one_per_line` or `csts`)
-p = pruning threshold (training only; minimum number of occurences for an
    analysis to be remembered)
"""

from __future__ import unicode_literals
import sys

from getopt import getopt

from string_distances import inv_edit_script
from flect import inflect
import json
import codecs
import re

__author__ = "Ondřej Dušek"
__date__ = "2013"

DEFAULT_MAX_SUF = 4


def train_suffixes(in_file, out_file,
                   max_suf=DEFAULT_MAX_SUF, lowercase=False,
                   input_format='factored', threshold=1):
    """
    Main training function -- memorizing morphological analyses based on
    suffixes of word forms encountered in the training corpus.

    `max_suf` indicates the maximum suffix length to be learned.

    `lowercase` tells the system to lowercase all forms.

    Supported `input_format`s:
    * `factored` (one sentence per line, word-lemma-tag split by pipe character `|')
    * `one_per_line` (one token per line, word-lemma-tag split by whitespace)
    * `csts` (the CSTS SGML format used in Czech morphological analysis)

    `threshold` sets the minimum number of occurrences for a form to be
    remembered.
    """

    # initialize data structures
    suff = {'*': {}}
    for suf_len in xrange(1, max_suf + 1):
        suff[suf_len] = {}
    line_no = 0
    # setup input format (function to return (form, lemma, tag) triplets in an array)
    if input_format == 'factored':
        get_tokens_func = lambda line: [token.split('|') for token in line.split()]
    elif input_format == 'one_per_line':
        get_tokens_func = lambda line: [line.split()] if line else []
    elif input_format == 'csts':
        get_tokens_func = lambda line: [re.match(r'<[df][^>]*>([^<]*)<l>([^<]*)<t>([^<]*)(?:<|$)',
                                                line).groups()] \
                                                if re.match(r'<[df][ >]', line) else []
    else:
        raise Exception('Unknown format ' + input_format)

    # process the input file
    with codecs.open(in_file, 'r', 'UTF-8') as in_file:
        for line in in_file:
            for form, lemma, tag in get_tokens_func(line.strip()):
                if lowercase:
                    form = form.lower()
                    lemma = lemma.lower()
                diff = ' '.join(inv_edit_script(form.lower(), lemma.lower())).strip()
                # irregular words go under separate index
                if diff.startswith('*'):
                    suf_lemmas = suff['*'].get(form, {})
                    suff['*'][form] = suf_lemmas
                    key = '|'.join((diff, tag))
                    suf_lemmas[key] = suf_lemmas.get(key, 0) + 1
                # other words get prefixes
                else:
                    for suf_len in xrange(1, max_suf + 1):
                        suf_lemmas = suff[suf_len].get(form[-suf_len:], {})
                        suff[suf_len][form[-suf_len:]] = suf_lemmas
                        key = '|'.join((diff, tag))
                        suf_lemmas[key] = suf_lemmas.get(key, 0) + 1
            line_no += 1
            if line_no % 10000 == 0:
                print >> sys.stderr, str(line_no),
    print >> sys.stderr, ''

    # prune according to the threshold
    for _, suff_len in suff.iteritems():
        for suffix in suff_len:
            suff_len[suffix] = {tag_lemma: count
                                for tag_lemma, count in suff_len[suffix].iteritems()
                                if count > threshold}
    # save the output
    out_file = codecs.open(out_file, 'w', 'UTF-8')
    json.dump(suff, out_file, indent=4, separators=(',', ': '), ensure_ascii=False)
    out_file.close()


class Analyzer(object):
    """Suffix-based memorizing morphological analyzer"""

    def __init__(self, data, max_suf=DEFAULT_MAX_SUF, lowercase=False):
        """
        Create the analyzer using a JSON learnt data file (obtainable via
        `train_suffixes()`).

        `max_suf` indicates the maximum suffixes length to be used (must be
        lower or equal to the suffixes length used in the JSON file).

        Setting `lowercase` to True tells the analyzer to produce only
        lowercased lemmas.
        """
        in_file = codecs.open(data, 'r', 'UTF-8')
        data_suff = json.load(in_file)
        self.suff = {}
        self.lowercase = lowercase
        for key in data_suff.keys():
            try:
                self.suff[int(key)] = data_suff[key]
            except:
                self.suff[key] = data_suff[key]
        self.max_suf_len = max_suf

    def analyze(self, word):
        """\
        Return all possible morphological analyses of the given word according the loaded
        model.
        """
        # initialize
        if self.lowercase:
            word = word.lower()
        analyzes = []
        # try finding in completely irregular forms
        if word in self.suff['*']:
            analyzes = [an[1:] for an in self.suff['*'][word]]
        # try suffixes of decreasing length
        for suf_len in xrange(self.max_suf_len, 0, -1):
            word_suf = word[-suf_len:]
            if word_suf not in self.suff[suf_len]:
                continue
            # try to create lemmas from all possible rules for the given prefix,
            # ruling out the incompatible ones
            for rule in self.suff[suf_len][word_suf]:
                diff, tag = rule.split('|', 1)
                # some rules require a matching prefix
                if diff.startswith('<'):
                    if ' ' in diff:
                        prefix, diff = diff.split(' ', 1)
                    else:
                        prefix = diff
                        diff = ''
                    if not word.startswith(prefix[1:]):
                        continue
                    prefix_len = len(prefix[1:])
                    lemma_cand = word[prefix_len:]
                # most rules have no prefix
                else:
                    prefix_len = 0
                    diff = diff.strip()
                    lemma_cand = word
                # skip rules for which our word form is too short
                if diff:
                    too_short = False
                    for diff_part in diff.split(','):
                        if diff_part.startswith('*'):
                            break
                        if diff_part.startswith('>'):
                            diff_part = diff_part[1:]
                        min_len = int(re.match(r'^([0-9]+)', diff_part).group(1))
                        if len(lemma_cand) <= min_len:
                            too_short = True
                            break
                    if too_short:
                        continue
                # create lemma according to the given rule
                lemma = inflect(lemma_cand, diff.strip())
                analyzes.append('|'.join((lemma, tag)))
            # end as soon as we have some analyzes
            if analyzes:
                break
        # fallback (TODO fix this better, language-indep.)
        if not analyzes and re.match(r'[^a-zA-Z0-9_]', word):
            return [word + '|Z:-------------']
        elif not analyzes:
            return [word + '|X@-------------']
        # return the result
        return analyzes

if __name__ == '__main__':
    # process options
    opts, files = getopt(sys.argv[1:], 'tem:f:lp:')
    train = False
    etest = False
    max_suf = DEFAULT_MAX_SUF
    lowercase = False
    input_format = 'factored'
    threshold = 1
    for opt, arg in opts:
        if opt == '-t':
            train = True
        elif opt == '-e':
            etest = True
        elif opt == '-m':
            max_suf = int(arg)
        elif opt == '-f':
            input_format = arg
        elif opt == '-l':
            lowercase = True
        elif opt == '-p':
            threshold = int(arg)
    # check sanity
    if (not train and not etest) or (train and len(files) != 2) or \
            (etest and len(files) < 1):
        sys.exit('Usage: ./suffix_morpho.py [-t|-e] [-f format] [-l] '
                 '[-p prune_threshold] in-file out-file')
    # run
    if train:
        train_suffixes(*files, max_suf=max_suf, lowercase=lowercase, input_format=input_format)
    elif etest:
        out = codecs.getwriter('UTF-8')(sys.stdout)
        analyzer = Analyzer(files[0], max_suf=max_suf, lowercase=lowercase)
        files = files[1:]
        if not files:
            while True:
                line = raw_input()
                line = codecs.decode(line.strip(), 'UTF-8')
                if not line:
                    break
                words = line.split(None, 1)
                for word in words:
                    print >> out, "\n".join(analyzer.analyze(word))
        else:
            for word in files:
                print >> out, "\n".join(analyzer.analyze(codecs.decode(word, 'UTF-8')))
