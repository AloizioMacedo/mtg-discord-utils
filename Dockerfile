FROM python:3.9-alpine

WORKDIR /

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /magic_utils

CMD python main.py
