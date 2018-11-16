# Pull base image
FROM alpine:3.8 as base
LABEL maintainer="Ymage"

FROM base as builder

# Base packages
# Build dependencies
RUN ln -s /lib /lib64 && \
    apk add --upgrade --no-cache \
        curl \
        ca-certificates \
        zip \
        xmlsec \
        libc6-compat \
        libxml2 \
        python3 \
        py3-lxml \
        py3-pip \
        openssl && \
    apk add --upgrade --no-cache --virtual build-dependencies \
        build-base \
        libffi-dev \
        openssl-dev \
        python3-dev \
        linux-headers \
        libxml2-dev

# Ansible installation
ADD requirements.txt /opt/
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir --install-option="--prefix=/install" -r /opt/requirements.txt

FROM base
COPY --from=builder /install /usr/local
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
        python3 \
        py3-lxml \
        openssl

ENV PYTHONPATH=/usr/local/lib/python3.6/site-packages:$PYTHONPATH

# Default config
COPY ansible/ /etc/ansible/

# Install tests
COPY tests/ /opt/resource/tests/

# install resource assets
COPY assets/ /opt/resource/

# default command: display local setup
CMD [ "ansible-playbook", "--version" ]
