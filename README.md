# PressTalk

Hold a key → speak → transcribed text is pasted at the cursor. Supports Russian and English with automatic language detection per request.

**Components:**
- **Client** — macOS background agent, records audio on keypress and sends it to the server
- **Server** — docker container with GPU inference (GigaAM for Russian, Whisper for English). You can add your own languages by adding the necessary models and editing the code in the server.py file.

---

## Server

**Requirements:** Linux host with an NVIDIA GPU, Docker, NVIDIA Container Toolkit.

### Download and place model weights

Download the models and place them into `server/weights/`:

- [whisper_base](https://huggingface.co/Systran/faster-whisper-base) → `server/weights/whisper_base/`
- [whisper_medium](https://huggingface.co/Systran/faster-whisper-medium.en) → `server/weights/whisper_medium/`
- [segmentation_model](https://huggingface.co/pyannote/segmentation-3.0) → `server/weights/segmentation_model/`
- [gigaAM](https://github.com/salute-developers/GigaAM) → `server/weights/gigaAM/`. On this page you can find info how to download model

### 2. Build and start

```bash
cd server
docker compose up -d --build
```

---

## Client

**Requirements:** macOS, [uv](https://github.com/astral-sh/uv).

### Configure `.env`

Change the environment variables in `client/.env`:

```
SERVER_URL=http://<server-ip>:8081/transcribe
PRESS_KEY=alt_r
```

Available `PRESS_KEY` values:

| Value | Key |
|---|---|
| `alt_r` | Right Option ⌥ (default) |
| `cmd_r` | Right Command ⌘ |
| `shift_r` | Right Shift ⇧ |

### Install

```bash
cd client
./install.sh
```

This installs dependencies, registers a `launchd` agent that starts automatically on login and restarts on crash.

### Grant macOS permissions

Both permissions must be granted to `/opt/homebrew/bin/uv` (or wherever `which uv` points).

**Microphone** — macOS only adds apps after they request access. Run once manually to trigger the dialog:
```bash
cd client && uv run client.py
```
Click **OK**, then the entry appears in System Settings → Privacy & Security → Microphone.

**Accessibility** — required for keystroke capture and paste:

System Settings → Privacy & Security → Accessibility → add `/opt/homebrew/bin/uv`

### Management

```bash
# restart after changes to client.py
launchctl unload ~/Library/LaunchAgents/com.presstalk.client.plist
launchctl load ~/Library/LaunchAgents/com.presstalk.client.plist

# check status
launchctl list | grep presstalk

# live logs
tail -f ~/Library/Logs/presstalk.log
```