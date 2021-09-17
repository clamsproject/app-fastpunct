"""align.py

Aligning two sequences. The elements of the sequences are stings or string like
elements, it is not clear to me what interface for the class is expected in the
latter case.

"""


def align(a, b, d=-5, s=lambda x,y: x==y, key=lambda x: x, gap=None):
    """Find the globally optimal alignment between the two sequences a and b
    using gap penalty d and similarity function s, and return the aligned
    sequences. The similarity function is applied to the result of key(x)
    and key(y) for each x in a and y in b, and should return an integer;
    key defaults to the identity function.

    This implementation uses the Needleman-Wunsch algorithm."""
    m = len(a) + 1
    n = len(b) + 1

    # Rather than keeping a separate traceback matrix, we'll store (score, fun)
    # tuples in the alignment matrix, where fun is one of the following three
    # traceback functions.
    trace = [m-1, n-1] # decoding starts in the lower right-hand corner
    def diag(): trace[0] -= 1; trace[1] -= 1; return a[trace[0]], b[trace[1]]
    def up(): trace[0] -= 1; return a[trace[0]], gap
    def left(): trace[1] -= 1; return gap, b[trace[1]]

    # Initialize the alignment matrix.
    f = [[None]*n for _ in range(m)]
    f[0][0] = (0, lambda: None)
    for i in range(1, m): f[i][0] = (d*i, up)
    for j in range(1, n): f[0][j] = (d*j, left)

    # Compute the optimal alignment.
    for i in range(1, m):
        for j in range(1, n):
            f[i][j] = max((f[i-1][j-1][0] + s(key(a[i-1]), key(b[j-1])), diag),
                          (f[i-1][j][0] + d, up),   # a[i] -> gap
                          (f[i][j-1][0] + d, left), # b[j] -> gap
                          key=lambda x: x[0])

    # Decoding is now just a matter of running the stored traceback functions
    # until we get back to the upper left-hand corner.
    aligned_a = []; aligned_b = []
    while trace != [0, 0]:
        next_a, next_b = f[trace[0]][trace[1]][1]()
        aligned_a.append(next_a)
        aligned_b.append(next_b)
    aligned_a.reverse(); aligned_b.reverse()

    if isinstance(a, str) and isinstance(b, str):
        # Be nice and coerce the results back to strings.
        def default_gap(x): return x if x is not None else "-"
        return ("".join(map(default_gap, aligned_a)),
                "".join(map(default_gap, aligned_b)))
    return aligned_a, aligned_b


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


class Word(object):

    def __init__(self, string):
        self.text = string

    def x__str__(self):
        return self.text

    def x__getitem__(self, i):
        return self.text[i]

    def x__len__(self):
        return len(self.text)
    

if __name__ == '__main__':

    s0 = ['door', 'knob']
    s1 = ['door', 'knobs', 'are', 'out']
    s2 = ['doors', 'knobs', 'are', 'in']
    s3 = ['door', 's', 'knobs', 'were', 'in']
    s4 = ['door\'s', 'knobs', 'are', 'in']

    for x, y in [(s0, s1), (s1, s2), (s2, s3), (s2, s4), (s3, s4)]:
        print("\nAligning")
        print('  ', x)
        print('  ', y)
        result = align(x, y)
        print('   ==>')
        print('  ', ''.join(["%-20s" % e for e in result[0]]))
        print('  ', ''.join(["%-20s" % e for e in result[1]]))

    s1 = "hello this is jim lehrer with the newshour on pbs we have news about the tomato it has been observed recently that they dont taste good anymore".split()

    s2 = 'Hello, this is Jim Lehrer, with the newshour on BBC: "We have news about the tomato it has been observed recently that they don\'t taste good anymore.'.split()

    s1 = [Word(w) for w in s1]
    s2 = [Word(w) for w in s2]

    for x in align(s1, s2):
        print('>>>', ' '.join([str(w) for w in x]))
        
    first, second = align(s1, s2)
    #print('  ', ''.join(["%-10s" % str(e) for e in first]))
    #print('  ', ''.join(["%-10s" % e for e in second]))
    for x in zip(first, second):
        print(str(x[0].text), str(x[1].text))
