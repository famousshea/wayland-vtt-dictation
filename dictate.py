#!/home/sheamus/Repositories/wayland-vtt-dictation/venv/bin/python3
import os
import sys
import subprocess
import time
import signal
import json

# Configuration
PROJECT_DIR = "/home/sheamus/Repositories/wayland-vtt-dictation"
STATE_FILE = "/tmp/wayland_vtt_state.pid"
AUDIO_FILE = "/tmp/wayland_vtt_audio.wav"
VOSK_MODEL_PATH = os.path.expanduser("~/.cache/vosk-model-small-en-us-0.15")
SOUND_START = "/usr/share/sounds/gnome/default/alerts/click.ogg"
SOUND_END = "/usr/share/sounds/gnome/default/alerts/string.ogg"
PREFACE = "(voice to text input) "
YDOTOOL_SOCKET = os.path.expanduser("~/.ydotool_socket")

# Add project venv to sys.path if needed
sys.path.insert(0, os.path.join(PROJECT_DIR, "venv/lib/python3.13/site-packages"))

from vosk import Model, KaldiRecognizer

# Ensure model exists
if not os.path.exists(VOSK_MODEL_PATH):
    notify_err = ["notify-send", "VTT Error", "Vosk model not found. See README."]
    subprocess.run(notify_err)
    sys.exit(1)

def play_sound(sound_path):
    subprocess.run(["paplay", sound_path], stderr=subprocess.DEVNULL)

def notify(msg):
    subprocess.run(["notify-send", "Dictation", msg])

def start_recording():
    if os.path.exists(STATE_FILE):
        return stop_recording()

    notify("Recording started...")
    play_sound(SOUND_START)

    # Use ffmpeg to record to a file in the background
    process = subprocess.Popen([
        "ffmpeg", "-y", "-f", "pulse", "-i", "default",
        "-ac", "1", "-ar", "16000", AUDIO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(STATE_FILE, "w") as f:
        f.write(str(process.pid))

def stop_recording():
    if not os.path.exists(STATE_FILE):
        return

    with open(STATE_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    os.remove(STATE_FILE)
    notify("Transcribing...")
    
    transcribe_and_type()

def transcribe_and_type():
    try:
        model = Model(VOSK_MODEL_PATH)
    except Exception as e:
        notify(f"Vosk Init Error: {e}")
        return

    # Process audio file with Vosk
    process = subprocess.Popen([
        "ffmpeg", "-loglevel", "quiet", "-i", AUDIO_FILE,
        "-ar", "16000", "-ac", "1", "-f", "s16le", "-"
    ], stdout=subprocess.PIPE)

    rec = KaldiRecognizer(model, 16000)
    text = ""

    while True:
        data = process.stdout.read(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            text += res.get("text", "") + " "

    res = json.loads(rec.FinalResult())
    text += res.get("text", "")
    text = text.strip()

    if text:
        full_text = f"{PREFACE}{text}"
        
        # Copy to clipboard
        subprocess.run(["wl-copy", full_text])
        
        # Type into active window using ydotool
        # Use YDOTOOL_SOCKET environment variable
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = YDOTOOL_SOCKET
        subprocess.run([
            "ydotool", "type", full_text
        ], env=env)
        
        play_sound(SOUND_END)
        notify("Text inserted.")
    else:
        notify("No speech detected.")

    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--stop":
        stop_recording()
    else:
        start_recording()
