#!/bin/bash
python3 login.py
if [ "$?" == "200" ]; then
    cd "$(dirname "$0")"
    xvfb-run pipenv run proxy
fi
