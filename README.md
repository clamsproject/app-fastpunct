# fastPunct

Application using the Python fastpunct module to restore punctuation and capitalization.

URLs:

- https://github.com/notAI-tech/fastpunct
- https://pypi.org/project/fastpunct/

The Python module is released under the MIT License.

**Requirements**

```
$ pip install clams-python==0.5.0
$ pip install fastpunct==2.0.2
```

This also instals Torch.

**Command line use:**

```python
>>> from fastpunct import FastPunct
>>> fastpunct = FastPunct()
>>> text = "hello this is jim lehrer with the newshour on pbs we have news about the tomato it has been observed recently that they dont taste good anymore"
>>> fastpunct.punct(text)
```

```
Hello, this is Jim Lehrer, with the newshour on BBC: "We have news about the tomato it has been observed recently that they don\'t taste good anymore.
```

**Testing the application without a server**

```
$ python test.py example-kaldi-output.mmif out.mmif
<View id=v_0 annotations=563 app=http://apps.clams.ai/aapb-pua-kaldi-wrapper/0.2.2>
<View id=v_1 annotations=573 app=https://apps.clams.ai/fastpunct>
```

**Running a server**

The following starts a Flask development server, without the option the application will run in a Gunicorn server.

```
$ python app.py --develop
```

To get the metadata or process a MMIF file:

```
$ curl http://0.0.0.0:5000/
$ curl -H "Accept: application/json" -X POST -d@example-input.json http://0.0.0.0:5000/
```

The second command will take a couple of seconds.