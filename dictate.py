#!/home/sheamus/Repositories/wayland-vtt-dictation/venv/bin/python3
import os
import sys
import subprocess
import signal
import json
import logging

# Configuration
PROJECT_DIR = "/home/sheamus/Repositories/wayland-vtt-dictation"
LOG_FILE = "/tmp/wayland_vtt.log"
STATE_FILE = "/tmp/wayland_vtt_state.pid"
AUDIO_FILE = "/tmp/wayland_vtt_audio.wav"
VOSK_MODEL_PATH = os.path.expanduser("~/.cache/vosk-model-small-en-us-0.15")
SOUND_START = "/usr/share/sounds/gnome/default/alerts/click.ogg"
SOUND_END = "/usr/share/sounds/gnome/default/alerts/string.ogg"
PREFACE = "(voice to text input) "
YDOTOOL_SOCKET = os.path.expanduser("~/.ydotool_socket")

# Add project venv to sys.path
sys.path.insert(0, os.path.join(PROJECT_DIR, "venv/lib/python3.13/site-packages"))

from vosk import Model, KaldiRecognizer

logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def play_sound(sound_path):
    try:
        # Use pw-play for PipeWire (standard on Ubuntu 25.10)
        subprocess.run(["pw-play", sound_path], stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to play sound: {e}")

def notify(msg):
    subprocess.run(["notify-send", "Dictation", msg])

def start_recording():
    if os.path.exists(STATE_FILE):
        logging.info("State file exists, stopping recording.")
        return stop_recording()

    logging.info("Starting recording...")
    play_sound(SOUND_START)
    notify("Recording started...")

    # Record using ffmpeg from pulse/pipewire
    process = subprocess.Popen([
        "ffmpeg", "-y", "-f", "pulse", "-i", "default",
        "-ac", "1", "-ar", "16000", AUDIO_FILE
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    with open(STATE_FILE, "w") as f:
        f.write(str(process.pid))
    logging.info(f"FFmpeg PID {process.pid} written to state file.")

def stop_recording():
    if not os.path.exists(STATE_FILE):
        return

    with open(STATE_FILE, "r") as f:
        pid = int(f.read().strip())

    logging.info(f"Stopping recording (FFmpeg PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        logging.error("FFmpeg process not found.")
    
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    notify("Transcribing...")
    transcribe_and_type()

def transcribe_and_type():
    logging.info("Transcribing audio...")
    if not os.path.exists(AUDIO_FILE):
        logging.error("Audio file not found.")
        notify("Error: No audio recorded.")
        return

    try:
        model = Model(VOSK_MODEL_PATH)
    except Exception as e:
        logging.error(f"Vosk Init Error: {e}")
        notify("Vosk initialization failed.")
        return

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
        logging.info(f"Transcribed text: {text}")
        
        # Copy to clipboard
        subprocess.run(["wl-copy", full_text])
        
        # Type into active window using ydotool
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = YDOTOOL_SOCKET
        subprocess.run(["ydotool", "type", full_text], env=env)
        
        play_sound(SOUND_END)
        notify("Text inserted.")
    else:
        logging.warning("No speech detected.")
        notify("No speech detected.")

    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--stop":
            stop_recording()
        else:
            start_recording()
    except Exception as e:
        logging.exception("Global exception occurred.")
