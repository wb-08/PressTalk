import os
import logging
import subprocess
import threading
import time
import numpy as np
import pyperclip
import requests
import sounddevice as sd
from dotenv import load_dotenv
from pynput import keyboard
from pynput.keyboard import Key

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('client_presstalk')

SAMPLE_RATE = 16000
_KEY_MAP = {
    'alt_r': Key.alt_r,
    'cmd_r': Key.cmd_r,
    'shift_r': Key.shift_r,
}

SERVER_URL = os.environ.get('SERVER_URL', 'http://localhost:8081/transcribe')
PRESS_KEY = _KEY_MAP.get(os.environ.get('PRESS_KEY', 'alt_r'), Key.alt_r)
_recording = False
_audio_frames: list[np.ndarray] = []


def _audio_callback(indata, frames, time_info, status):
    if _recording:
        _audio_frames.append(indata.copy())


def _frames_to_opus(frames: list[np.ndarray]) -> bytes:
    audio = np.concatenate(frames, axis=0)
    pcm = (audio * 32767).astype(np.int16).tobytes()
    result = subprocess.run(
        ['/opt/homebrew/bin/ffmpeg', '-hide_banner', '-loglevel', 'error',
         '-f', 's16le', '-ar', str(SAMPLE_RATE), '-ac', '1',
         '-i', 'pipe:0', '-c:a', 'libopus', '-b:a', '32k', '-f', 'ogg', 'pipe:1'],
        input=pcm,
        capture_output=True,
        check=True
    )
    return result.stdout


def _send_and_insert(frames: list[np.ndarray]):
    if not frames:
        return

    opus_bytes = _frames_to_opus(frames)
    logger.info(f"Sending {len(opus_bytes) // 1024} KB to the server...")

    try:
        response = requests.post(
            SERVER_URL,
            files={'audio': ('recording.ogg', opus_bytes, 'audio/ogg')},
            timeout=60,
        )
        response.raise_for_status()
        text = response.json().get('text', '').strip()

        if not text:
            logger.warning("The server returned an empty string")
            return

        logger.info(f"Result: {text}")
        pyperclip.copy(' ' + text)
        result = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to key code 9 using command down'],
            capture_output=True,
        )
        if result.returncode != 0:
            logger.error(f"osascript error: {result.stderr.strip()}")

    except requests.exceptions.ConnectionError:
        logger.error(f"No connection to the server {SERVER_URL}")
    except requests.exceptions.Timeout:
        logger.error("The server did not respond within 60 seconds")
    except Exception as e:
        logger.error(f"Error: {e}")


def on_press(key):
    global _recording
    if key == PRESS_KEY and not _recording:
        _recording = True
        _audio_frames.clear()
        logger.info("Recording...")


def on_release(key):
    global _recording
    if key == PRESS_KEY:
        _recording = False
        frames_copy = list(_audio_frames)
        threading.Thread(target=_send_and_insert, args=(frames_copy,), daemon=True).start()


def main():
    logger.info(f"PressTalk has been launched. Hold down {os.environ.get('PRESS_KEY', 'alt_r')} to start recording.")

    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype='float32',
        callback=_audio_callback,
        blocksize=1024,
    )

    with stream:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()


if __name__ == '__main__':
    main()
