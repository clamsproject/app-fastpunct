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
import argparse

from clams.app import ClamsApp
from clams.restify import Restifier
from clams.appmetadata import AppMetadata
from mmif.serialize import Mmif
from mmif.vocabulary import DocumentTypes, AnnotationTypes
from lapps.discriminators import Uri
from fastpunct import FastPunct

from align import align
from utils import Identifiers
import evaluation.examples

MMIF_VERSION = '0.4.0'
MMIF_PYTHON_VERSION = '0.4.5'
CLAMS_PYTHON_VERSION = '0.5.0'

APP_VERSION = '0.0.3'
APP_LICENSE = 'Apache 2.0'
ANALYZER_VERSION = '2.0.2'
ANALYZER_LICENSE = 'MIT License'


FASTPUNCT = FastPunct()


# Maximum pause between words allowed before we insert a segment boundary
MAX_PAUSE = 250

# Maximum size of a segment. The fastpunct module doesn't do well with sequences
# longer than 512. Since the sequence length seems to be longer than the number
# of tokens we play it conservatively here.
MAX_SEGMENT_SIZE = 256

# We hardwire the name of the Kaldi app so we can use it to find views created
# by Kaldi, this is not a very elegant way to do this
KALDI_APP = 'http://apps.clams.ai/aapb-pua-kaldi-wrapper'

# Some settings for verbose output when running from the command line, set these
# to True from the test.py script.
PRINT_PROGRESS = False
PRINT_ERROR_FIXES = False


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
        # We are copying the TimeFrame instances since having them included in
        # the view is a bit clearer. We don't really create tokens, but spans
        # over the text that are based on tokens, so instead of Uri.TOKEN we are
        # using AnnotationTypes.Span.
        metadata.add_output(DocumentTypes.TextDocument)
        metadata.add_output(AnnotationTypes.TimeFrame)
        metadata.add_output(AnnotationTypes.Alignment)
        metadata.add_output(AnnotationTypes.Span)
        return metadata

    def _annotate(self, mmif, **kwargs):
        Identifiers.reset()
        self.mmif = mmif if type(mmif) is Mmif else Mmif(mmif)
        for view in list(self.mmif.views):
            annotation_types = [t.shortname for t in view.metadata.contains]
            if view.metadata.app.startswith(KALDI_APP):
                # As currently set up we do not need the document as input to
                # fastpunct since we work from the tokens in the input view, but
                # we hand in the input view since we want to copy some metadata.
                new_view = self._new_view(view)
                run_fastpunct(view, new_view)
        return self.mmif

    def _new_view(self, input_view):
        # First get some goodies from the previous view, where the metadata for
        # the TimeFrame are of interest.
        document = None
        time_unit = None
        tf_contains = input_view.metadata.contains.get(AnnotationTypes.TimeFrame)
        if 'document' in tf_contains:
            document = tf_contains['document']
        if 'timeUnit' in tf_contains:
            time_unit = tf_contains['timeUnit']
        # Build the new view.
        view = self.mmif.new_view()
        view.metadata.app = self.metadata.identifier
        self.sign_view(view)
        # We know that we create one text document which is the document source
        # for all Span annotations, and the identifier for that single document
        # is going to be td1 because of how the Identifiers class works.
        docid = view.id + ':td1'
        view.new_contain(DocumentTypes.TextDocument)
        view.new_contain(AnnotationTypes.Span, document=docid)
        view.new_contain(AnnotationTypes.TimeFrame, document=document, timeUnit=time_unit)
        view.new_contain(AnnotationTypes.Alignment)
        return view


def run_fastpunct(view, new_view):
    """Run the fastpunct module over the text in the view and add annotations to
    the new view, including a TextDocument and the individual token-like spans as
    well as all time frames that the spans are aligned to."""
    segments = get_segments(view)
    #print_segments(segments)
    new_document, new_timeframe = add_toplevel_annotations(new_view)
    # Loop through the segments and add spans, frames and alignments, this is
    # also where we collect the specifics for the top level document and frame.
    text = []
    doc_start = sys.maxsize
    doc_end = -1
    doc_offset = 0
    for segment in segments:
        if PRINT_PROGRESS:
            print('SEGMENT:', segment)
        aligned_segment = segment.run_fastpunct()
        #print_alignments(aligned_segment)
        for aligned in aligned_segment:
            (i, word_in_aligned, word_out_aligned,
             j, word_in, token, timeframe) = aligned
            if word_out_aligned is None:
                continue
            text.append(word_out_aligned)
            doc_start = min(doc_start, timeframe.properties['start'])
            doc_end = max(doc_end, timeframe.properties['end'])
            p1 = doc_offset
            p2 = doc_offset + len(word_out_aligned)
            add_annotations(new_view, word_out_aligned, timeframe, p1, p2)
            doc_offset += len(word_out_aligned) + 1
    update_toplevel_annotations(new_document, new_timeframe,
                                text, doc_start, doc_end)


