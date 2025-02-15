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
sudo pkill dockerd || true
sudo pkill containerd || true
bash /usr/local/share/docker-init.sh

sudo apt-get update
sudo apt-get install -y libgl1 libglib2.0-0 libsm6 libxrender1 libxext6
pants venv
