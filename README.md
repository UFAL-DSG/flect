Flect
=====
**Robust Multilingual Statistical Morphology Generation Models**

Authors: Ondřej Dušek and Filip Jurčíček

Institute of Formal and Applied Linguistics, Charles University in Prague

About
-----

**Flect** is a tool based on Python and Scikit-Learn that learns morphological
inflection patterns from corpora.

Use any morphologically annotated corpus to have the system learn how to 
automatically obtain inflected word forms from lemmas and morphological 
features. 

The system is able to inflect even previously unseen words by using lemma 
suffixes as features and predicting “edit scripts” that describe the 
difference between the lemma and the form.

Basic usage
------------

* Prepare data using the `conll2arff.py` script.

* Train your models and save them using `train.py`.
    * setup the models' configuration via Python code as shown in `configs/`.

* Test the performance of your models using `test.py`.

* To easily access Flect as a library from your program, use the 
    `SentenceInflector` class located in the `lib.flect` module.

Additional functions
---------------------

* You may generate further features (concatenations etc.)
    using the `combine_features.py` script.

* Data statistics may be obtained from `get_data_stats.py`,
    `get_feat_list.py` and `select_errors.py`.


License
-------

Distributed under the Apache 2.0 license. See `LICENSE` for more information.

Please cite the following paper if you use this software in your scientific
works:

* Ondřej Dušek, Filip Jurčíček: "Robust Multilingual Statistical Morphological
    Generation Models", in: *ACL Student Research Workshop*, Sofia, 2013.

The paper which describes the inner workings of the software and our 
experiments done with it, is available for download at
[https://aclweb.org/anthology-new/P/P13/P13-3023.pdf].

You may contact the authors at odusek * ufal.mff.cuni.cz or through GitHub
in case of bugs, comments, or questions.
