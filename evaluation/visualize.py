"""visualize.py

$ python3 visualize.py MMIF_FILE HTML_FILE

Takes the MMIF file and creates an HTML file with the displacy visualization.

You need an environment with the spacy module installed.

We run this on the output of the following two chains:

- Kaldi --> spaCy NER
- Kaldi --> fastpunct --> spaCy NER

$ python visualize.py tomato-kaldi-spacy.json tomato-kaldi-spacy.html
$ python visualize.py tomato-kaldi-fastpunct-spacy.json tomato-kaldi-fastpunct-spacy.html

The two MMIF input files above were created as follows:

- tomato-kaldi-spacy.json
    run the spaCy app over example-input.json
- tomato-kaldi-fastpunct-spacy.json
    run the spaCy app over example-output.json

"""


import sys
import json

from spacy import displacy


def create_html(infile, outfile):
    mmif_obj = json.load(open(infile))
    text_docs = get_text_documents(mmif_obj)
    spacy_view = get_spacy_view(mmif_obj)
    entities = []
    doc_id = None
    docs_found = set()
    for annotation in spacy_view['annotations']:
        attype = annotation['@type']
        if 'NamedEntity' in attype:
            doc_id = annotation['properties']['document']
            docs_found.add(annotation['properties']['document'])
            entities.append({"start": annotation['properties']['start'],
                             "end": annotation['properties']['end'],
                             "label": annotation['properties']['category']})
    if len(docs_found) > 1:
        print("ERROR: found more than one document referred to from NE")
        exit()
    text = text_docs[doc_id]['properties']['text']['@value']
    ex = [{"text": text, "ents": entities, "title": None}]
    html = displacy.render(ex, style="ent", manual=True)
    with open(outfile, 'w') as fh:
        fh.write(html)
    

def get_text_documents(mmif_obj):
    """Returns a dictionary of all text documents, indexed on the identifier."""
    docs = {}
    for view in mmif_obj['views']:
        for annotation in view['annotations']:
            if 'TextDocument' in annotation['@type']:
                full_id = "%s:%s" % (view['id'], annotation['properties']['id'])
                docs[full_id] = annotation
    return docs


def get_spacy_view(mmif_obj):
    """Returns the most recent spaCY view. If spaCy runs on Kaldi output then there
    is just one single spaCy view, but if it ran on the output of fastpunct then
    there are two spaCy views, in which case we take the last of them because
    that one has the entities on the fastpunct data."""
    spacy_view = None
    for view in mmif_obj['views']:
        app = view['metadata']['app']
        if 'spacy' in app:
            spacy_view = view
    return spacy_view


if __name__ == '__main__':

    create_html(sys.argv[1], sys.argv[2])
