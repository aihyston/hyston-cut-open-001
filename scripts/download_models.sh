#!/usr/bin/env bash
# Downloads the Chinese Paraformer ASR model used for lyric timing (~230 MB).
# Model is NOT redistributed in this repo; see its own license in the extracted README.
set -euo pipefail
mkdir -p models && cd models
URL=https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-paraformer-zh-2023-09-14.tar.bz2
[ -d sherpa-onnx-paraformer-zh-2023-09-14 ] || { curl -L -o pz.tar.bz2 "$URL" && tar xjf pz.tar.bz2 && rm pz.tar.bz2; }
echo "Model ready: models/sherpa-onnx-paraformer-zh-2023-09-14"
