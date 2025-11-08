## Title
Reader Elf (reader_elf.py)

## Overview

What ReaderElf does:
- personal text reader, no requirement to be deployed in bulk.
- reads aloud ebooks, web pages, blogs or any text pasted or provided as a .txt file.
- free or low-cost implementation
- reader quality at the same level as Copilot or Grok implementation - good understanding of intonation and context. NO DEFAULT ROBOTIC TTS.

### 📂 Input Formats

- `.txt`, `.html`, `.epub`
- ability to paste long text to read
- Future: `.docx`, `.md`, `.pdf`, `.mobi`

### 🧹 Preprocessing (Planned)

- Remove:
    - Hard line breaks
    - Page numbers        
    - Headers/footers
    - Special symbols (e.g., OCR artifacts)
        
- Normalize:
    - Paragraphs
    - Quotation marks
    - Unicode cleanup

### 🎛️ Controls (MVP)

- Play / Pause / Stop
- Library/ File select
- Auto-resume from last position per library object

## Extended AI features

### 🧠 AI Voice & Comprehension

- **Voice**: Marvis TTS (https://github.com/Marvis-Labs/marvis-tts)

- **Goal**: Use Copilot-quality comprehension for text discussion and word/idiom lookup
    
- **Future**: Voice interaction like:
    - “What does ‘diffident’ mean?”
    - “Summarize this chapter”
    - “Who is the main character?”

## 🧪 Development

### Dev Environment
- DEV_GUIDE.md describes project details and defines MVP product at the end of the document.
- Use as speech model Marvis, #fetch https://github.com/Marvis-Labs/marvis-tts
- The local pyenv already is set to voice. 
- Already includes necessary modules to run this example command:
    > python -m mlx_audio.tts.generate --model Marvis-AI/marvis-tts-250m-v0.1  --stream  --text "Marvis TTS is a new text-to-speech model that provides fast streaming
     on edge devices."
- we dont do unit tests, as they give false positive all too often and add runaway complexity

### Next Steps

1. **Prototype Mac / Windows version** (easier for debugging, file access, and TTS testing)
2. **Integrate TTS** for natural voice
3. **Design minimal UI**: file picker, play/pause, progress bar
4. **Build text cleaner module** (regex + heuristics)
5. **Plan for LLM integration** (Copilot-style comprehension)

### MVP
- include Marvis-TTS as speach model
- ensure minimal procesing to match Marvis requirements
- build basic interface with ability to paste text to read