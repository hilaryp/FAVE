#!/usr/bin/env python -O
# encoding: UTF-8

from syllabify import syllabify
from stem import stem_infl as STEM

TENSERS = frozenset(['M', 'N', 'S', 'TH', 'F'])
NEGATIVE_EXCEPTIONS = frozenset(['AM', 'RAN', 'SWAM', 'MATH', 'EXAM', 'ALAS', 'FAMILY',
                       'FAMILIES', "FAMILY'S", 'CATHOLIC', 'CATHOLICS',
                       'CAMERA', 'CATHERINE', "CATHERINE'S", 'ASPECT', 'ASPECTS', 
                       'ASPIRIN', 'ASPIRINS', 'FANTASTIC', 'RASCAL', 'RASCALS'])
POSITIVE_EXCEPTIONS = frozenset(['BAD', 'BADLY', 'BADDER', 'BADDEST', 'BADNESS', 
                       'BADMINTON', 'BADMINTONS', 'MAD', 'MADLY', 'MADDEN', 
                       'MADDENING', 'MADDENINGLY', 'MADDER', 'MADNESS', 'GLAD',
                       'GLADLY', 'GLADDER', 'GLADDEST', 'GLADDEN', 
                       'GLADDENING', 'GLADNESS', 'GRANDMOTHER', 'GRANDMOTHERS',
                       "GRANDMOTHER'S", 'GRANDMA', 'SANTA', 'SANTAS', "SANTA'S",
                       'BATHROOM'])
# TASKER candidate for pos exception, but should be ok with stemming changes
UNCLASSIFIABLE = frozenset(['CAN', 'BEGAN', 'ANNE', 'ANNIE'])


def is_penultimate_syllable_resyllabified(word):
    """
    Use a Porter stemmer to decompose words into "stem" and "suffix", and 
    return True iff last syllable is a candidate for resyllabification
    opacifying tensing
    """
    stem = STEM(word)
    # find the rightmost point where wordform and its stem don't match
    sp = len(stem) - 1
    while sp >= 0 and word[sp] != stem[sp]:
        sp -= 1
    # define the suffix to be the residue
    suffix = word[sp + 1:].upper()
    # check for /-z/, /-iŋ/, or /-iŋ-z/ therein
    if suffix.endswith(("ED", "ES", "ING")):
        return True
    return False


