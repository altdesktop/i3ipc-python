#!/usr/bin/env bash
set -e

make clean html
cd _build/html
python3 -m http.server -b 127.0.0.1
