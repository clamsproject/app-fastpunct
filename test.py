"""test.py

Run a simple tokenizery on an input MMIF file. This bypasses the server and just
pings the annotate() method on the SpacyApp class. Prints a summary of the views
in the end result.

Usage:

$ python test.py example-mmif.json out.json

"""

import sys
import json
import mmif
import app

app.PRINT_PROGRESS = True
app.PRINT_ERROR_FIXES = True

application = app.App()

meta = application.appmetadata()
#print(json.dumps(json.loads(meta), indent=4))

with open(sys.argv[1]) as fh_in, open(sys.argv[2], 'w') as fh_out:
    mmif_out_as_string = application.annotate(fh_in.read(), pretty=True)
    mmif_out = mmif.Mmif(mmif_out_as_string)
    fh_out.write(mmif_out_as_string)
    for view in mmif_out.views:
        print("VIEW: <View id=%s annotations=%s app=%s>"
              % (view.id, len(view.annotations), view.metadata['app']))