def is_tense(word, pron):
    """
    True iff word `word` with pronuciation `pron` (represented as a list of
    ARPABET characters) has a tense short-a in the first syllable in the 
    "classic" Philadelphia pattern. The algorithm (for lack of a better
    term) is as follows:
    
    * Check whether the word is a positive exception to tensing: if so
      return True
    * Check whether the word is a negative exception to tensing: if so
      return False
    * Check whether the word is an indeterminate word (at the moment, just
      "CAN"): if so return None
    * Syllabify and extract the onset, nucleus, and coda of the first 
      syllable
    * Check whether the first-syllable nucleus is r-colored: if so return 
      False
    * Check whether the first coda consonant of the first syllable is 
      a tensing segment: if so return True
    * Check whether the word is two syllables, has an empty penultimate
      coda, but has an ultimate onset consisting of a tensing segment
      and ends in a suffix that triggers resyllabification in the classic
      system: so return True
    * Return False

    Load CMU dictionary for testing (requires internet connection)
    NB: this does not have appropriate handling for words with multiple
    dictionary entries

    >>> pron = {}
    >>> for line in open("dict", "r"):
    ...     if line.startswith(';'):
    ...         continue
    ...     (word, pron_string) = line.rstrip().split('  ', 1)
    ...     pron[word] = pron_string.split()
    >>> pron['GLADDEST'] = pron['GLAD'] + ['EH0', 'S', 'T']

    Positive exceptions:
    >>> is_tense('MADDER', pron['MADNESS'])
    True
    >>> is_tense('BADNESS', pron['BADNESS'])
    True
    >>> is_tense('GLADDEST', pron['GLADDEST'])
    True

    Negative exceptions:
    >>> is_tense('RAN', pron['RAN'])
    False
    >>> is_tense('SWAM', pron['SWAM'])
    False
    >>> is_tense('MATH', pron['MATH'])
    False
    >>> is_tense('SAD', pron['SAD'])
    False
    
    Tautosyllabic /m, n/:
    >>> is_tense('HAND', pron['HAND'])
    True
    >>> is_tense('HAM', pron['HAM'])
    True

    Tautosyllabic /f, θ, s/:
    >>> is_tense('HALF', pron['HALF'])
    True
    >>> is_tense('PATH', pron['HALF'])
    True
    >>> is_tense('PASS', pron['PASS'])
    True

    Closed syllables that go without:
    >>> is_tense('CASH', pron['CASH'])
    False
    >>> is_tense('BANG', pron['BANG'])
    False
    >>> is_tense('BAT', pron['BAT'])
    False
    >>> is_tense('PAL', pron['PAL'])
    False
    >>> is_tense('BAG', pron['BAG'])
    False
    >>> is_tense('CAB', pron['CAB'])
    False

    Open syllables:
    >>> is_tense('HAMMER', pron['HAMMER'])
    False
    >>> is_tense('MANAGE', pron['MANAGE'])
    False
    >>> is_tense('PLANET', pron['PLANET'])
    False
    >>> is_tense('PLANETS', pron['PLANETS'])
    False

    Opaque tensing in (re)open(ed) syllables:
    >>> is_tense('MANNING', pron['MANNING'])
    True
    >>> is_tense('CLASSES', pron['CLASSES'])
    True
    >>> is_tense('ASKING', pron['ASKING'])
    True
    >>> is_tense("PASSIN'", pron["PASSIN'"]) # Did we catch -in' transcriptions?
    True

    (lexically) Unclassifiable:
    >>> is_tense('CAN', pron['CAN'])
    >>> is_tense('BEGAN', pron['BEGAN'])
    >>> is_tense('ANNE', pron['ANNE'])

    Formerly unclassifiable sC:
    >>> is_tense('ASPECT', pron['ASPECT'])
    False
    >>> is_tense('CASKET', pron['CASKET'])
    True
    >>> is_tense('ASKED', pron['ASKED'])
    True
    >>> is_tense('BASKETBALL', pron['BASKETBALL'])
    True
    

    Previously incorrectly marked as "unclassifiable":
    >>> is_tense('BANDSTAND', pron['BANDSTAND'])
    True
    >>> is_tense('BACKSTROKE', pron['BACKSTROKE'])
    False
    
    Previously incorrectly marked as 'lax':
    >>> is_tense('PROGRAM', pron['PROGRAM'][5:])
    True
    >>> is_tense('TRANSFER', pron['TRANSFER'])
    True
 
    not handled yet: schwa-apocope (e.g., CAMERA), SANTA (when /t/ deleted)
    """
    if word.endswith("IN'"):
        word = word[:-1] + 'G'
    # check lexical exceptions
    if word in UNCLASSIFIABLE:
        return None
    if word in POSITIVE_EXCEPTIONS:
        return True
    if word in NEGATIVE_EXCEPTIONS:
        return False    
    # parse syllables, with "Alaska rule" ON 
    syls = syllabify(pron)
    (onset, nucleus, coda) = syls[0]
    # in my syllable-parsing scheme, 'r' is parsed into the nucleus in 
    # certain contexts; in this case the vowel is lax regardless of the 
    # coda's contents
    if len(nucleus) > 1 and nucleus[1] == 'R':
        return False
    # check for tautosyllabic tensing segment at the start of the coda
    if len(coda) > 0:
        if coda[0] in TENSERS:
            return True
    # check for the possibility of resyllabification opacifying tensing
    if len(syls) == 2 and coda == []:
        if is_penultimate_syllable_resyllabified(word):
            resyl_onset = syls[1][0]
            if len(resyl_onset) == 1 and resyl_onset[0] in TENSERS:
                return True
    return False
    


if __name__ == '__main__':
    import doctest
    doctest.testmod()
