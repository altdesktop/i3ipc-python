FROM ubuntu:19.04

WORKDIR /app

RUN apt-get update && apt-get install -y python-pip python3-pip i3 xvfb

COPY requirements.txt .
RUN pip3 install -r requirements.txt && pip2 install -r requirements.txt

ADD . /app

CMD ["./run-tests.py"]
