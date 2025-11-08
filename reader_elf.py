#!/usr/bin/env python3
"""Reader Elf — minimalist CLI for reading text aloud with AI-enabled TTS.

Usage:
  python reader_elf.py --file path/to/file.txt
  python reader_elf.py --text "paste long text here"
  python reader_elf.py --file path/to/file.txt --show-notes

This script reads text either from a --file or from the --text argument 
and streams it to an AI-enabled TTS. 
Informational messages are written to STDERR 
so they won't be accidentally included in the spoken stream
and can be shown if --show-notes is included.
"""
