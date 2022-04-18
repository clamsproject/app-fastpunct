"""evaluate.py

Usage:

$ python3 evaluate.py GOLD_TRANSCRIPT

This takes a while because large models need to be loaded.

Results are written to standard output. Verbose output is written to
evaluation.dribble.txt

The standard output will look like this

Loading FastPunct...
Evaluating transcript-fragment.txt...
  Intro Good evening. Leading the news thi     40   234   239   0.98    22    14
  ROBERT MacNEIL: Good evening. In the new     81   487   492   0.99    43    24
  JUDY WOODRUFF: After the news summary, t     91   521  1008   0.52    37   515
  MacNEIL: The leading suspect in yesterda    131   754   967   0.78    42   537
                                              343  1996  2706   0.82   144  1090

It shows the following data for each segment in the text:
- the first 40 characters of each segment
- the number of tokens in the segment
- the length of the segment with punctuations removed
- the length of the segment after running fast[unct
- the ration of the two lengths
- the edit distance between the gold standard segment and the segment with all
  punctuation/capitalization removed
- the edit distance between the gold standard and the stripped segment after
  running fastpunct.

Note how the edit distance goes down for the first two segments and increases
massively for the last two segments. The former is what we expect, the latter is
because of an error in fastpunct where some texts give rise to duplicate strings.
This effect is also clearly visible in the ratio of the two lengths, and this
ratio can be used as a heauristic to check whether the result is acceptable.

"""


import os, sys, time, statistics

from fastpunct import FastPunct
from curses import ascii

print("Loading FastPunct...")
fp = FastPunct()


def evaluate(fname, timestamp):
    print("Evaluating %s..." % fname)
    text_gold = open(fname).read()
    text_gold_paras = text_gold.split('\n\n')
    fname1, fname2 = dribble_files(fname, timestamp)
    with open(fname1, 'w') as fh1, open(fname2, 'w') as fh2:
        results = [eval_paragraph(para, fh1, fh2) for para in text_gold_paras]
        fh2.write(totals_line(results) + '\n')
        print('  ' + totals_line(results))

def eval_paragraph(para, fh1, fh2):
    fh1.write("%s\n" % ('=' * 80))
    fh1.write("Evaluating paragraph of %d tokens...\n" % len(para.split()))
    stripped_para = strip_punctuation(para)
    processed_para = run_fastpunct(stripped_para)
    fh1.write("%s\n%s\n" % ("-" * 80, para))
    fh1.write("%s\n%s\n" % ("-" * 80, stripped_para))
    fh1.write("%s\n%s\n" % ("-" * 80, processed_para))
    ed_p1_p2 = levenshtein_distance(para, stripped_para)
    ed_p1_p3 = levenshtein_distance(para, processed_para)
    len_p2 = len(stripped_para)
    len_p3 = len(processed_para)
    ratio = len_p2 / len_p3
    fh1.write("%s\n" % ('-' * 80))
    fh1.write('distance p1-p2: %d\n' % ed_p1_p2)
    fh1.write('distance p1-p3: %d\n' % ed_p1_p3)
    status_line = paragraph_status_short(para, len_p2, len_p3, ratio, ed_p1_p2, ed_p1_p3)
    fh2.write("%s\n" % status_line)
    print('  ' + status_line)
    return (len(para.split()), len_p2, len_p3, ratio, ed_p1_p2, ed_p1_p3)

def strip_punctuation(text):
    tokens = []
    for token in text.split():
        token = token.lower()
        if ascii.ispunct(token[-1]):
            token = token[:-1]
        tokens.append(token)
    return ' '.join(tokens)

def dribble_files(fname, timestamp):
    printname = os.path.basename(fname)
    printname = os.path.splitext(printname)[0]
    fixit_prefix = 'fixit-fragments-'
    if printname.startswith(fixit_prefix):
        printname = printname[len(fixit_prefix):]
    return ('dribble-%s-%s-long.txt' % (timestamp, printname),
            'dribble-%s-%s-summary.txt' % (timestamp, printname))

def run_fastpunct(text_in):
    # This does the same as the method Segment.run_fastpunct() in the main
    # application in ../app.py.
    text_out = fp.punct(text_in)
    ratio = len(text_in) / len(text_out)
    if False:
        print('>>> %4d  %.2f  %s' % (len(text_in), ratio, text_out[:80]))
    # Undo all processing when we run into the nasty case where fastpunct
    # flips out on longer input with repetitions.
    if ratio < 0.95 and len(text_in.split()) > 10:
        text_out = text_in
    return text_out

def paragraph_status_short(para, len_p2, len_p3, ratio, ed_p1_p2, ed_p1_p3):
    text = para.replace('\n', '\\n ')[:40]
    size = len(para.split())
    return ("%-40s  %5d %5d %5d   %.2f %5d %5d"
            % (text, size, len_p2, len_p3, ratio, ed_p1_p2, ed_p1_p3))

def totals_line(results):
    return ("%40s  %5d %5d %5d   %.2f %5d %5d"
            % ('',
               sum([r[0] for r in results]),
               sum([r[1] for r in results]),
               sum([r[2] for r in results]),
               statistics.mean([r[3] for r in results]),
               sum([r[4] for r in results]),
               sum([r[5] for r in results])))


## Copied from ../align.py

def levenshtein_distance(a, b):
    """Compute the Levenshtein edit distance between the sequences a and b."""
    m = len(a) + 1
    n = len(b) + 1
    d = [[0]*n for _ in range(m)]
    for i in range(m): d[i][0] = i  # deletion
    for j in range(n): d[0][j] = j  # insertion
    for i in range(1, m):
        for j in range(1, n):
            if a[i-1] == b[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j] + 1,    # deletion
                              d[i][j-1] + 1,    # insertion
                              d[i-1][j-1] + 1)  # substitution
    return d[m-1][n-1]


if __name__ == '__main__':

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    for fname in sys.argv[1:]:
        evaluate(fname, timestamp)
