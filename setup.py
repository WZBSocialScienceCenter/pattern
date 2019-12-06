#### PATTERN #######################################################################################

from __future__ import print_function

import sys
import os

from io import open

from setuptools import setup

from pattern import __version__


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

#---------------------------------------------------------------------------------------------------
# "python setup.py zip" will create the zipped distribution and checksum.

if sys.argv[-1] == "zip":

    import zipfile
    import hashlib
    import re

    n = "patternlite-%s.zip" % __version__
    p = os.path.join(os.path.dirname(os.path.realpath(__file__)))
    z = zipfile.ZipFile(os.path.join(p, "..", n), "w", zipfile.ZIP_DEFLATED)
    for root, folders, files in os.walk(p):
        for f in files:
            f = os.path.join(root, f)
            # Exclude revision history (.git).
            # Exclude development files (.dev).
            if not re.search(r"\.DS|\.git[^i]|\.pyc|\.dev|tmp", f):
                z.write(f, os.path.join("patternlite-" + __version__, os.path.relpath(f, p)))
    z.close()
    print(n)
    print(hashlib.sha256(open(z.filename).read()).hexdigest())
    sys.exit(0)

#---------------------------------------------------------------------------------------------------
# "python setup.py install" will install /pattern in /site-packages.

setup(
            name = "PatternLite",
         version = __version__,
     description = "Stripped down, forked version of Pattern package (Web mining module for Python.)",
    long_description=long_description,
    long_description_content_type='text/markdown',
         license = "BSD",
          author = "Markus Konrad",
    author_email = "markus.konrad@wzb.eu",
             url = "https://github.com/WZBSocialScienceCenter/patternlite",
        packages = [
        "pattern",
        "pattern.db",
        "pattern.text",
        "pattern.text.de",
        "pattern.text.en",
        "pattern.text.en.wordlist",
        "pattern.text.en.wordnet",
        "pattern.text.ru",
        "pattern.text.ru.wordlist",
        "pattern.text.es",
        "pattern.text.fr",
        "pattern.text.it",
        "pattern.text.nl",
        "pattern.vector",
        "pattern.vector.svm"
    ],
    package_data = {
        "pattern.text.de"         : ["*.txt", "*.xml"],
        "pattern.text.en"         : ["*.txt", "*.xml", "*.slp"],
        "pattern.text.en.wordlist": ["*.txt"],
        "pattern.text.en.wordnet" : ["*.txt", "dict/*"],
        "pattern.text.ru": ["*.txt", "*.xml", "*.slp"],
        "pattern.text.ru.wordlist": ["*.txt"],
        "pattern.text.es"         : ["*.txt", "*.xml"],
        "pattern.text.fr"         : ["*.txt", "*.xml"],
        "pattern.text.it"         : ["*.txt", "*.xml"],
        "pattern.text.nl"         : ["*.txt", "*.xml"],
        "pattern.vector"          : ["*.txt"],
        "pattern.vector.svm"      : ["*.txt"],
    },
    py_modules = [
        "pattern.metrics",
        "pattern.helpers",
        "pattern.text.search",
        "pattern.text.tree"
    ],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: Dutch",
        "Natural Language :: English",
        "Natural Language :: French",
        "Natural Language :: German",
        "Natural Language :: Italian",
        "Natural Language :: Spanish",
        "Operating System :: OS Independent",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires='>=3.6',
    install_requires = [
        "numpy",
        "scipy",
        "nltk",
    ],
    zip_safe = False
)
