FROM ubuntu:14.04

# Update
RUN apt-get update \
# Install pip
    && apt-get install -y \
        python-dev python-pip \
        libffi-dev libssl-dev xmlsec1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install -r requirements.txt

ADD *.py /server/

EXPOSE 5000

WORKDIR /server

CMD ["./start.py", "--bind_host=0.0.0.0"]

