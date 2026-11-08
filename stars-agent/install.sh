#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv && source .venv/bin/activate
pip install -q -r requirements.txt
echo "Lancez ensuite: python setup.py  (assistant de configuration)"
echo "Puis: python validate.py && python main.py"