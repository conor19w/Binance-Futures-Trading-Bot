# syntax=docker/dockerfile:1

FROM ubuntu:20.04
FROM python:3.9.0

WORKDIR /app

COPY . .

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "Live_Bot.py"]