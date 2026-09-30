$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install "pymupdf>=1.24" "pymupdf4llm>=0.0.17"
Write-Host "Installing MinerU with all core features. First parsing run may download model weights."
python -m pip install -U "mineru[all]"
python "$PSScriptRoot\doctor.py"
