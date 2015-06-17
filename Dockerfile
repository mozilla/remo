FROM debian:jessie

EXPOSE 8000
WORKDIR /code

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential libxml2-dev libxslt1-dev python-dev \
    libmysqlclient-dev python-pip node-less && \
    pip install --upgrade pip==7.0.3 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements /code/requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt
