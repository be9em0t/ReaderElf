# Reader Elf — MVP

This repository contains a minimal CLI prototype for the Reader Elf MVP. It reads text from a file or a pasted string, performs lightweight cleaning, and streams audio using Marvis TTS via the `mlx-audio` CLI (python -m mlx_audio.tts.generate).

Usage examples:

python reader_elf.py --file examples/sample.txt

python reader_elf.py --text "Paste long text here to be read aloud"

Notes:
- Requires Python and the `mlx-audio` package available in the active environment (pyenv "voice" as mentioned in project docs).
- If `mlx-audio` isn't installed, the script will print an install hint.

Next steps:
- Add GUI (minimal Electron or native macOS window) and playback controls
- Support `.epub`, `.html`, `.md` and preserve structural metadata
- Add resume position and per-file library
