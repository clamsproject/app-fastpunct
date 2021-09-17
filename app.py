"""app.py

Adding punctuation and capitalization to Kaldi output.

Uses the fastpunct package which is built on top of the torch package for tensor
computation and neural networks.

Requirements

$ pip install clams-python==0.5.0
$ pip install fastpunct==2.0.2

"""

import os
import sys
import json
import urllib
import argparse
import collections

from clams.app import ClamsApp
from clams.restify import Restifier
from clams.appmetadata import AppMetadata
from mmif.serialize import Mmif
from mmif.vocabulary import DocumentTypes, AnnotationTypes
from lapps.discriminators import Uri

from fastpunct import FastPunct

from align import align


MMIF_VERSION = '0.4.0'
MMIF_PYTHON_VERSION = '0.4.5'
CLAMS_PYTHON_VERSION = '0.5.0'

APP_VERSION = '0.0.1'
APP_LICENSE = 'Apache 2.0'
ANALYZER_VERSION = '2.0.2'
ANALYZER_LICENSE = 'MIT License'


FASTPUNCT = FastPunct()


# Maximum pause between words allowed before we insert a segment boundary
MAX_PAUSE = 1000


class App(ClamsApp):

    def _appmetadata(self):
        metadata = AppMetadata(
            identifier='https://apps.clams.ai/fastpunct',
            url='https://github.com/clamsproject/app-fastpunct',
            name="FastPunct",
            description="Restore punctuation and capitalization after ASR.",
            app_version=APP_VERSION,
            app_license=APP_LICENSE,
            analyzer_version=ANALYZER_VERSION,
            analyzer_license=ANALYZER_LICENSE,
            mmif_version=MMIF_VERSION
        )
        metadata.add_input(DocumentTypes.TextDocument)
        metadata.add_input(AnnotationTypes.TimeFrame)
        metadata.add_input(AnnotationTypes.Alignment)
        metadata.add_input(Uri.TOKEN)
        # For now we are copying the TimeFrame instances. We don't really create
        # tokens, but spans over the text that are based on tokens, so using
        # AnnotationTypes.Span instead of Uri.TOKEN.
        metadata.add_output(DocumentTypes.TextDocument)
        metadata.add_output(AnnotationTypes.TimeFrame)
        metadata.add_output(AnnotationTypes.Alignment)
        metadata.add_output(AnnotationTypes.Span)
        return metadata

    def _annotate(self, mmif, **kwargs):
        #print(mmif.serialize(pretty=True))
        Identifiers.reset()
        self.mmif = mmif if type(mmif) is Mmif else Mmif(mmif)
        for view in list(self.mmif.views):
            annotation_types = [t.shortname for t in view.metadata.contains]
            kaldi_app = 'http://apps.clams.ai/aapb-pua-kaldi-wrapper'
            if view.metadata.app.startswith(kaldi_app):
                doc = self.mmif.get_documents_in_view(view.id)[0]
                doc_id = view.id + ':' + doc.id
                new_view = self._new_view()
                self._run_fastpunct(doc, view, new_view, doc_id)
        return self.mmif

    def _new_view(self, docid=None):
        view = self.mmif.new_view()
        view.metadata.app = self.metadata.identifier
        self.sign_view(view)
        # TODO: one question here is whether we should copy over the timeframes
        # since they are somewhat redundant, but having them included in the
        # view is a bit clearer. Also, think about what the values of document
        # should be for each new_contain.
        view.new_contain(DocumentTypes.TextDocument, document=docid)
        view.new_contain(AnnotationTypes.Span, document=docid)
        view.new_contain(AnnotationTypes.TimeFrame, document=docid)
        view.new_contain(AnnotationTypes.Alignment, document=docid)
        return view

    def _read_text(self, textdoc):
        """Read the text content from the document or the text value."""
        if textdoc.location:
            fh = urllib.request.urlopen(textdoc.location)
            text = fh.read().decode('utf8')
        else:
            text = textdoc.properties.text.value
        return text

    def _run_fastpunct(self, doc, view, new_view, full_doc_id):
        """Run the NLP tool over the document and add annotations to the view, using the
        full document identifier (which may include a view identifier) for the document
        property."""
        tokens, timeframes_idx, alignments_idx = self._get_annotations(view)
        timeframes = self._get_aligned_timeframes(tokens, timeframes_idx, alignments_idx)
        segments = self._get_segments(tokens, timeframes)
        # Creating the anontations for the top-level elements: a text document,
        # a time frame for the entire document, and the alignment between the
        # two, some specifics (text of the document, start and end of the frame)
        # will be filled in later
        new_document = new_view.new_textdocument(DocumentTypes.TextDocument, 'en', Identifiers.new("td"))
        new_timeframe = new_view.new_annotation(AnnotationTypes.TimeFrame, Identifiers.new("tf"))
        new_alignment = new_view.new_annotation(AnnotationTypes.Alignment, Identifiers.new("a"))
        # and this is where we start collecting those specifics
        text = []
        doc_start = sys.maxsize
        doc_end = -1
        for segment in segments:
            #print('=' * 80)
            aligned_segment = self._run_fastpunct_on_segment(segment)
            for aligned in aligned_segment:
                (i, word_in_aligned, word_out_aligned,
                 j, word_in, token, timeframe) = aligned
                if word_out_aligned is not None:
                    text.append(word_out_aligned)
                    doc_start = min(doc_start, timeframe.properties['start'])
                    doc_end = max(doc_end, timeframe.properties['end'])
                self._add_annotations(new_view, word_out_aligned, token, timeframe)
                continue
                timespan = "%s:%s" % (timeframe.properties['start'],
                                      timeframe.properties['end'])
                print("%2d  %-12s %-12s  %2d  %-12s %-12s %s"
                      % (i, word_in_aligned, word_out_aligned,
                         j, word_in, token.properties['word'], timespan))
        if doc_start == sys.maxsize:
            doc_start = 0
        if doc_end == -1:
            doc_end = 0
        text = ' '.join(text)
        new_document.text_value = text
        new_timeframe.add_property('start', doc_start)
        new_timeframe.add_property('end', doc_end)

    def _add_annotations(self, new_view, word_out_aligned, token, timeframe):
        # Creating a Span from the word and token, note that start and end are
        # copied, but will be later overridden to match with the offsets in the
        # text document
        new_span = new_view.new_annotation(AnnotationTypes.Span, Identifiers.new("s"))
        new_span.add_property('text', word_out_aligned)
        new_span.add_property('start', token.properties['start'])
        new_span.add_property('end', token.properties['end'])
        # Creating a new TimeFrame from the TimeFrame in the source view.
        new_frame = new_view.new_annotation(AnnotationTypes.TimeFrame, Identifiers.new("tf"))
        new_frame.add_property('start', timeframe.properties['start'])
        new_frame.add_property('end', timeframe.properties['end'])
        new_frame.add_property('frameType', timeframe.properties['frameType'])
        # Creating an Alignment, using the identifiers of the newly created span and frame.
        new_alignment = new_view.new_annotation(AnnotationTypes.Alignment, Identifiers.new("a"))
        new_alignment.add_property('source', new_frame.id)
        new_alignment.add_property('target', new_span.id)
        # TODO: need to add in the document property. But maybe this is already
        # dealt with in _new_view().

    def _get_annotations(self, view):
        """Get all tokens from the view as well as an index of the timeframes and the
        alignments. The tokens in the view are assumed to be in order."""
        tokens = []
        timeframes_idx = {}
        alignments_idx = {}
        token_attype_shortname = os.path.split(Uri.TOKEN)[1]
        timeframe_attype_shortname = AnnotationTypes.TimeFrame.shortname
        alignment_attype_shortname = AnnotationTypes.Alignment.shortname
        for annotation in view.annotations:
            if annotation.at_type.shortname == token_attype_shortname:
                tokens.append(annotation)
            elif annotation.at_type.shortname == timeframe_attype_shortname:
                timeframes_idx[annotation.id] = annotation
            elif annotation.at_type.shortname == alignment_attype_shortname:
                alignments_idx[annotation.properties['target']] = annotation
        return tokens, timeframes_idx, alignments_idx

    def _get_aligned_timeframes(self, tokens, timeframes_idx, alignments_idx):
        timeframes = []
        for token in tokens:
            alignment = alignments_idx[token.id]
            timeframe = timeframes_idx[alignment.properties['source']]
            #print(token.id, alignment.properties, timeframe.properties)
            timeframes.append(timeframe)
        return timeframes

    def _get_segments(self, tokens, timeframes):
        segments = []
        # the very first start is always considered to be after a pause
        previous_end = -MAX_PAUSE - 1
        # start with an empty sentence
        segment_tokens = []
        segment_timeframes = []
        for i in range(len(tokens)):
            token = tokens[i]
            timeframe = timeframes[i]
            start = timeframe.properties['start']
            end = timeframe.properties['end']
            length = end - start
            pause = start - previous_end
            if start - previous_end > MAX_PAUSE:
                if segment_tokens:
                    segments.append((segment_tokens, segment_timeframes))
                segment_tokens = []
                segment_timeframes = []
            else:
                segment_tokens.append(token)
                segment_timeframes.append(timeframe)
            previous_end = end
        if segment_tokens:
            segments.append((segment_tokens, segment_timeframes))
        return segments

    def _run_fastpunct_on_segment(self, segment):
        segment_tokens, segment_timeframes = segment
        words_in = [t.properties['word'] for t in segment_tokens]
        text_in = ' '.join(words_in)
        # TODO: remove "This happy"
        # TODO: add way to fix obvious garbage, maybe governed by an option, the
        # latter would check whether the two aligned words (before and after
        # fastpunct), consisting of letters only (no punctuation) are the same
        # (module capitals), if they are not, undo the fastpunct; this is to
        # deal with cases where we have PBS ==> BBC and tragedy ==> Tragicity,
        # maybe also fix children ==> Children even though no period was added
        # to the token before it (but this would screws us over on entities).
        text_out = "This happy " + FASTPUNCT.punct(text_in)
        words_out = text_out.split()
        words_in_aligned, words_out_aligned = align(words_in, words_out)
        # aligning words_in_aligned ==> words_in
        adjustment = 0
        aligned = []
        aligned_zipped = zip(words_in_aligned, words_out_aligned)
        for i, (word_in_aligned, word_out_aligned) in enumerate(aligned_zipped):
            if word_in_aligned is None:
                adjustment += 1
            # make sure j points to a legal index in the original data
            j = max(0, i - adjustment)
            j = min(j, len(segment_tokens) - 1)
            aligned.append((i, word_in_aligned, word_out_aligned,
                            j, words_in[j], segment_tokens[j], segment_timeframes[j]))
        return aligned

    def _print_alignment(self, words_in, words_out,
                         words_in_aligned, words_out_aligned):
        print('=' * 80)
        print("%d ==> %d" % (len(words_in), len(words_out)))
        for i, (w1, w2) in enumerate(zip(words_in_aligned, words_out_aligned)):
            print("%2d  %-12s %-12s"  % (i, w1, w2))


class Identifiers(object):

    """Utility class to generate annotation identifiers. You could, but don't have
    to, reset this each time you start a new view. This works only for new views
    since it does not check for identifiers of annotations already in the list
    of annotations."""

    identifiers = collections.defaultdict(int)

    @classmethod
    def new(cls, prefix):
        cls.identifiers[prefix] += 1
        return "%s%d" % (prefix, cls.identifiers[prefix])

    @classmethod
    def reset(cls):
        cls.identifiers = collections.defaultdict(int)


if __name__ == "__main__":

    app = App()
    service = Restifier(app)

    parser = argparse.ArgumentParser()
    parser.add_argument('--develop',  action='store_true')
    args = parser.parse_args()

    if args.develop:
        service.run()
    else:
        service.serve_production()
