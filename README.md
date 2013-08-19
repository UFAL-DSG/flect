Flect
=====
**Robust Multilingual Statistical Morphology Generation Models**

Authors: Ondřej Dušek and Filip Jurčíček

Institute of Formal and Applied Linguistics, Charles University in Prague

Basic usage:
------------

    * Prepare data using the `conll2arff.py` script.

    * Train your models and save them using `train.py` (setting the 
         configuration via Python code – examples shown in `examples/`

    * Test the performance of your models using `test.py`

Additional functions:
---------------------

    * You may generate further features (concatenations etc.)
        using the `combine_features.py` script.

    * Data statistics may be obtained from `get_data_stats.py`,
        `get_feat_list.py` and `select_errors.py`.


License:
--------

Distributed under the Apache 2.0 license. See `LICENSE` for more information.

Please cite the following paper if using this in your scientific works:

* Ondřej Dušek, Filip Jurčíček: "Robust Multilingual Statistical Morphological
    Generation Models", in: ACL Student Research Workshop, Sofia, 2013.

You may contact the authors at odusek * ufal.mff.cuni.cz in case of
bugs or any questions.
