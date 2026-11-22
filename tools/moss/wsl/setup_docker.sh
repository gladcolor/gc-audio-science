#!/bin/bash
# Docker engine + NVIDIA Container Toolkit in WSL (Ubuntu 24.04, root). Packages from Ubuntu's and NVIDIA's apt repos.
set -e
export DEBIAN_FRONTEND=noninteractive
echo "init: $(ps -p 1 -o comm=)"
apt-get update -qq
apt-get install -y -qq docker.io curl gnupg ca-certificates > /dev/null
# NVIDIA Container Toolkit (official repo)
if [ ! -f /etc/apt/sources.list.d/nvidia-container-toolkit.list ]; then
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
  curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
    | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
    > /etc/apt/sources.list.d/nvidia-container-toolkit.list
  apt-get update -qq
fi
apt-get install -y -qq nvidia-container-toolkit > /dev/null
nvidia-ctk runtime configure --runtime=docker > /dev/null
if [ "$(ps -p 1 -o comm=)" = "systemd" ]; then
  systemctl enable --now docker > /dev/null 2>&1 || true
  systemctl restart docker
else
  (dockerd > /var/log/dockerd.log 2>&1 &) ; sleep 5
fi
docker --version
docker info 2>/dev/null | grep -i -E "runtimes|default runtime" || true
echo DOCKER-READY
