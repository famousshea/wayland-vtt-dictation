#!/bin/bash
cd /home/sheamus/Repositories/wayland-vtt-dictation
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install vosk sounddevice numpy faster-whisper
echo "Python environment setup complete."
