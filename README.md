# Empathy Engine

Sentence-Level Emotion-Aware Speech Synthesis using FastAPI, Transformers, and offline neural TTS.

## Problem Statement

Most text-to-speech systems read text in a flat tone.  
Empathy Engine addresses this by:

- understanding emotion at the **sentence level**
- mapping detected emotion to expressive speech settings
- generating one final audio file that sounds emotionally varied across sentences

This project is designed as a modular, interview-ready backend application with a lightweight web UI.

## What the System Does

Given an input paragraph from the browser:

1. Split text into sentences.
2. Classify each sentence into emotion probabilities using:
   - `j-hartmann/emotion-english-distilroberta-base`
3. Pick the dominant emotion per sentence.
4. Map emotion to a discrete prosody preset (rate, volume).
5. Synthesize each sentence with offline neural TTS (Coqui TTS).
6. Merge sentence audio chunks into one `.wav`.
7. Return sentence-level analysis + audio URL to the frontend.

## Current Architecture

- `app/`
  - `main.py`: FastAPI app creation, startup lifecycle, dependency wiring.
  - `routes.py`: UI route + `POST /generate` pipeline.
- `core/`
  - `sentence_processor.py`: spaCy-based sentence segmentation.
  - `emotion_model.py`: Hugging Face emotion classifier + LRU caching.
  - `emotion_to_prosody.py`: dominant emotion -> prosody presets.
- `tts/`
  - `base.py`: abstract TTS interface.
  - `offline.py`: offline Coqui TTS backend, per-sentence synthesis, WAV merging.
- `templates/`, `static/`: HTML + JS UI.
- `config.py`: app-level constants.

## Emotion and Prosody Strategy

The current implementation uses **dominant emotion mapping** (not valence/arousal):

- joy -> faster, louder
- sadness -> slower, softer
- anger -> very fast, louder
- fear -> fast, moderate loudness
- surprise -> fastest, louder
- neutral -> baseline

This gives stronger audible contrast than subtle continuous scaling.

## API

### `POST /generate`

Request:

```json
{
  "text": "I got selected for my dream job. I feel exhausted and hopeless."
}
```

Response:

```json
{
  "sentences": [
    {
      "text": "I got selected for my dream job.",
      "emotions": {
        "joy": 0.92,
        "neutral": 0.04,
        "surprise": 0.03
      },
      "dominant_emotion": "joy",
      "rate": 230,
      "volume": 1.2
    }
  ],
  "audio_url": "/static/audio/output_1234567890.wav"
}
```

## Performance and Reliability

- Transformer classifier is loaded once at startup.
- spaCy NLP pipeline is loaded once at startup.
- TTS model is loaded once at startup.
- Emotion inference uses LRU caching for repeated sentences.
- Structured logging is used for:
  - model inference timing
  - TTS generation timing
  - total pipeline timing

## Setup

### 1. Create virtual environment

```bash
python -m venv venv
```

Activate:

- Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

If `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

If not, install manually:

```bash
pip install fastapi uvicorn transformers torch spacy jinja2 TTS numpy
```

### 3. Download spaCy English model

```bash
python -m spacy download en_core_web_sm
```

## Run

```bash
uvicorn app.main:app --reload
```

Open:

- `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`

## Known Limitations

- Some Coqui models may require additional system dependencies.
- Very long or punctuation-heavy inputs can degrade neural synthesis quality.
- Output quality depends on model choice and CPU/GPU availability.

## Future Improvements

- Add model selection in config (quality vs speed profiles).
- Add sentence-level regeneration fallback for corrupted chunks.
- Add streaming audio endpoint.
- Add Dockerfile and production deployment profile.
- Add automated audio quality checks in tests.
