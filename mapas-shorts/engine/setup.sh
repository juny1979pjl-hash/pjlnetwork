#!/usr/bin/env bash
# Prepara un directorio de trabajo para un short nuevo.
# Uso: bash mapas-shorts/engine/setup.sh <directorio_trabajo>
set -euo pipefail
ENG="$(cd "$(dirname "$0")" && pwd)"
W="${1:?directorio de trabajo}"
mkdir -p "$W"
cp "$ENG/package.json" "$ENG/render.js" "$ENG/tts.py" "$W/"
cd "$W"
npm install --silent --no-audit --no-fund >/dev/null
pip install -q kokoro-onnx soundfile 2>/dev/null
[ -f kokoro-v1.0.int8.onnx ] || curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx
[ -f voices-v1.0.bin ] || curl -sSLO https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
echo "listo: $W"
