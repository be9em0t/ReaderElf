#!/usr/bin/env python3
"""Reader Elf — minimalist CLI for reading text with Marvis TTS.

Usage:
  python reader_elf.py --file path/to/file.txt
  python reader_elf.py --text "paste long text here"
  python reader_elf.py --file path/to/file.txt --show-notes

This script reads text either from a file or from the --text argument,
cleans it with the project's text_cleaner utilities, and streams it to
Marvis TTS via the mlx-audio module. Informational messages are written
to STDERR so they won't be accidentally included in the spoken stream.
"""

import argparse
import subprocess
import sys
from pathlib import Path

from text_cleaner import clean_text, split_notes


def call_marvis_stream(text: str, model: str = "Marvis-AI/marvis-tts-250m-v0.1") -> int:
    """Invoke Marvis TTS via the installed Python executable using the
    mlx_audio module. Returns the subprocess return code.

    If the module is missing or execution fails, an error is printed to
    STDERR and a non-zero code returned.
    """
    python_exe = sys.executable or "python"
    cmd = [python_exe, "-m", "mlx_audio.tts.generate", "--model", model, "--stream", "--text", text]

    # Informational message to STDERR only (so stdout remains clean).
    print("Running Marvis TTS...", file=sys.stderr)
    try:
        proc = subprocess.run(cmd, check=True)
        return proc.returncode
    except FileNotFoundError:
        print("mlx-audio module not found. Install with: pip install -U mlx-audio", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print("Marvis TTS exited with code", e.returncode, file=sys.stderr)
        return e.returncode


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Reader Elf: read text via Marvis TTS")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Path to text file to read")
    group.add_argument("--text", "-t", help="Text to read (wrap in quotes)")
    p.add_argument("--model", "-m", default="Marvis-AI/marvis-tts-250m-v0.1", help="Marvis model id")
    p.add_argument("--show-notes", action="store_true", help="Print detected notes/guidance sections to STDERR (never spoken)")
    args = p.parse_args(argv)

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1
        raw = path.read_text(encoding="utf-8")
    else:
        raw = args.text or ""

    # split out developer/user guidance sections (if present)
    main_text, notes_text = split_notes(raw)

    # Always prefer main_text for reading and NEVER speak notes.
    content_to_speak = main_text.strip()

    if args.show_notes and notes_text:
        print("--- detected notes/guidance section ---", file=sys.stderr)
        print(notes_text, file=sys.stderr)
        print("--- end notes ---", file=sys.stderr)

    if not content_to_speak:
        # If the cleaner determined the document contains only notes/guidance,
        # fall back to speaking the notes so short guidance files can still be
        # read. Inform the user via STDERR so the streamed text remains clean.
        if notes_text:
            print("Warning: document appears to contain only notes/guidance — streaming notes.", file=sys.stderr)
            content_to_speak = notes_text.strip()
        else:
            print("No readable document text detected (file/text appears to contain only notes/guidance).", file=sys.stderr)
            print("Use --show-notes to print the guidance if desired.", file=sys.stderr)
            return 0

    cleaned = clean_text(content_to_speak)

    # Short preview to STDERR (won't be streamed)
    print("--- cleaned text preview (first 300 chars) ---", file=sys.stderr)
    print(cleaned[:300], file=sys.stderr)
    print("--- end preview ---", file=sys.stderr)

    # Call Marvis
    return call_marvis_stream(cleaned, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
