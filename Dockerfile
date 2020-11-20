FROM python:3.7
ENV PYTHONBUFFERED 1
RUN mkdir /code
COPY . /code/

WORKDIR /code

RUN pip install -r requirements.txt

