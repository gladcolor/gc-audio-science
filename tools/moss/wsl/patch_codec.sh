#!/bin/bash
cd /root/gc/models/MOSS-TTS-Local-Transformer-v1.5
for f in processor_config.json config.json; do [ -f $f.orig ] || cp $f $f.orig; sed -i "s#\"OpenMOSS-Team/MOSS-Audio-Tokenizer-v2\"#\"/models/MOSS-Audio-Tokenizer-v2\"#" $f; done
grep -n audio_tokenizer_name_or_path processor_config.json config.json
/root/.local/bin/uv pip install --python /root/gc/venv/bin/python requests -q && echo requests-ok
