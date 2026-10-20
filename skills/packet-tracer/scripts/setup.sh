#!/bin/bash
# One-time setup: venv with the `twofish` package (needed by ptcrypto.py) + python-xlib (GUI automation).
set -e
cd "$(dirname "$0")"
[ -d venv ] || python3 -m venv venv
./venv/bin/pip install -q twofish python-xlib
# twofish 0.3.0 still uses the removed `imp` module on Python >= 3.12
T=$(./venv/bin/python -c "import sysconfig;print(sysconfig.get_paths()['purelib'])")/twofish.py
sed -i "s/^import imp$/import importlib.util/; s/imp.find_module('_twofish')\[1\]/importlib.util.find_spec('_twofish').origin/" "$T"
./venv/bin/python -c "import twofish; print('twofish ok')"
