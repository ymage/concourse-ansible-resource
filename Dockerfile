# Pull base image
FROM python:3.7.2-alpine3.9 as base
ARG VERSION
LABEL maintainer="Ymage"
LABEL version="$VERSION"

# Base packages
# Build dependencies
RUN ln -s /lib /lib64 && \
    apk add --upgrade --no-cache \
        curl \
        ca-certificates \
        zip \
        jq \
        xmlsec \
        yaml \
        libc6-compat \
        libxml2 \
        libxslt \
        py3-lxml \
        openssh \
        openssl \
        rsync && \
    apk add --upgrade --no-cache --virtual build-dependencies \
        build-base \
        libffi-dev \
        openssl-dev \
        python3-dev \
        linux-headers \
        libxml2-dev \
        libxslt-dev

# Ansible installation
ADD requirements.txt /opt/
RUN pip3 install --no-cache-dir --upgrade pip setuptools && \
    pip3 install --no-cache-dir --upgrade -r /opt/requirements.txt && \
    apk del build-dependencies && \
    rm -rf /var/cache/apk/*

ENV PYTHONPATH=/usr/local/lib/python3.7/site-packages:$PYTHONPATH

# Default config
COPY ansible/ /etc/ansible/

# Install tests
COPY tests/ /opt/resource/tests/

# install resource assets
COPY assets/ /opt/resource/

# default command: display local setup
CMD [ "ansible-playbook", "--version" ]
