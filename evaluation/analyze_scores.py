"""analyze_scores.py

$ python test.py SCORE_FILE

Reads the file with scores and looks at ratios, the input lines look like:

>>>   21  0.91  And yes, I could do it.
>>>   49  0.98  Would be as good stuff I was two of a fragile pro.

The first number is the length of the input in characters and the second the
ration of thelength of the input and the length of the output.

This is to help find candidates where the fastpunct processing went rogue,
candidates are cases with a ratio < 0.9 and a input length > 10.

"""

import sys


def analyze_scores(fname):
    for line in open(fname):
        if not line.startswith('>>>'):
            continue
        fields = line.strip().split()
        length = int(fields[1])
        score = float(fields[2])
        if score < 0.9 and length > 10:
            print(fields)


if __name__ == '__main__':
    
    analyze_scores(sys.argv[1])
