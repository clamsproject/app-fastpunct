# fastPunct

Application using the Python fastpunct module to restore punctuation and capitalization.

- https://github.com/notAI-tech/fastpunct
- https://pypi.org/project/fastpunct/

The fastpunct module is released under the MIT License.

**Requirements**

```
$ pip install clams-python==0.5.0
$ pip install fastpunct==2.0.2
```

This also installs Torch.

### Usage

Basic use:

```python
>>> from fastpunct import FastPunct
>>> fastpunct = FastPunct()
>>> fastpunct.punct("hello this is jim lehrer with the newshour on pbs we have news about the tomato it has been observed recently that they dont taste good anymore")
```

Result:

```
Hello, this is Jim Lehrer, with the newshour on BBC: "We have news about the tomato it has been observed recently that they don\'t taste good anymore.
```

To test the application without a server:

```
$ python test.py data/example-input.json out.json
<View id=v_0 annotations=563 app=http://apps.clams.ai/aapb-pua-kaldi-wrapper/0.2.2>
<View id=v_1 annotations=573 app=https://apps.clams.ai/fastpunct>
```

The output should like `data/example-output`.

#### Running a server

The following starts a Flask development server, without the --develop option the application will run in a Gunicorn server.

```
$ python app.py --develop
```

To get the metadata or process a MMIF file:

```
$ curl http://0.0.0.0:5000/
$ curl -H "Accept: application/json" -X POST -d@data/example-input.json http://0.0.0.0:5000/
```

The second command will take a couple of seconds.

### Docker

Building the image and starting the container:

```
$ docker build -t clams-fastpunct:2.0.2 .
$ docker run --name clams-fastpunct --rm -d -p 5000:5000 clams-fastpunct:2.0.2
```

Pinging the server:

```
$ curl http://127.0.0.1:5000/
$ curl -H "Accept: application/json" -X POST -d@example-input.json http://127.0.0.1:5000/
```

### Evaluation

There are two informal evaluations. The first allows you to eyeball the results of two pipelines:

- Kaldi ⟹ spaCy NER
- Kaldi ⟹ fastpunct ⟹ spaCy NER

Both pipelines were run on a small audio document and the results were saved in `data\kaldi-spacy.json` and `data\kaldi-fastpunct-spacy.json`.

The following commands create HTML files that contain a spaCy visualization:

```
$ cd evaluation
$ python3 visualize.py kaldi-spacy.json kaldi-spacy.html
$ python3 visualize.py kaldi-fastpunct-spacy.json kaldi-fastpunct-spacy.html
```

Note that this code requires spaCy to be installed and that the code in this repository generally does not have that requirement.

The other evaluation is to compare the gold standard transcript in `transcript-fragment.txt` to two files resulting from the following processing sequence:

- transcript_doc  ⟹ [stripper] ⟹ stripped_doc ⟹ [fastpunct] ⟹ fastpunct_doc

The stripper removes punctuation and makes all letters lower case and fastpunct tries to restore the original. The idea is to calculate the edit distance between transcript_doc and stripped_doc as well as between transcript_doc and fastpunct_doc. If fastpunct is succesful the edit distance should go down significantly.

```
$ python3 evaluate.py transcript-fragment.txt
```

Results are shown in `evaluate.txt`.

