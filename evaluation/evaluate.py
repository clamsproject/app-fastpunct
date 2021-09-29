"""evaluate.py

reque
$ python3 evaluate.py GOLD_TRANSCRIPT

"""


import sys

from fastpunct import FastPunct
from curses import ascii


def evaluate(gold_transcript):
    fp = FastPunct()
    text_gold = open(gold_transcript).read()
    text_gold_paras = text_gold.split('\n\n')
    text_stripped_paras = [strip_punctuation(t) for t in text_gold_paras]
    text_fastpunct_paras = [fp.punct(t) for t in text_stripped_paras]
    text_stripped = ' '.join(text_stripped_paras)
    text_fastpunct = ' '.join(text_fastpunct_paras)
    print('=' * 80)
    print(text_gold)
    print('=' * 80)
    print(text_stripped)
    print('=' * 80)
    print(text_fastpunct)
    print('=' * 80)
    print(levenshtein_distance(text_gold, text_stripped))
    print(levenshtein_distance(text_gold, text_fastpunct))


def strip_punctuation(text):
    tokens = []
    for token in text.split():
        token = token.lower()
        if ascii.ispunct(token[-1]):
            token = token[:-1]
        tokens.append(token)
    return ' '.join(tokens)


## Copied from ../align.py

def levenshtein_distance(a, b):
    """Compute the Levenshtein edit distance between the sequences a and b."""
    m = len(a) + 1
    n = len(b) + 1

    d = [[0]*n for _ in range(m)]
    for i in range(m): d[i][0] = i # deletion
    for j in range(n): d[0][j] = j # insertion

    for i in range(1, m):
        for j in range(1, n):
            if a[i-1] == b[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j] + 1, # deletion
                              d[i][j-1] + 1, # insertion
                              d[i-1][j-1] + 1) # substitution
    return d[m-1][n-1]


if __name__ == '__main__':

    evaluate(sys.argv[1])
