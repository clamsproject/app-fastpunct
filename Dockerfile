FROM clamsproject/clams-python:0.5.0

RUN pip install fastpunct==2.0.2

WORKDIR ./app
COPY ./ ./

CMD ["python", "app.py"]
