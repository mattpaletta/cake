FROM python:3.6 as base

FROM base as builder
COPY requirements.txt /requirements.txt
RUN pip3 install mypy -r /requirements.txt

COPY . /cake
RUN cd /cake && pip3 install . -v && mypy -m cake
WORKDIR /cake
ENTRYPOINT ["python3", "-m", "cake"]