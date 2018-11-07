FROM python:3.6 as base

FROM base as builder
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

COPY cake /cake
WORKDIR /
ENTRYPOINT ["python3", "-m", "cake"]