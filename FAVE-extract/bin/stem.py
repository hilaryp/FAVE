#!/usr/bin/env python -O
#
# Copyright (c) 2013-2014 Kyle Gorman
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Regarding the licensing of this code, this is loosely based off the NLTK
# implementation by Vivake Gupta, which bears a GPL 2.0 license, but also
# the "GNU Linking Exception".
#
# stem.py: Porter stemmer implementation


"""
Porter Stemmer utilities

This is the Porter stemming algorithm, ported to Python from ANSI C. It
follows loosely the algorithm in:

M. Porter. 1980. An algorithm for suffix stripping. Program 14(3): 130-137.

`stem_infl` applies steps 1a and 1b of the Porter stemmer, preserving the 
casing of the input. While there is code for steps 1c and 2-5 here, they 
are not used, nor have they been subject to careful testing.
"""


from string import ascii_uppercase


VOWELS = frozenset("aeiou")
EXCEPTIONS = {# from Vivake Gupta:
              "dying": "die",
              "lying": "lie",
              "news":  "news",
              "sky":   "sky", "skies": "sky",
              "tying": "tie",
              "inning":  "inning",  "innings":  "inning",
              "outing":  "outing",  "outings":  "outing",
              "canning": "canning", "cannings": "canning",
              # from Hiranmay Ghosh:
              "exceed":  "exceed",
              "proceed": "proceed",
              "succeed": "succeed",
              # from Metrah Mohammed:
              "anything":   "anything",
              "everything": "everything",
              "nothing":    "nothing",
              "something":  "something"}
STOPLIST = frozenset("don't won't ain't let's".split())


def _cons(word, i):
    """
    cons(i) is TRUE <=> b[i] is a consonant.
    """
    if word[i] in VOWELS:
        return False
    if word[i] == 'y':
        if i == 0:
            return True
        else:
            return not _cons(word, i - 1)
    return True


def _m(word, j):
    """
    m() measures the number of consonant sequences between k0 and j.
    If c is a consonant sequence and v a vowel sequence, and <..>
    indicates arbitrary presence,

       <c><v>       gives 0
       <c>vc<v>     gives 1
       <c>vcvc<v>   gives 2
       <c>vcvcvc<v> gives 3
       ...
    """
    n = i = 0
    while True:
        if i > j:
            return n
        if not _cons(word, i):
            break
        i += 1
    i += 1
    while True:
        while True:
            if i > j:
                return n
            if _cons(word, i):
                break
            i += 1
        i += 1
        n += 1
        while True:
            if i > j:
                return n
            if not _cons(word, i):
                break
            i += 1
        i += 1


def _vowelinstem(stem):
    """
    vowelinstem(stem) is TRUE <=> stem contains a vowel
    """
    for i in range(len(stem)):
        if not _cons(stem, i):
            return True
    return False


def _doublec(word):
    """
    doublec(word) is TRUE <=> word ends with a double consonant
    """
    if len(word) < 2:
        return False
    if word[-1] != word[-2]:
        return False
    return _cons(word, len(word) - 1)


def _cvc(word, i):
    """
    cvc(i) is TRUE iff

    a) i == 1, and word[0] word[1] is vowel consonant, or

    b) word[i - 2], word[i - 1], word[i] has the form CVC and also if
       the second C is not w, x or y. This is used when trying to
       restore an e at the end of a short word. E.g.: cav(e), lov(e),
       hop(e), crim(e), but snow, box, tray.
    """
    if i == 0:
        return False  # i == 0 never happens perhaps
    if i == 1:
        return not _cons(word, 0) and _cons(word, 1)
    if not _cons(word, i) or _cons(word, i - 1) or not _cons(word, i - 2):
        return False
    ch = word[i]
    if ch in "wxy":
        return False
    return True


def _step1ab(word):
    """
    step1ab() gets rid of plurals and -ed or -ing. E.g.:

    >>> _step1ab("caresses")
    'caress'
    >>> _step1ab("caress")
    'caress'
    >>> _step1ab("ponies")
    'poni'
    >>> _step1ab("pony")
    'poni'
    >>> _step1ab("sties")
    'sti'
    >>> _step1ab("tie")
    'tie'
    >>> _step1ab("cats")
    'cat'
    >>> _step1ab("feed")
    'feed'
    >>> _step1ab("agreed")
    'agree'
    >>> _step1ab("disabled")
    'disable'
    >>> _step1ab("matting")
    'mat'
    >>> _step1ab("mating")
    'mate'
    >>> _step1ab("meeting")
    'meet'
    >>> _step1ab("meetings")
    'meet'
    >>> _step1ab("milling")
    'mill'
    >>> _step1ab("messing")
    'mess'
    """
    if word[-1] == "s":
        if word.endswith("sses"):
            word = word[:-2]
        elif word.endswith("ies"):
            if len(word) == 4:
                word = word[:-1]
            # this line extends the original algorithm, so that 
            # 'flies'->'fli' but 'dies'->'die' etc
            else:
                word = word[:-2]
        elif word[-2] != "s":
            word = word[:-1]
    ed_or_ing_trimmed = False
    if word.endswith("ied"):
        if len(word) == 4:
            word = word[:-1]
        else:
            word = word[:-2]
    # this line extends the original algorithm, so that
    # 'spied'->'spi' but 'died'->'die' etc
    elif word.endswith("eed"):
        if _m(word, len(word) - 4) > 0:
            word = word[:-1]
    elif word.endswith("ed") and _vowelinstem(word[:-2]):
        word = word[:-2]
        ed_or_ing_trimmed = True
    elif word.endswith("ing") and _vowelinstem(word[:-3]):
        word = word[:-3]
        ed_or_ing_trimmed = True
    if ed_or_ing_trimmed:
        if word.endswith(("at", "bl", "iz")):
            word += 'e'
        elif _doublec(word):
            if word[-1] not in "lsz":
                word = word[:-1]
        elif _m(word, len(word) - 1) == 1 and _cvc(word, len(word) - 1):
            word += 'e'
    return word


