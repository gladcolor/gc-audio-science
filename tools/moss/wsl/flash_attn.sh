#!/bin/bash
# Try to install FlashAttention 2 into the MOSS env from a prebuilt wheel only (no compiling).
export PATH=/root/.local/bin:$PATH
PY=/root/gc/venv/bin/python
$PY -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda)"
# flash-attn's setup downloads a matching prebuilt wheel from its GitHub releases when one exists; FLASH_ATTENTION_SKIP_CUDA_BUILD
# stops it from compiling when none exists.
FLASH_ATTENTION_SKIP_CUDA_BUILD=TRUE timeout 900 uv pip install --python $PY flash-attn --no-build-isolation 2>&1 | tail -5
$PY -c "import flash_attn, flash_attn_2_cuda; print('flash_attn', flash_attn.__version__, 'OK')" 2>&1 | tail -1