def get_segments(view):
    """Return a list of Segments from the view. Segments are slices of the text
    that are separated by a pause (where MAX_PAUSE determines the maximum pause
    between words in the same segment). Each segment has a token and its aligned
    timeframe."""
    tokens, timeframes = get_annotations(view)
    segments = []
    segment = Segment()
    # the very first start is always considered to be after a pause
    previous_end = -MAX_PAUSE - 1
    for token, timeframe in zip(tokens, timeframes):
        t_props = token.properties
        tf_props = timeframe.properties
        start = timeframe.properties['start']
        end = timeframe.properties['end']
        length = end - start
        pause = start - previous_end
        #print_token_and_timeframe(token, timeframe, pause)
        if start - previous_end > MAX_PAUSE or len(segment) >= MAX_SEGMENT_SIZE:
            if segment:
                segments.append(segment)
            segment = Segment()
        segment.append_token_and_timeframe(token, timeframe)
        previous_end = end
    if segment:
        segments.append(segment)
    return segments


def get_annotations(view):
    """Get all tokens and corresponding time frames from the view. The tokens in the
    view are assumed to be in order and the timeframes line up with the tokens."""
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
    timeframes = []
    for token in tokens:
        alignment = alignments_idx[token.id]
        timeframe = timeframes_idx[alignment.properties['source']]
        #print(token.id, alignment.properties, timeframe.properties)
        timeframes.append(timeframe)
    return tokens, timeframes


def add_toplevel_annotations(new_view):
    """Create the annotations for the top-level elements: a text document and a
    time frame for the entire document, some specifics (text of the document,
    start and end of the frame) will be filled in later and therefore this
    function returns the new document and time frame."""
    new_document = new_view.new_textdocument(DocumentTypes.TextDocument, 'en', Identifiers.new("td"))
    new_timeframe = new_view.new_annotation(AnnotationTypes.TimeFrame, Identifiers.new("tf"))
    # Also add the alignment between the document and timeframe
    new_view.new_annotation(AnnotationTypes.Alignment,
                            Identifiers.new("a"),
                            source=new_timeframe.id,
                            target=new_document.id)
    return new_document, new_timeframe


def fix_errors(aligned_zipped):
    """Fix some common errors in the output of fastpunct."""
    fix_local_alignment_errors(aligned_zipped)
    fix_none_sequences(aligned_zipped)


def fix_local_alignment_errors(aligned_zipped):
    """Fix local transformations like 'tragic ==> Tragicity'. Also tentatively
    copies input word to the output if there is nothing aligned."""
    for i, (word_in, word_out) in enumerate(aligned_zipped):
        # If word_in does not align with anything then copy it to word_out.
        # TODO: this may need a context check.
        fixed_word_out = None
        if word_out is None:
            fixed_word_out = word_in
        # Tries to replace things like 'gbh ==> BBC' with 'gbh ==> GBH'.
        # TODO: this needs work
        elif word_in is not None and word_out is not None and \
             word_out.isupper() and len(word_in) == len(word_out) \
             and word_in != word_out.lower():
            fixed_word_out = word_in.upper()
        # If a token that is just letters is changed then revert to the
        # original. This will turn the alignment (robert, Laurent) back to
        # (robert, robert). May want to keep capitalization though.
        elif word_in is not None and word_out is not None \
             and word_in.lower() != word_out.lower() and word_out.isalpha():
            fixed_word_out = word_in
        if fixed_word_out is not None:
            if PRINT_ERROR_FIXES:
                print("ERROR_FIX: [%s] ==> [%s]" % (word_out, word_in))
            aligned_zipped[i] = (word_in, fixed_word_out)


def fix_none_sequences(aligned_zipped):
    """Sometimes there are long sequences of None on the input side mapped to
    words on the output side. Typically these sequences repeat text from the
    input and they can be cut out."""
    none_sequences = []
    none_sequence = []
    for i, (word_in, word_out) in enumerate(aligned_zipped):
        if word_in is None and word_out is not None:
            none_sequence.append(i)
        elif word_in is not None and none_sequence:
            none_sequences.append(none_sequence)
            none_sequence = []
    if none_sequence:
        none_sequences.append(none_sequence)
    # Cut out all none sequences as long as they are longer than 1
    for seq in reversed(none_sequences):
        if PRINT_ERROR_FIXES:
            print("ERROR_FIX: deleting tokens %s through %s" % (seq[0], seq[-1]))
        if len(seq) > 1:
            aligned_zipped[seq[0]:seq[-1]+1] = []


