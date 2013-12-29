#!/usr/bin/env python -O
# encoding: UTF-8

from syllabify import syllabify

# initialize stemmer
from decorators import Memoize
from porter import PorterStemmer
STEM = Memoize(PorterStemmer().stem)


TENSERS = {'M', 'N', 'S', 'TH', 'F'}
NEGATIVE_EXCEPTIONS = {'AM', 'RAN', 'SWAM', 'MATH', 'EXAM', 'ALAS', 'FAMILY',
                       'FAMILIES', "FAMILY'S", 'CATHOLIC', 'CATHOLICS',
                       'CAMERA', 'CATHERINE'}
POSITIVE_EXCEPTIONS = {'BAD', 'BADLY', 'BADDER', 'BADDEST', 'BADNESS', 
                       'BADMINTON', 'BADMINTONS', 'MAD', 'MADLY', 'MADDEN', 
                       'MADDENING', 'MADDENINGLY', 'MADDER', 'MADNESS', 'GLAD',
                       'GLADLY', 'GLADDER', 'GLADDEST', 'GLADDEN', 
                       'GLADDENING', 'GLADNESS', 'GRANDMOTHER', 'GRANDMOTHERS',
                       "GRANDMOTHER'S", 'GRANDMA', 'SANTA', 'SANTAS', "SANTA'S",
                       'BASKET', 'BASKETS', 'BASKETRY', "BASKET'S",
                       'BASKETMAKER', 'BASKETMAKING', 'BASKETBALL', 
                       'BASKETBALLS', "BASKETBALL'S", 'TASKER'}
UNCLASSIFIABLE = {'CAN', 'BEGAN', 'ANNE', 'ANNIE'}


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
    if suffix and suffix.endswith(('ES', 'ING', 'INGS')):
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

    >>> from urllib2 import urlopen
    >>> DICT = 'http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict.0.7a'
    >>> pron = {}
    >>> for line in urlopen(DICT):
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

    Tensing blocked in r-colored nuclei:
    >>> is_tense('BARS', pron['BARS'])
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

    (lexically) Unclassifiable:
    >>> is_tense('CAN', pron['CAN'])
    >>> is_tense('BEGAN', pron['BEGAN'])
    >>> is_tense('ANNE', pron['ANNE'])

    Unclassifiable:
    >>> is_tense('ASPECT', pron['ASPECT'])
    >>> is_tense('CASKET', pron['CASKET'])
    >>> is_tense('ASTRO', pron['ASTRO'])

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
    # check lexical exceptions
    if word in UNCLASSIFIABLE:
        return None
    if word in POSITIVE_EXCEPTIONS:
        return True
    if word in NEGATIVE_EXCEPTIONS:
        return False    
    # parse syllables, with "Alaska rule" off
    syls = syllabify(pron, False)
    (onset, nucleus, coda) = syls[0]
    # in my syllable-parsing scheme, 'r' is parsed into the nucleus in 
    # certain contexts; in this case the vowel is lax regardless of the 
    # coda's contents
    if len(nucleus) > 1 and nucleus[1] == 'R':
        return False
    # code potential "Alaska rule" problems as UNCLASSIFIABLE if they
    # are not positive or negative exceptions already
    if len(syls) > 1:
        # true if there is a following syllable
        next_onset = syls[1][0]
        if len(syls[0][2]) == 0 and len(next_onset) > 1:
            # coda is empty, onset is complex...may be a target of the Alaska rule
            if next_onset[0] == 'S': 
                # has at least two sounds in the next onset
                return None
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

