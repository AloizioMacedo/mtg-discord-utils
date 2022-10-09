FROM python:3.9-alpine

RUN apk add build-base

WORKDIR /

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /magic_utils

RUN rm -rf utils

CMD python main.py
