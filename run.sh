#!/bin/bash
# Nimbus Runner Script

export PYTHONPATH=.:./references/morg/python:./references/zahra/zahra-main
source venv/bin/activate
python -m nimbus.main
