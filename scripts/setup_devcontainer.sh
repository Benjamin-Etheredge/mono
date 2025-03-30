#!/bin/bash
set -e

# Setup docker for containerd snapshots

echo "Setting up Docker for containerd snapshots..."
echo '
{
  "features": {
    "containerd-snapshotter": true
  }
}
' | sudo tee /etc/docker/daemon.json

# Install NVIDIA Container Toolkit
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg &&
	curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |
	sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |
		sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker

# This is a special way to restart dind with devcontainers
sudo pkill dockerd || true
sudo pkill containerd || true
bash /usr/local/share/docker-init.sh

sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0 libsm6 libxrender1 libxext6

# pants venv
uv pip install --system -r 3rdparty/python/requirements.txt
