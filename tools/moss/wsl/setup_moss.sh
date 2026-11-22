#!/bin/bash
# Set up MOSS-TTS in WSL (Ubuntu 24.04, root): uv, the MOSS code, a Python env, and copies of the models.
set -e
mkdir -p /root/gc /root/gc/models
cd /root/gc
if ! command -v uv >/dev/null 2>&1 && [ ! -x /root/.local/bin/uv ]; then
  curl -LsSf https://astral.sh/uv/install.sh | sh > /root/gc/uv_install.log 2>&1
fi
export PATH=/root/.local/bin:$PATH
echo "uv: $(uv --version)"
if [ ! -d MOSS-TTS ]; then
  git clone -q --depth 1 https://github.com/OpenMOSS/MOSS-TTS.git
fi
if [ ! -x /root/gc/venv/bin/python ]; then
  uv venv /root/gc/venv --python 3.12 -q
fi
cd /root/gc/MOSS-TTS
uv pip install --python /root/gc/venv/bin/python -e ".[torch-runtime]" soundfile numpy librosa --torch-backend cu128 -q
/root/gc/venv/bin/python -c "import torch, transformers; print('torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'transformers', transformers.__version__)"
for m in MOSS-TTS-Local-Transformer-v1.5 MOSS-Audio-Tokenizer-v2; do
  if [ ! -d "/root/gc/models/$m" ]; then
    cp -r "/mnt/e/gc-audio/models/$m" /root/gc/models/
  fi
done
du -sh /root/gc/models/*
echo SETUP-DONE
