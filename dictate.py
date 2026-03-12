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
SOUND_START = "/usr/share/sounds/gnome/default/alerts/click.ogg"
SOUND_END = "/usr/share/sounds/gnome/default/alerts/string.ogg"
PREFACE = "(voice to text input) "
YDOTOOL_SOCKET = os.path.expanduser("~/.ydotool_socket")

# Whisper Config
WHISPER_MODEL = "base"  # options: tiny, base, small, medium, large-v3
WHISPER_CACHE = os.path.expanduser("~/.cache/whisper-models")

# Add project venv to sys.path
sys.path.insert(0, os.path.join(PROJECT_DIR, "venv/lib/python3.13/site-packages"))

logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def play_sound(sound_path):
    try:
        subprocess.run(["pw-play", sound_path], stderr=subprocess.DEVNULL)
    except Exception as e:
        logging.error(f"Failed to play sound: {e}")

def notify(msg, expire_time=2000):
    subprocess.run(["notify-send", "-t", str(expire_time), "Dictation", msg])

def start_recording():
    if os.path.exists(STATE_FILE):
        return stop_recording()

    play_sound(SOUND_START)
    notify("Recording started...", 1500)

    # Record using ffmpeg
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
    
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    notify("Transcribing (Whisper)...", 5000)
    transcribe_and_type()

def transcribe_and_type():
    if not os.path.exists(AUDIO_FILE):
        notify("Error: No audio recorded.")
        return

    try:
        from faster_whisper import WhisperModel
        
        # Initialize Whisper
        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8", download_root=WHISPER_CACHE)
        
        segments, info = model.transcribe(AUDIO_FILE, beam_size=5)
        text = " ".join([segment.text for segment in segments]).strip()

    except Exception as e:
        logging.error(f"Whisper Error: {e}. Falling back to Vosk if possible.")
        text = fallback_vosk()

    if text:
        full_text = f"{PREFACE}{text}"
        
        # Copy to clipboard
        subprocess.run(["wl-copy", full_text])
        
        # Type into active window
        env = os.environ.copy()
        env["YDOTOOL_SOCKET"] = YDOTOOL_SOCKET
        subprocess.run(["ydotool", "type", full_text], env=env)
        
        play_sound(SOUND_END)
        notify("Text inserted.")
    else:
        notify("No speech detected.")

    if os.path.exists(AUDIO_FILE):
        os.remove(AUDIO_FILE)

def fallback_vosk():
    VOSK_MODEL_PATH = os.path.expanduser("~/.cache/vosk-model-small-en-us-0.15")
    if not os.path.exists(VOSK_MODEL_PATH):
        return ""
        
    try:
        from vosk import Model, KaldiRecognizer
        model = Model(VOSK_MODEL_PATH)
        process = subprocess.Popen([
            "ffmpeg", "-loglevel", "quiet", "-i", AUDIO_FILE,
            "-ar", "16000", "-ac", "1", "-f", "s16le", "-"
        ], stdout=subprocess.PIPE)

        rec = KaldiRecognizer(model, 16000)
        text = ""
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0: break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                text += res.get("text", "") + " "
        res = json.loads(rec.FinalResult())
        text += res.get("text", "")
        return text.strip()
    except:
        return ""

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--stop":
            stop_recording()
        else:
            start_recording()
    except Exception as e:
        logging.exception("Global exception occurred.")
