#! /bin/bash

docker build -t flight-route-optimizer .

docker run --rm -it -v "$PWD":/app -p 8000:8000 flight-route-optimizer bash -c "pip install -q watchfiles && uvicorn app:app --host 0.0.0.0 --port 8000 --reload"
