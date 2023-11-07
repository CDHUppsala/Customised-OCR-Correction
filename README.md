# Customised-OCR-Correction
A word-list based OCR post-correction, originally designed for historical medical text

This is a re-implementation of Thompson et al.'s algorithm for OCR post-correction. The implementation is built on the spellchecker "pyspellchecker". "Customised" refers to that suggested corrections are only used if their frequency in the OCR:ed corpus exceeds a cut-off. As a default, a cut-off of 2 is used, (i.e., at least two occurrences are required).

The type of OCR:ed corpus that the algorithm targets is one with a high quality OCR output, but for which it might be relevant to correct some remaining errors.

User-made word lists can be used for the correction. The spellchecker only has built-in word lists for a few languages, so for most languages, user-made word lists are required.

There are some additions to the original algorithm:
a) A word is not replaced if the frequency of the original word is higher than the frequency for the spellcheckar's suggestion for replacement
b) A compound splitting of words is also performed by t
c) The algorithm also attempts to locate words that are written with white space between characters and change these to words in which the charachters are not separated by white space.



## Programming libraries needed
pip install pyspellchecker

conda install -c anaconda nltk

conda install -c conda-forge matplotlib

(Read more about the spell checker: https://pyspellchecker.readthedocs.io)
