FROM debian:jessie

EXPOSE 8000
WORKDIR /code

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential libxml2-dev libxslt1-dev libffi-dev python-dev \
    libmysqlclient-dev mysql-client python-pip node-less locales && \
    pip install --upgrade pip==8.0.3 && \
    rm -rf /var/lib/apt/lists/*
RUN dpkg-reconfigure locales && locale-gen C.UTF-8 && \
    /usr/sbin/update-locale LANG=C.UTF-8
RUN echo 'en_US.UTF-8 UTF-8' >> /etc/locale.gen && locale-gen
ENV LC_ALL C.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

COPY requirements /code/requirements/
RUN pip install --require-hashes --no-deps -r requirements/dev.txt
