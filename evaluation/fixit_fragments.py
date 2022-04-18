"""fixit_fragments.py

Script to handle transcript data from the Fixit process.

The results are used to evaluate the fastpunct application.

"""

import os, re, json


DATA_DIR = ('/Users/marc/Dropbox/projects/CLAMS/data'
            '/transcripts/fixit/Transcripts_from_kaldi_and_crowdsourced')


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
    """This just keeps those files for which we have the Kaldi-created input and
    the reformatted Fixit output, non-formatted output is ignored."""
    filtered_files = {}
    for base, exts in files.items():
        if KALDI in exts and FIXIT in exts:
            filtered_files[base] = [KALDI, FIXIT]
    return filtered_files

def print_files(files):
    for base, exts in files.items():
        if KALDI in exts and FIXIT in exts:
            print(base)
            for x in exts:
                print('   ', x)

def extract_fragments_from_files(files):
    for base, exts in files.items():
        for ext in exts:
            if ext == FIXIT:
                fname = "%s-%s.json" % (base, ext)
                extract_fragments_from_file(base, fname)

def extract_fragments_from_file(base, fname):
    print(fname)
    path = os.path.join(DATA_DIR, fname)
    transcript = json.load(open(path))
    parts = transcript['parts']
    texts = []
    for part in parts:
        texts.append((part['start_time'], part['end_time'], part['text']))
    fragments = []
    fragment = []
    for text in texts:
        filtered_text = filter_text(text[2])
        fragment.append(filtered_text)
        if text[2].endswith('.'):
            fragments.append(fragment)
            fragment = []
    if fragment:
        fragments.append(fragment)
    fragments = [' '.join([text for text in para]) for para in fragments]
    with open("fixit-fragments-%s.txt" % base, 'w') as fh:
        for fragment in fragments:
            fh.write(fragment.strip() + "\n\n")
    return fragments

def filter_text(text):
    """This cuts out all the annotations like "[intro music]."""
    filtered_text = ''
    annotations = list(re.finditer(r"\[.*?\]", text))
    for annotation in reversed(annotations):
        p1, p2 = annotation.span()
        text = text[:p1] + text[p2:]
    text = ' '.join(text.split())
    return text


if __name__ == '__main__':

    files = collect_files(DATA_DIR)
    files = filter_files(files)
    #print_files(files)
    extract_fragments_from_files(files)