def add_annotations(view, word, timeframe, p1, p2):
    """Add Span, TimeFrame and Alignment annotations to the view. We do not need to
    add document properties to the Span and TimeFrame because this was done by the
    metadata."""
    # Creating a Span for the new potentially punctuated word
    new_span = view.new_annotation(AnnotationTypes.Span, Identifiers.new("s"))
    new_span.add_property('text', word)
    new_span.add_property('start', p1)
    new_span.add_property('end', p2)
    # Creating a new TimeFrame from the TimeFrame in the source view.
    new_frame = view.new_annotation(AnnotationTypes.TimeFrame, Identifiers.new("tf"))
    new_frame.add_property('start', timeframe.properties['start'])
    new_frame.add_property('end', timeframe.properties['end'])
    new_frame.add_property('frameType', timeframe.properties['frameType'])
    # Creating an Alignment, using the identifiers of the newly created span and frame.
    new_alignment = view.new_annotation(AnnotationTypes.Alignment, Identifiers.new("a"))
    new_alignment.add_property('source', new_frame.id)
    new_alignment.add_property('target', new_span.id)


def update_toplevel_annotations(
        new_document, new_timeframe, text, doc_start, doc_end):
    """Update the TextDocument and TimeFrame with information collected while
    looping through all segments."""
    new_document.text_value = ' '.join(text)
    # We have determined the start and end of the timeframe, but we update to
    # reasonable values if there were no tokens. In that case we might be better
    # off not adding anything though.
    if doc_start == sys.maxsize:
        doc_start = 0
    if doc_end == -1:
        doc_end = 0
    new_timeframe.add_property('start', doc_start)
    new_timeframe.add_property('end', doc_end)


def print_segments(segments):
    for segment in segments:
        print(segment)


def print_alignments(alignments, start=None, end=None):
    """Debugging method to print a list of alignments."""
    if start is None and end is None:
        start = 0
        end = len(alignments)
        for i in range(start, end):
            print_alignment(alignments[i])


def print_alignment(aligned):
    """Debugging method to print an alignment."""
    (i, word_in_aligned, word_out_aligned, j, word_in, token, timeframe) = aligned
    timespan = "%s:%s" % (timeframe.properties['start'], timeframe.properties['end'])
    charspan = "%s:%s" % (token.properties['start'], token.properties['end'])
    print("%2d  %-12s %-12s %-15s  %2d  %-12s %-12s"
          % (j, word_in, charspan, timespan,
             i, word_in_aligned, word_out_aligned))


def print_token_and_timeframe(token, timeframe, pause):
    t_props = token.properties
    tf_props = timeframe.properties
    print("%4d %4d  %6d %6d %4d %s"
          % (t_props['start'], t_props['end'],
             tf_props['start'], tf_props['end'], pause, t_props['word']))


class Segment(object):

    def __init__(self):
        self.tokens = []
        self.timeframes = []

    def __str__(self):
        return "<Segment tokens=%d timeframes=%d '%s:%s --> %s:%s'>" \
            % (len(self.tokens), len(self.timeframes),
               self.tokens[0].properties['word'],
               self.timeframes[0].properties['start'],
               self.tokens[-1].properties['word'],
               self.timeframes[-1].properties['end'])

    def __len__(self):
        return len(self.tokens)

    def append_token_and_timeframe(self, token, timeframe):
        self.tokens.append(token)
        self.timeframes.append(timeframe)

    def words(self):
        return [t.properties['word'] for t in self.tokens]

    def text(self):
        return ' '.join(self.words())

    def run_fastpunct(self):
        text_in = self.text()
        text_out = FASTPUNCT.punct(text_in)
        #text_out = evaluation.examples.cached_results.get(text_in, '')
        words_in = self.words()
        words_out = text_out.split()
        words_in_aligned, words_out_aligned = align(words_in, words_out)
        # TODO: maybe the following needs to be moved elsewhere
        # TODO: conceptually that aligned list is somewhat unintuitive
        aligned_zipped = list(zip(words_in_aligned, words_out_aligned))
        fix_errors(aligned_zipped)
        aligned = []
        adjustment = 0
        for i, (word_in_aligned, word_out_aligned) in enumerate(aligned_zipped):
            if word_in_aligned is None:
                adjustment += 1
            # make sure j points to a legal index in the original data
            j = max(0, i - adjustment)
            j = min(j, len(self.tokens) - 1)
            aligned.append((i, word_in_aligned, word_out_aligned,
                            j, words_in[j], self.tokens[j], self.timeframes[j]))
        return aligned


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