def _step1c(word):
    """
    step1c() turns terminal y to i when there is another vowel in the stem.

    This has been modified from the original Porter algorithm so that
    y -> i is only done when y is preceded by a consonant, but not if the
    stem is only a single consonant.

    >>> _step1c("happy")
    'happi'
    >>> _step1c("enjoy")
    'enjoy'

    This is a much better rule. Formerly 'enjoy' -> 'enjoi' and
    'enjoyment' -> 'enjoy'. Step 1c is perhaps done too soon; but with this
    modification that no longer really matters.

    Also, the removal of the vowelinstem(z) condition means that words like
    "spy", etc. conflate with "spied", etc.

    >>> _step1c("spy")
    'spi'
    >>> _step1c("fly")
    'fli'
    >>> _step1c("try")
    'tri'
    """
    if word[-1] == "y" and len(word) > 2 and _cons(word, len(word) - 2):
        return word[:-1] + "i"
    else:
        return word


def _step2(word):
    """
    step2() maps double suffices to single ones. So -ization (= -ize
    plus -ation) maps to -ize etc. Note that the string before the
    suffix must give m() > 0.
    """
    if len(word) <= 1:
        # Only possible at this stage given unusual inputs to stem_word
        # like 'oed'
        return word
    ch = word[-2]
    if ch == 'a':
        if word.endswith("ational"):
            return word[:-7] + "ate" if _m(word, len(word) - 8) > 0 \
                else word
        elif word.endswith("tional"):
            return word[:-2] if _m(word, len(word) - 7) > 0 \
                else word
        else:
            return word
    elif ch == 'c':
        if word.endswith("enci"):
            return word[:-4] + "ence" if _m(word, len(word) - 5) > 0 \
                else word
        elif word.endswith("anci"):
            return word[:-4] + "ance" if _m(word, len(word) - 5) > 0 \
                else word
        else:
            return word
    elif ch == 'e':
        if word.endswith("izer"):
            return word[:-1] if _m(word, len(word) - 5) > 0 \
                else word
        else:
            return word
    elif ch == 'l':
        if word.endswith("bli"):
            return word[:-3] + "ble" if _m(word, len(word) - 4) > 0 \
                else word
        # To match the published algorithm, replace "bli" with "abli" and
        # "ble" with "able"
        elif word.endswith("alli"):
            if _m(word, len(word) - 5) > 0:
                word = word[:-2]
                return _step2(word)
            else:
                return word
        elif word.endswith("fulli"):
            return word[:-2] if _m(word, len(word) - 6) else word
        elif word.endswith("entli"):
            return word[:-2] if _m(word, len(word) - 6) else word
        elif word.endswith("eli"):
            return word[:-2] if _m(word, len(word) - 4) else word
        elif word.endswith("ousli"):
            return word[:-2] if _m(word, len(word) - 6) else word
        else:
            return word
    elif ch == 'o':
        if word.endswith("ization"):
            return word[:-7] + "ize" if _m(word, len(word) - 8) \
                else word
        elif word.endswith("ation"):
            return word[:-5] + "ate" if _m(word, len(word) - 6) \
                else word
        elif word.endswith("ator"):
            return word[:-4] + "ate" if _m(word, len(word) - 5) \
                else word
        else:
            return word
    elif ch == 's':
        if word.endswith("alism"):
            return word[:-3] if _m(word, len(word) - 6) \
                else word
        elif word.endswith("ness"):
            if word.endswith("iveness"):
                return word[:-4] if _m(word, len(word) - 8) \
                    else word
            elif word.endswith("fulness"):
                return word[:-4] if _m(word, len(word) - 8) \
                    else word
            elif word.endswith("ousness"):
                return word[:-4] if _m(word, len(word) - 8) \
                    else word
            else:
                return word
        else:
            return word
    elif ch == 't':
        if word.endswith("aliti"):
            return word[:-3] if _m(word, len(word) - 6) \
                else word
        elif word.endswith("iviti"):
            return word[:-5] + "ive" if _m(word, len(word) - 6) \
                else word
        elif word.endswith("biliti"):
            return word[:-6] + "ble" if _m(word, len(word) - 7) \
                else word
        else:
            return word
    elif ch == 'g':
        if word.endswith("logi"):
            return word[:-1] if _m(word, len(word) - 4) else word
        # To match the published algorithm, pass len(word) - 5 to _m
        # instead of len(word) - 4
        else:
            return word
    else:
        return word


