# Pull base image
FROM python:3.7.3-alpine3.9
ARG VERSION
LABEL maintainer="Ymage"
LABEL version="${VERSION}"

# Base packages

RUN ln -s /lib /lib64 && \
    apk add --upgrade --no-cache \
      ca-certificates \
      curl \
      git \
      openssh-client \
      openssl \
      rsync \
      zip && \
    apk add --upgrade --no-cache --virtual build-dependencies \
      build-base \
      libffi-dev \
      openssl-dev \
      python3-dev

# Ansible installation
ADD requirements.txt /opt/
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools && \
    python3 -m pip install --no-cache-dir --upgrade --requirement /opt/requirements.txt && \
    apk del build-dependencies && \
    rm -rf /var/cache/apk/* && \
    mkdir -p ~/.ssh && \
    echo $'Host *\nStrictHostKeyChecking no' > ~/.ssh/config && \
    chmod 400 ~/.ssh/config

ENV PYTHONPATH=/usr/local/lib/python3.7/site-packages:$PYTHONPATH

# Default config
COPY ansible/ /etc/ansible/

# Install tests
COPY tests/ /opt/resource/tests/

# install resource assets
COPY assets/ /opt/resource/

# default command: display local setup
CMD [ "ansible-playbook", "--version" ]
