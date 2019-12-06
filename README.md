PatternLite
===========

[![PyPi version](http://img.shields.io/pypi/v/PatternLite.svg?style=flat)](https://pypi.org/project/PatternLite/)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-green.svg?style=flat)](https://github.com/WZBSocialScienceCenter/PatternLite/blob/master/LICENSE.txt)


**This is a fork of the original [Pattern package](https://github.com/clips/pattern). It is a stripped down version of the original package and contains only the `text` modules (i.e. `pattern.de`, `pattern.en`, `pattern.es`, `pattern.fr`, `pattern.it`, `pattern.nl`, `pattern.ru`, the `vector` module and parts of the `db` module.**

Apart from that, it fixes a few problems with the original package: 

 * much fewer dependencies: now only requires *numpy, scipy* and *nltk*
 * compatible with Python 3.6, 3.7, 3.8
 * properly closes files (no more *"ResourceWarning: unclosed file"*)

The remaining original features are:

 * Natural Language Processing: part-of-speech taggers, n-gram search, sentiment analysis, WordNet
 * Machine Learning: vector space model, clustering, classification (KNN, SVM, Perceptron)

For the original documentation, see <http://www.clips.ua.ac.be/pages/pattern>.

Installation
------------

PatternLite supports Python 3.6, 3.7 and 3.8.

If you have pip, you can automatically download and install from the [PyPI repository](https://pypi.org/project/PatternLite/):

```bash
pip install PatternLite
```

To install PatternLite from source, unzip the download and from the command line do:

```bash
python setup.py install
```


Documentation
-------------

For documentation and examples see the [user documentation](http://www.clips.ua.ac.be/pages/pattern). If you are a developer, go check out the [developer documentation](http://www.clips.ua.ac.be/pages/pattern-dev).

Version
-------

3.7

License
-------

**BSD**, see `LICENSE.txt` for further details.

Reference
---------

De Smedt, T., Daelemans, W. (2012). Pattern for Python. *Journal of Machine Learning Research, 13*, 2031–2035.

Contribute
----------

The source code is hosted on GitHub and contributions or donations are welcomed. Please have look at the [developer documentation](http://www.clips.ua.ac.be/pages/pattern-dev). If you use Pattern in your work, please cite our reference paper.

Bundled dependencies
--------------------

Pattern is bundled with the following data sets, algorithms and Python packages:

- **Brill tagger**, Eric Brill
- **Brill tagger for Dutch**, Jeroen Geertzen
- **Brill tagger for German**, Gerold Schneider & Martin Volk
- **Brill tagger for Spanish**, trained on Wikicorpus (Samuel Reese & Gemma Boleda et al.)
- **Brill tagger for French**, trained on Lefff (Benoît Sagot & Lionel Clément et al.)
- **Brill tagger for Italian**, mined from Wiktionary
- **English pluralization**, Damian Conway
- **Spanish verb inflection**, Fred Jehle
- **French verb inflection**, Bob Salita
- **LIBSVM**, Chih-Chung Chang & Chih-Jen Lin
- **LIBLINEAR**, Rong-En Fan et al.
- **spelling corrector**, Peter Norvig

Acknowledgements
----------------

**Authors:**

- Tom De Smedt (tom@organisms.be)
- Walter Daelemans (walter.daelemans@ua.ac.be)

**Contributors (chronological):**

- Frederik De Bleser
- Jason Wiener
- Daniel Friesen
- Jeroen Geertzen
- Thomas Crombez
- Ken Williams
- Peteris Erins
- Rajesh Nair
- F. De Smedt
- Radim Řehůřek
- Tom Loredo
- John DeBovis
- Thomas Sileo
- Gerold Schneider
- Martin Volk
- Samuel Joseph
- Shubhanshu Mishra
- Robert Elwell
- Fred Jehle
- Antoine Mazières + fabelier.org
- Rémi de Zoeten + closealert.nl
- Kenneth Koch
- Jens Grivolla
- Fabio Marfia
- Steven Loria
- Colin Molter + tevizz.com
- Peter Bull
- Maurizio Sambati
- Dan Fu
- Salvatore Di Dio
- Vincent Van Asch
- Frederik Elwert