def _step3(word):
    """
    step3() deals with -ic-, -full, -ness etc. similar strategy to step2.
    """
    ch = word[-1]
    if ch == "e":
        if word.endswith("icate"):
            return word[:-3] if _m(word, len(word) - 6) else word
        elif word.endswith("ative"):
            return word[:-5] if _m(word, len(word) - 6) else word
        elif word.endswith("alize"):
            return word[:-3] if _m(word, len(word) - 6) else word
        else:
            return word
    elif ch == "i":
        if word.endswith("iciti"):
            return word[:-3] if _m(word, len(word) - 6) else word
        else:
            return word
    elif ch == "l":
        if word.endswith("ical"):
            return word[:-2] if _m(word, len(word) - 5) else word
        elif word.endswith("ful"):
            return word[:-3] if _m(word, len(word) - 4) else word
        else:
            return word
    elif ch == "s":
        if word.endswith("ness"):
            return word[:-4] if _m(word, len(word) - 5) else word
        else:
            return word
    else:
        return word


def _step4(word):
    """
    step4() takes off -ant, -ence etc., in context <c>vcvc<v>.
    """
    if len(word) <= 1:
        # Only possible at this stage given unusual inputs to stem_word
        # like 'oed'
        return word
    ch = word[-2]
    if ch == "a":
        if word.endswith("al"):
            return word[:-2] if _m(word, len(word) - 3) > 1 else word
        else:
            return word
    elif ch == "c":
        if word.endswith("ance"):
            return word[:-4] if _m(word, len(word) - 5) > 1 else word
        elif word.endswith("ence"):
            return word[:-4] if _m(word, len(word) - 5) > 1 else word
        else:
            return word
    elif ch == "e":
        if word.endswith("er"):
            return word[:-2] if _m(word, len(word) - 3) > 1 else word
        else:
            return word
    elif ch == "i":
        if word.endswith("ic"):
            return word[:-2] if _m(word, len(word) - 3) > 1 else word
        else:
            return word
    elif ch == "l":
        if word.endswith("able"):
            return word[:-4] if _m(word, len(word) - 5) > 1 else word
        elif word.endswith("ible"):
            return word[:-4] if _m(word, len(word) - 5) > 1 else word
        else:
            return word
    elif ch == "n":
        if word.endswith("ant"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        elif word.endswith("ement"):
            return word[:-5] if _m(word, len(word) - 6) > 1 else word
        elif word.endswith("ment"):
            return word[:-4] if _m(word, len(word) - 5) > 1 else word
        elif word.endswith("ent"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    elif ch == "o":
        if word.endswith("sion") or word.endswith("tion"):
            # slightly different logic to all the other cases
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        elif word.endswith("ou"):
            return word[:-2] if _m(word, len(word) - 3) > 1 else word
        else:
            return word
    elif ch == "s":
        if word.endswith("ism"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    elif ch == "t":
        if word.endswith("ate"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        elif word.endswith("iti"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    elif ch == "u":
        if word.endswith("ous"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    elif ch == "v":
        if word.endswith("ive"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    elif ch == "z":
        if word.endswith("ize"):
            return word[:-3] if _m(word, len(word) - 4) > 1 else word
        else:
            return word
    else:
        return word


def _step5(word):
    """
    step5() removes a final -e if m() > 1, and changes -ll to -l if
    m() > 1.
    """
    if word[-1] == "e":
        a = _m(word, len(word) - 1)
        if a > 1 or (a == 1 and not _cvc(word, len(word) - 2)):
            word = word[:-1]
    if word.endswith("ll") and _m(word, len(word) - 1) > 1:
        word = word[:-1]
    return word


def stem_word(word):
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if len(word) <= 2:
        return word
    # Strings of length 1 or 2 don't go through the stemming process,
    # though no mention is made of this in the published algorithm. Remove
    # these lines to match the published algorithm.
    word = _step1ab(word)
    word = _step1c(word)
    word = _step2(word)
    word = _step3(word)
    word = _step4(word)
    word = _step5(word)
    return word


def stem_word_infl(word):
    if word in EXCEPTIONS:
        return EXCEPTIONS[word]
    if len(word) <= 2:
        return word
    return _step1ab(word)


def _adjust_case(word, stem):
    """
    >>> _adjust_case("xTotallyRaNd0mwored", "xtotallyrand0mwor")
    'xTotallyRaNd0mwor'
    """
    return ''.join(chfold.upper() if ch in ascii_uppercase else chfold \
                   for (ch, chfold) in zip(word, stem))


def stem(word):
    return _adjust_case(word, stem_word(word.lower()))


def stem_infl(word):
    """
    Stem word using only "step 1" of the algorithm (which focuses on
    regular inflectional suffixes) and reapply original case pattern to
    output.
    """
    return _adjust_case(word, stem_word_infl(word.lower()))


if __name__ == "__main__":
    import doctest
    doctest.testmod()
