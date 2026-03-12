# Project Design: Wayland VTT Dictation Tool

## Overview
A lightweight, background-driven voice-to-text (VTT) tool for Ubuntu 25.10 (Wayland). It allows users to dictate high-quality, punctuated text into any active application via a global keyboard shortcut.

## Core Requirements
1. **Lightweight & Headless:** No GUI. Runs as a background process.
2. **Wayland Native:** Must handle text input using `ydotool`.
3. **Local Intelligence:** Uses `Faster-Whisper` (Base) for accurate, punctuated local transcription.
4. **User Feedback:**
   - Desktop notifications (`notify-send`).
   - Audible cues (beeps) for status changes via `pw-play`.
5. **Output Handling:**
   - Prefixes text with `(voice to text input) `.
   - Automatically types into the active window.
   - Copies the result to the clipboard (`wl-copy`) for backup.

## Tech Stack
- **Language:** Python 3.
- **Transcription Engine:** `Faster-Whisper` (Base model).
- **Fallback Engine:** `Vosk` (Lightweight fallback).
- **Wayland Input:** `ydotool` (via `ydotoold` daemon).
- **Notifications:** `libnotify`.
- **Audio Cues:** `pw-play` (PipeWire).

## Architecture
1. **The Orchestrator:** A Python script (`dictate.py`) that toggles recording state using a PID file in `/tmp/`.
2. **The Buffer:** Captures audio using `ffmpeg` from the default PulseAudio/PipeWire source.
3. **The Processor:** Transcribes the audio file using Faster-Whisper, generating a punctuated string.
4. **The Typist:** Simulates keyboard events to "type" the string into the currently focused window.

## Installation & Setup Plan
1. Install system dependencies (`ydotool`, `wl-clipboard`, `ffmpeg`).
2. Configure `uinput` permissions and start the `ydotoold` user service.
3. Set up the Python virtual environment and download models.
4. Map `Super+R` to the `dictate.py` script.
