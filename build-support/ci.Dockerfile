FROM ubuntu:24.04

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        build-essential \
        curl \
        wget \
        sudo \
        software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
        python3.12 \
        python3.12-dev \
        python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

# Setup docker stuff
COPY --from=docker:latest /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker:latest /usr/local/libexec/docker/cli-plugins/docker-buildx /usr/local/libexec/docker/cli-plugins/docker-buildx
COPY --from=docker:latest /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose

# hadolint ignore=DL4006
RUN curl --proto '=https' --tlsv1.2 -fsSL https://static.pantsbuild.org/setup/get-pants.sh  | bash -s -- -d /usr/local/bin

# RUN mkdir -p /etc/docker \
#     && echo '{\
#     "debug": true,\
#     "features": {\
#         "containerd-snapshotter": true\
#     }\
# }' > /etc/docker/daemon.json

# RUN useradd -m runner \
#     && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/runner \
#     && chmod 0440 /etc/sudoers.d/runner

# RUN groupadd docker \
#     && usermod -aG docker runner \
#     && newgrp docker
# #     # && systemctl enable docker.service \
# #     # && systemctl start docker.service

# USER runner

# WORKDIR /home/runner/

# # Pants install in .local/bin
# RUN mkdir -p /home/runner/_work/_temp \
#     && mkdir -p /home/runner/.local/bin

# ENV AGENT_TOOLSDIRECTORY=/home/runner/tools
# ENV PATH=${AGENT_TOOLSDIRECTORY}:/home/runner/.local/bin:${PATH}
# Setup paths for github actions

