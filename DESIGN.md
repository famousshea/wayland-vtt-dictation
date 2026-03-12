# Project Design: Wayland VTT Dictation Tool

## Overview
A lightweight, background-driven voice-to-text (VTT) tool for Ubuntu 25.10 (Wayland). It allows users to dictate text into any active application via a global keyboard shortcut, adding a specific preface for AI context.

## Core Requirements
1. **Lightweight & Headless:** No GUI. Runs as a background process or via a systemd user service.
2. **Wayland Native:** Must handle text input using Wayland-compatible tools (`ydotool` or `wtype`).
3. **Local Processing:** No external API calls. Fast, local transcription (Vosk or Faster-Whisper).
4. **User Feedback:**
   - Desktop notifications (`notify-send`) for "Recording Start/Stop".
   - Audible cues (beeps) for status changes.
5. **Output Handling:**
   - Prefixes text with `(voice to text input) `.
   - Automatically types into the active window.
   - Copies the result to the clipboard for backup/multi-paste.

## Tech Stack
- **Language:** Python 3.
- **Audio Recording:** `sounddevice` or `ffmpeg`.
- **Transcription Engine:** `Vosk` (Lightest) or `Faster-Whisper` (Best accuracy/speed balance).
- **Wayland Input:** `ydotool` (requires a background daemon for virtual keyboard events).
- **Clipboard:** `wl-copy` (Wayland native).
- **Notifications:** `libnotify` via `notify-send`.
- **Audio Cues:** `paplay` or `sox`.

## Architecture
1. **The Orchestrator:** A Python script that toggles recording state.
2. **The Listener:** Uses a global keyboard shortcut (configured in GNOME Settings) to signal the Orchestrator.
3. **The Buffer:** Captures audio to a temporary RAM file (`/dev/shm`) to minimize disk I/O.
4. **The Typist:** After transcription, it executes the "Type" sequence using a virtual keyboard.

## Installation & Setup Plan
1. Install system dependencies (`ydotool`, `libnotify`, `ffmpeg`).
2. Set up a Python Virtual Environment in the project folder.
3. Create the core `dictate.py` script.
4. Configure the `ydotool` daemon (requires `sudo` for initial setup).
5. Map a custom keyboard shortcut in GNOME.
