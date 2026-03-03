# Empathy Engine - Sentence-Level Affective Prosody System

## Architecture Overview

Empathy Engine is a modular FastAPI application with clear separation of concerns:

- `app/`: FastAPI lifecycle, routing, dependency injection, and API/web endpoints.
- `core/`: NLP sentence splitting, transformer-based emotion classification, valence-arousal computation, and prosody mapping.
- `tts/`: Pluggable text-to-speech abstraction and offline implementation (`pyttsx3`).
- `templates/` and `static/`: Browser UI with AJAX requests and sentence-level result visualization.
- `config.py`: Centralized tunable hyperparameters and model settings.

Startup initializes all heavyweight resources once and stores them in `app.state`:

- Hugging Face emotion model pipeline
- spaCy language model
- Offline TTS engine wrapper

These are injected into request handlers via FastAPI `Depends`.

## Valence-Arousal Modeling

The system converts multi-class emotion probabilities into continuous affect values.

Emotion map (`EMOTION_VA_MAP`):

- joy -> (0.9, 0.7)
- sadness -> (-0.9, -0.5)
- anger -> (-0.7, 0.8)
- fear -> (-0.8, 0.6)
- surprise -> (0.0, 0.9)
- disgust -> (-0.6, 0.4)
- neutral -> (0.0, 0.0)

For each sentence:

- `Valence = sum(prob_i * valence_i)`
- `Arousal = sum(prob_i * arousal_i)`

The full probability distribution is used; top-1-only mapping is not used.

## Prosody Formulas

Prosody is computed from arousal only (config-driven):

- `rate = BASE_RATE + (arousal * AROUSAL_RATE_SCALE)`
- `volume = BASE_VOLUME + (abs(arousal) * AROUSAL_VOLUME_SCALE)`

Then values are clamped:

- `RATE_MIN <= rate <= RATE_MAX`
- `VOLUME_MIN <= volume <= VOLUME_MAX`

No emotion-specific branching is used.

## Performance Optimizations

- Transformer model loaded once at startup.
- spaCy model loaded once at startup.
- `pyttsx3` engine initialized once (singleton-style in `OfflineTTS`).
- Emotion inference cached with `functools.lru_cache` at sentence level.

Structured logging captures:

- sentence count
- emotion inference timing
- TTS generation timing
- average valence/arousal
- full pipeline timing

## Caching Details

`EmotionClassifier` uses an internal `@lru_cache(maxsize=4096)` method keyed by normalized sentence text.
Repeated sentences skip model recomputation and return cached probability distributions.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Download spaCy model:

```bash
python -m spacy download en_core_web_sm
```

## Run

```bash
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

## API

`POST /generate`

Request:

```json
{ "text": "I am excited. But a little nervous." }
```

Response:

```json
{
  "sentences": [
    {
      "text": "I am excited.",
      "emotions": {"joy": 0.7, "fear": 0.1, "neutral": 0.2},
      "valence": 0.55,
      "arousal": 0.53,
      "rate": 201,
      "volume": 1.106
    }
  ],
  "audio_url": "/static/audio/output.wav"
}
```

## Future Extensibility

- Add GoogleTTS backend by implementing `BaseTTS` and swapping dependency in startup.
- Add streaming endpoint for incremental sentence audio delivery.
- Add Dockerization for reproducible deployment and CI/CD integration.
