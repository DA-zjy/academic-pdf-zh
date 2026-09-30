#!/usr/bin/env bash
set -euo pipefail
python -m pip install --upgrade pip
python -m pip install "pymupdf>=1.24" "pymupdf4llm>=0.0.17"
python -m pip install -U "mineru[all]"
python "$(dirname "$0")/doctor.py"
