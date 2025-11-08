import torch
import mlx.core as mx
import mlx.nn as nn
import pygame
import io
import soundfile as sf
from mlx_audio.tts import TTS  # For MLX inference
import re
import numpy as np

# Setup TTS (adjust device; use 'cpu' if no GPU)
device = mx.gpu if mx.gpu_is_available() else mx.cpu
tts = TTS.from_pretrained("Marvis-AI/marvis-tts-250m-v0.1", device=device)

# Reference audio for voice style (provide your own ~10s WAV)
ref_audio_path = "ref.wav"  # Clone from this for natural tone

# Read input (from file or paste as string)
input_text = ""  # Or paste long text here
if not input_text:
    with open('book.txt', 'r', encoding='utf-8') as f:
        input_text = f.read()

# Split into sentences for chunking (avoids rushed output)
sentences = re.split(r'(?<=[\.\!\?])\s+', input_text.strip())
chunks = [s.strip() for s in sentences if s.strip()]

# Init Pygame for playback
pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=4096)  # Adjust freq to model output (typically 22kHz)

# Generate and play chunks sequentially (streaming feel)
for chunk in chunks:
    # Generate audio (with expressiveness; tweak params per docs)
    audio = tts(chunk, reference_audio=ref_audio_path, expressiveness=0.5)  # Returns numpy array or similar
    
    # Play in-memory
    with io.BytesIO() as wav_buffer:
        sf.write(wav_buffer, audio, 22050, format='WAV')  # Model sample rate
        wav_buffer.seek(0)
        sound = pygame.mixer.Sound(wav_buffer)
    sound.play()
    
    # Wait for chunk to finish before next
    while pygame.mixer.get_busy():
        pygame.time.delay(100)

print("Playback complete!")