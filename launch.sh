#!/bin/bash
python3 login.py
if [ "$?" == "200" ]; then
    echo "start chatgpt server"
    cd "$(dirname "$0")"
    xvfb-run pipenv run proxy
else
    echo "login failure"
fi
