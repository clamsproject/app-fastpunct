"""test.py

Several tests and experiments for this application.

$ python test.py example-mmif.json out.json
Run fastpunct on an input MMIF file. This bypasses the server and just pings the
annotate() method on the App class. Output is written to out.json.

$ python test.py --duplicates
Run the code that finds duplicates on an example.

$ python test.py --metadata
Prints the metadata.

"""

import sys
import json
import mmif
import app
import evaluation.examples
from align import align

app.PRINT_PROGRESS = True
app.PRINT_ERROR_FIXES = True

application = app.App()


def test_fixing_duplication_errors():
    print('>>> testing duplication error fix')
    segment_in = evaluation.examples.segment_with_duplicates_in
    segment_out = evaluation.examples.segment_with_duplicates_out
    words_in_aligned, words_out_aligned = align(segment_in.split(), segment_out.split())
    app.fix_errors(list(zip(words_in_aligned, words_out_aligned)))

def print_metadata():
    meta = application.appmetadata()
    print(json.dumps(json.loads(meta), indent=4))

def run_tool(in_file, out_file):
    with open(in_file) as fh_in, open(out_file, 'w') as fh_out:
        mmif_out_as_string = application.annotate(fh_in.read(), pretty=True)
        mmif_out = mmif.Mmif(mmif_out_as_string)
        fh_out.write(mmif_out_as_string)
        for view in mmif_out.views:
            print("VIEW: <View id=%s annotations=%s app=%s>"
                  % (view.id, len(view.annotations), view.metadata['app']))


if __name__ == '__main__':

    if sys.argv[1] == '--duplicates':
        test_fixing_duplication_errors()
    elif sys.argv[1] == '--metadata':
        print_metadata()
    else:
        run_tool(sys.argv[1], sys.argv[2])
