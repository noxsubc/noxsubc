#!/usr/bin/env bash
apt-get update && \
apt-get install -y ffmpeg libsm6 libxext6 libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev
pip install -r requirements.txt
