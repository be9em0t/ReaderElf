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
import tempfile
import os
import gc

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


def inprocess_stream(text: str, model: str = "Marvis-AI/marvis-tts-250m-v0.1") -> int:
    """Load the TTS model in-process and stream paragraph-by-paragraph.

    This avoids model reload on each paragraph. Playback uses macOS `afplay`
    (blocking). If required dependencies are missing, this function falls
    back to calling the external mlx-audio module per entire text.
    """
    # Try best-effort to clear previous GPU memory and Python GC.
    try:
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()

    # Prevent tokenizers parallelism deadlock after forking by disabling it
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

    import importlib
    # Ensure local playback / audio libs exist first
    try:
        import soundfile as sf
        import numpy as np
    except Exception as e:
        print("ERROR: in-process mode requires 'soundfile' and 'numpy':", e, file=sys.stderr)
        print("Exiting.", file=sys.stderr)
        return 2

    # Prefer pygame for in-memory playback to avoid temp files and blocking system calls
    pygame_available = False
    try:
        import io
        import pygame
        pygame.mixer.init(frequency=22050, size=-16, channels=1)
        pygame_available = True
    except Exception:
        pygame_available = False

    TTS = None
    mlx_mod = None
    # Try several plausible import paths and attribute locations
    try:
        mlx_mod = importlib.import_module('mlx_audio.tts')
        if hasattr(mlx_mod, 'TTS'):
            TTS = getattr(mlx_mod, 'TTS')
    except Exception:
        # try top-level
        try:
            mlx_root = importlib.import_module('mlx_audio')
            # common placements
            if hasattr(mlx_root, 'TTS'):
                TTS = getattr(mlx_root, 'TTS')
            elif hasattr(mlx_root, 'tts') and hasattr(mlx_root.tts, 'TTS'):
                TTS = getattr(mlx_root.tts, 'TTS')
            else:
                mlx_mod = getattr(mlx_root, 'tts', None)
        except Exception:
            mlx_mod = None

    use_model_obj = None
    if TTS is None:
        # Fall back to model loader used by the CLI internals (generate.py)
        try:
            utils = importlib.import_module('mlx_audio.tts.utils')
            # load_model returns a model instance with .generate(...)
            loader = getattr(utils, 'load_model')
            print("No TTS class; will use mlx_audio.tts.utils.load_model to load model in-process.", file=sys.stderr)
        except Exception as e:
            # If even the utils loader is missing, print available names for debugging and exit
            try:
                names = []
                if mlx_mod is not None:
                    names = [n for n in dir(mlx_mod) if not n.startswith('_')]
                else:
                    root = importlib.import_module('mlx_audio')
                    names = [n for n in dir(root) if not n.startswith('_')]
                print("ERROR: mlx_audio present but no usable loader found. Available names:", file=sys.stderr)
                print(', '.join(names[:200]), file=sys.stderr)
            except Exception:
                pass
            print("ERROR: In-process TTS unavailable (no TTS class and no loader).", file=sys.stderr)
            print("Exiting.", file=sys.stderr)
            return 3

    # Decide device
    device = None
    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        device = "cpu"

    print(f"Loading Marvis model '{model}' on device {device}...", file=sys.stderr)
    # Default sample rate; will be overridden if the model exposes one
    sample_rate = 22050
    # If we have a TTS class, use it; otherwise use the loader from utils
    try:
        if TTS is not None:
            if hasattr(TTS, 'from_pretrained'):
                tts = TTS.from_pretrained(model, device=device)
            else:
                try:
                    tts = TTS(model, device=device)
                except Exception:
                    if hasattr(TTS, 'load'):
                        tts = TTS.load(model, device=device)
                    else:
                        raise
            # When TTS class exists, we will call tts(...) per paragraph as before
            use_model_obj = None
        else:
            # Use the lower-level loader to create a model object with .generate
            # loader is already bound above
            model_obj = loader(model)
            # model_obj should expose .sample_rate and .generate(...)
            sample_rate = getattr(model_obj, 'sample_rate', sample_rate)
            use_model_obj = model_obj
            tts = None
    except Exception as e:
        print("ERROR: Failed to load in-process model:", e, file=sys.stderr)
        print("Exiting.", file=sys.stderr)
        return 4

    # Split into paragraphs only (no sentence chunking, no overlap)
    import re as _re
    paragraphs = [p.strip() for p in _re.split(r'\n\s*\n+', text) if p.strip()]
    if not paragraphs:
        # nothing to speak
        return 0

    # Try to determine sample rate; default to 22050
    sample_rate = getattr(tts, 'sample_rate', 22050)

    for i, para in enumerate(paragraphs, 1):
        # Attempt to reset any model-internal state between paragraphs if available.
        if i > 1:
            for reset_name in ('reset_state', 'reset', 'clear_cache'):
                fn = getattr(tts, reset_name, None)
                if callable(fn):
                    try:
                        fn()
                        print(f"Called tts.{reset_name}() to clear state before paragraph {i}.", file=sys.stderr)
                        break
                    except Exception:
                        # ignore and try next
                        pass

        print(f"Generating paragraph {i}/{len(paragraphs)}...", file=sys.stderr)
        try:
            # If we loaded a model object, call its generate API
            if use_model_obj is not None:
                    # Use streaming generation to receive and play chunks as they are produced
                    results = use_model_obj.generate(
                        text=para,
                        voice=None,
                        speed=1.0,
                        lang_code='a',
                        ref_audio=None,
                        ref_text=None,
                        temperature=0.7,
                        max_tokens=1200,
                        verbose=False,
                        stream=True,
                        streaming_interval=1.0,
                    )

                    received = False
                    arr_list = []
                    for result in results:
                        received = True
                        chunk = result.audio
                        sample_rate = getattr(result, 'sample_rate', sample_rate)
                        # Play chunk immediately if pygame available, else buffer
                        if pygame_available:
                            # write chunk to in-memory WAV and play
                            with io.BytesIO() as wb:
                                sf.write(wb, chunk, sample_rate, format='WAV')
                                wb.seek(0)
                                try:
                                    s = pygame.mixer.Sound(wb)
                                    ch = s.play()
                                    # block until this chunk finishes to maintain order
                                    while ch.get_busy():
                                        pygame.time.delay(20)
                                except Exception as e:
                                    # fall back to buffering
                                    arr_list.append(chunk)
                        else:
                            arr_list.append(chunk)

                    if not received:
                        print("ERROR: model.generate returned no audio for paragraph.", file=sys.stderr)
                        return 5

                    if not pygame_available:
                        # concatenate all chunks and assign to arr for playback below
                        arr = np.concatenate(arr_list, axis=0)
            else:
                # Primary call pattern for TTS callable
                try:
                    audio = tts(para)
                except TypeError:
                    audio = tts(para, reference_audio=None)
                arr = np.asarray(audio)
        except Exception as e:
            print("ERROR: TTS generation failed for paragraph:", e, file=sys.stderr)
            return 5

        # Expect numpy array-like; arr is already set for both code paths above
        try:
            arr = np.asarray(arr)
        except Exception:
            print("ERROR: Unexpected audio format from TTS; aborting.", file=sys.stderr)
            return 6

        # Append short silence to prevent concatenation confusion (250ms)
        try:
            silence = np.zeros(int(sample_rate * 0.25), dtype=arr.dtype)
            arr = np.concatenate([arr, silence])
        except Exception:
            # if dtype or concat fails, ignore
            pass

        # Write to a temp WAV file and play via afplay (macOS)
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tf:
                tmpname = tf.name
            sf.write(tmpname, arr, sample_rate, format='WAV')
            # Play and block until finished
            subprocess.run(["afplay", tmpname], check=True)
        except FileNotFoundError:
            print("ERROR: Playback utility not found (afplay).", file=sys.stderr)
            return 7
        except subprocess.CalledProcessError as e:
            print("ERROR: Playback failed:", e, file=sys.stderr)
            return 8
        finally:
            try:
                os.remove(tmpname)
            except Exception:
                pass

    # Unload model and free GPU memory
    try:
        del tts
        gc.collect()
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass
    except Exception:
        pass

    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Reader Elf: read text via Marvis TTS")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", "-f", help="Path to text file to read")
    group.add_argument("--text", "-t", help="Text to read (wrap in quotes)")
    p.add_argument("--model", "-m", default="Marvis-AI/marvis-tts-250m-v0.1", help="Marvis model id")
    p.add_argument("--show-notes", action="store_true", help="Print detected notes/guidance sections to STDERR (never spoken)")
    p.add_argument("--inprocess", action="store_true", help="Load TTS model in-process and stream paragraph-by-paragraph (keeps model loaded)")
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

    # Call Marvis: prefer in-process if requested
    if getattr(args, 'inprocess', False):
        return inprocess_stream(cleaned, model=args.model)
    return call_marvis_stream(cleaned, model=args.model)


if __name__ == "__main__":
    raise SystemExit(main())
