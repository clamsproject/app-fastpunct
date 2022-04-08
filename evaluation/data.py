"""data.py

Script to handle transcript data from the Fixit process.

These are used to evaluate the fastpunct application.

"""

import os

DATA_DIR = \
    '/Users/marc/Dropbox/projects/CLAMS/data' \
    + '/transcripts/fixit/Transcripts_from_kaldi_and_crowdsourced'


# extensions of the Kaldi and Fixit files
KALDI = 'kaldi'
FIXIT = 'transcript-fixitplus-reformatted'


def collect_files(data_dir):
    files = {}
    for fname in sorted(os.listdir(data_dir)):
        if not fname.startswith('cpb'):
            continue
        path = fname[:-5].split('-')
        name = '-'.join(path[:4])
        ext = '-'.join(path[4:])
        files.setdefault(name, []).append(ext)
    return files


def filter_files(files):
    """This just keeps those files for which we have the Kaldi created input and
    the reformatted Fixit output, non-formatted output is ignored."""
    filtered_files = {}
    for fname, exts in files.items():
        if KALDI in exts and FIXIT in exts:
            filtered_files[fname] = [KALDI, FIXIT]
    return filtered_files


def print_files(files):
    for fname, exts in files.items():
        if KALDI in exts and FIXIT in exts:
            print(fname)
            for x in exts:
                print('   ', x)


def analyze_files(files):
    pass


if __name__ == '__main__':

    files = collect_files(DATA_DIR)
    files = filter_files(files)
    print_files(files)
    analyze_files(files)
