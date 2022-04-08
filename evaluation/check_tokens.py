"""check_tokens.py

Script to print a table with all Tokens and Spans in Kaldi and fastpunct views.

$ python check_tokens.py <mmif_file> <html_file>

The MMIF file is assumed to have a view with Kaldi and optionally fastpunct
views. It will print a table for each view with for each token the following
columns: (1) start offset, (2) end offsets, (3) word or text in the properties
dictionary, and (4) the text as gotten from taking the slice from the text.

This is for testing purposes, the last two columns should have the same content,
otherwise something went wrong.

TODO:

- Currently there is no check whether a view is from Kaldi or fastpunct and all
  views are treated equally and TOkens and Spans are printed for all views.

- It assumes that for tokens the document is on the annotation and for spans in
  the metadata, this will break no views that behave differently.

"""

import sys
import json

def check_tokens(fh_in, fh_out):
    mmif = json.load(fh_in)
    text_documents = {}
    for view in mmif['views']:
        tokens = []
        view_id = view['id']
        view_app = view['metadata']['app']
        sources = get_sources(view)
        print('VIEW', view_id, view_app)
        fh_out.write("<h3 id='%s'>%s &mdash; %s</h3>\n\n" % (view_id, view_id, view_app))
        write_navigation(fh_out, mmif)
        fh_out.write("<blockquote>\n")
        fh_out.write("<table cellspacing=0 cellpadding=5 border=1>\n")
        for annotation in view['annotations']:
            if 'TextDocument' in annotation['@type']:
                add_text_document(view_id, annotation, text_documents)
            elif 'Token' in annotation['@type']:
                add_token(annotation, tokens, text_documents)
            elif 'Span' in annotation['@type']:
                add_span(annotation, tokens, text_documents, sources[annotation['@type']])
        write_tokens(fh_out, view_id, view_app, tokens)
        fh_out.write("</table>\n")
        fh_out.write("</blockquote>\n")
    fh_out.write("<p id='end'/>\n")
    write_navigation(fh_out, mmif)

def get_sources(view):
    sources = {}
    for atype, contains in view['metadata']['contains'].items():
        if 'document' in contains:
            sources[atype] = contains['document']
    return sources

def add_text_document(view_id, annotation, text_documents):
    doc_id = "%s:%s" % (view_id, annotation['properties']['id'])
    text = annotation['properties']['text']['@value']
    print('TEXT', doc_id, len(text))
    text_documents[doc_id] = text

def add_token(annotation, tokens, text_documents):
    token = annotation['properties']['word']
    start = annotation['properties']['start']
    end = annotation['properties']['end']
    end = annotation['properties']['end']
    doc_id = annotation['properties']['document']
    span = text_documents[doc_id][start:end]
    tokens.append((token, start, end, span))

def add_span(annotation, tokens, text_documents, document):
    token = annotation['properties']['text']
    start = annotation['properties']['start']
    end = annotation['properties']['end']
    end = annotation['properties']['end']
    if 'document' in annotation['properties']:
        doc_id = annotation['properties']['document']
    else:
        doc_id = document
    span = text_documents[doc_id][start:end]
    tokens.append((token, start, end, span))

def write_navigation(fh_out, mmif):
    for view in mmif['views']:
        view_id = view['id']
        view_app = view['metadata']['app']
        fh_out.write("<a href='#%s'>%s</a><br/>\n" % (view_id, view_app))
    fh_out.write("<a href='#end'>end of file</a><br/>\n")

def write_tokens(fh_out, view_id, view_app, tokens):
    for token in tokens:
        fh_out.write("<tr>\n")
        fh_out.write("  <td>%s</td>\n" % token[1])
        fh_out.write("  <td>%s</td>\n" % token[2])
        fh_out.write("  <td>%s</td>\n" % token[0])
        fh_out.write("  <td>%s</td>\n" % token[3])
        fh_out.write("</tr>\n")


if __name__ == '__main__':
    
    infile = sys.argv[1]
    outfile = sys.argv[2]
    with open(infile) as fh_in, open(outfile, 'w') as fh_out:
        check_tokens(fh_in, fh_out)
    
