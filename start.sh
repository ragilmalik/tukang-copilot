#!/usr/bin/env bash
# One-click start for Mac/Linux. First run installs everything into .venv
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q -r requirements.txt
[ -f .env ] || cp .env.example .env
python app.py
