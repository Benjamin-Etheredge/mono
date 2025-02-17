FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install -y \
        build-essential \
        curl \
        wget \
        sudo \
        software-properties-common\
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y python3.12 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker:latest /usr/local/bin/docker /usr/local/bin/docker

RUN mkdir -p /etc/docker \
    && echo '{\
    "debug": true,\
    "features": {\
        "containerd-snapshotter": true\
    }\
}' > /etc/docker/daemon.json

RUN useradd -m runner \
    && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/runner \
    && chmod 0440 /etc/sudoers.d/runner

RUN groupadd docker \
    && usermod -aG docker runner 
    # && systemctl enable docker.service \
    # && systemctl start docker.service

USER runner

WORKDIR /home/runner/

# Pants install in .local/bin
RUN mkdir -p /home/runner/_work/_temp \
    && mkdir -p /home/runner/.local/bin

ENV AGENT_TOOLSDIRECTORY=/home/runner/tools
ENV PATH=${AGENT_TOOLSDIRECTORY}:/home/runner/.local/bin:${PATH}
# Setup paths for github actions
