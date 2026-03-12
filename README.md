# Wayland VTT Dictation Tool

A lightweight, local voice-to-text dictation tool for Wayland (Ubuntu 25.10).

## Features
- **Headless & Fast:** No windows, just system notifications and audible cues.
- **Wayland Compatible:** Uses `ydotool` for virtual keyboard input and `wl-copy` for clipboard.
- **Privacy First:** 100% local transcription using Vosk/Faster-Whisper.
- **AI-Ready:** Prefixes all transcribed text with `(voice to text input) `.

## Prerequisites
- `ydotool`: For virtual keyboard events in Wayland.
- `wl-clipboard`: For clipboard integration.
- `libnotify-bin`: For desktop notifications (`notify-send`).
- `ffmpeg`: For audio recording.
- Python 3.10+

## Quick Setup
1. Clone the repository:
   ```bash
   cd ~/Repositories/wayland-vtt-dictation
   ```
2. Install system dependencies:
   ```bash
   sudo apt update && sudo apt install -y ydotool wl-clipboard libnotify-bin ffmpeg python3-venv
   ```
3. Set up the Python environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install vosk sounddevice numpy
   ```
4. Start the `ydotool` daemon (required for virtual keyboard input):
   ```bash
   sudo ydotoold --socket-path=$HOME/.ydotool_socket --socket-own=$(id -u):$(id -g)
   ```

## Usage
Map a global keyboard shortcut (e.g., `Super+Shift+V`) in GNOME Settings to run the `dictate.py` script.
- **First Press:** Starts recording. Notification "Recording Start" appears.
- **Second Press:** Stops recording, transcribes, and types the text into your active application.
