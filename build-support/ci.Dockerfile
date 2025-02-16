FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        curl \
        wget \
        sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m runner \
    && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/runner \
    && chmod 0440 /etc/sudoers.d/runner

USER runner
WORKDIR /home/runner/workspaces/ci-build
