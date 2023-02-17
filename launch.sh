#!/bin/bash
python3 login.py
if [ "$?" == "200" ]; then
    echo "start chatgpt server"
    python3 proxy.py
else
    echo "login failure"
fi
