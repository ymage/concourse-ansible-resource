# Pull base image
FROM alpine:3.8
LABEL maintainer="Ymage"

# Base packages
# Build dependencies
RUN ln -s /lib /lib64 \
    && \
        apk --upgrade add --no-cache \
            bash \
            sudo \
            curl \
            zip \
            jq \
            xmlsec \
            yaml \
            libc6-compat \
            libxml2 \
            python \
            py-lxml \
            py-pip \
            openssl \
            ca-certificates \
            openssh-client \
            rsync \
    && \
        apk --upgrade add --no-cache --virtual \
            build-dependencies \
            build-base \
            libffi-dev \
            openssl-dev \
            python-dev \
            linux-headers \
            libxml2-dev

# Ansible installation
ADD requirements.txt /opt/
RUN pip install --upgrade --no-cache-dir -r /opt/requirements.txt

RUN apk del \
        build-dependencies \
        build-base \
        libffi-dev \
        openssl-dev \
        python-dev \
        linux-headers \
        libxml2-dev \
    && \
        rm -rf /var/cache/apk/*

# Default config
COPY ansible/ /etc/ansible/

# Install tests
COPY tests/ /opt/resource/tests/

# install resource assets
COPY assets/ /opt/resource/

# default command: display local setup
CMD ["ansible", "-c", "local", "-m", "setup", "all"]
# CMD [ "ansible-playbook", "--version" ]
