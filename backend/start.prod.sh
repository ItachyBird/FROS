#! /bin/bash

docker build -t flight-route-optimizer .

docker run -p 8000:8000 flight-route-optimizer