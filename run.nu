#!/usr/bin/env nu
# Nimbus Runner Script (Nushell)

$env.PYTHONPATH = ".:./references/morg/python:./references/zahra/zahra-main"
./venv/bin/python -m nimbus.main
