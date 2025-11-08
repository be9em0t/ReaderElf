## ✅ Refined Requirements (So Far)

### 📱 Platforms

- **Android**: Primary mobile experience
    
- **Windows**: Optional desktop version (likely easier to prototype and debug)
    

### 📂 Input Formats

- `.txt`, `.html`, `.epub`
    
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

- Play / Pause
    
- File select
    
- Auto-resume from last position
    

### 🧠 AI Voice & Comprehension

- **Goal**: Use Copilot-quality voice and understanding, not Android's default TTS
    
- **Future**: Voice interaction like:
    
    - “What does ‘diffident’ mean?”
        
    - “Summarize this chapter”
        
    - “Who is the main character?”
        

## 🔊 How to Harness AI Voice + Comprehension

### 1. **Voice Engine Options**

To replicate Copilot’s natural voice quality, you’ll want **cloud-based neural TTS**:

|Provider|Pros|Notes|
|---|---|---|
|**Microsoft Azure TTS**|Same tech as Copilot, natural voices|Best match|
|Google Cloud TTS|Widely used, multilingual|Slightly robotic at times|
|Amazon Polly|Good quality, SSML support|Less expressive|

**Recommendation**: Start with **Azure TTS**. It supports:

- Natural-sounding neural voices
    
- SSML for emphasis, pauses, etc.
    
- Streaming audio (for real-time playback)
    

### 2. **Architecture for AI Voice**

- **App** sends cleaned text to Azure TTS API
    
- **Receives** audio stream or file
    
- **Plays** audio via media player
    
- **Caches** audio for offline replay (optional)
    

### 3. **Comprehension Layer (Future)**

To support interactions like “What does this mean?”:

- Use **Copilot-style LLM backend** (e.g., Azure OpenAI or local LLM)
    
- Maintain **context window** of current paragraph/chapter
    
- On voice command:
    
    - Transcribe voice (using Whisper or Android SpeechRecognizer)
        
    - Parse intent (e.g., define, summarize, explain)
        
    - Query LLM with context + question
        
    - Respond via TTS
        

## 🧠 Example Flow: “What does ‘diffident’ mean?”

1. User says: “What does diffident mean?”
    
2. App transcribes voice
    
3. App sends: `Define 'diffident' in this context: [current paragraph]` to LLM
    
4. LLM replies: “It means shy or lacking confidence.”
    
5. App reads response aloud using Azure TTS
    

## 🧪 Next Steps

1. **Prototype Windows version** (easier for debugging, file access, and TTS testing)
    
2. **Integrate Azure TTS** for natural voice
    
3. **Build text cleaner module** (regex + heuristics)
    
4. **Design minimal UI**: file picker, play/pause, progress bar
    
5. **Plan for LLM integration** (Copilot-style comprehension)
    
## Diagram

+---------------------+
|  User Interface     | ← Windows (WPF/WinUI) or Android (Jetpack Compose)
+---------------------+
          ↓
+---------------------+
|  File Loader        | ← Reads .txt, .html, .epub, .pdf, .mobi
+---------------------+
          ↓
+---------------------+
|  Text Cleaner       | ← Removes line breaks, page numbers, symbols
+---------------------+
          ↓
+---------------------+
|  TTS Engine         | ← Azure TTS API (neural voice)
+---------------------+
          ↓
+---------------------+
|  Audio Player       | ← Streams or plays cached audio
+---------------------+
          ↓
+---------------------+
|  Progress Tracker   | ← Saves last position per book
+---------------------+
