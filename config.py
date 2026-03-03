"""Application configuration values for Empathy Engine."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_AUDIO_DIR = BASE_DIR / "static" / "audio"
OUTPUT_AUDIO_FILENAME = "output.wav"

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
SPACY_MODEL = "en_core_web_sm"

BASE_RATE = 180
BASE_VOLUME = 1.0
AROUSAL_RATE_SCALE = 70
AROUSAL_VOLUME_SCALE = 0.4

RATE_MIN = 120
RATE_MAX = 240

VOLUME_MIN = 0.5
VOLUME_MAX = 1.5

EMOTION_VA_MAP = {
    "joy": (0.9, 0.7),
    "sadness": (-0.9, -0.5),
    "anger": (-0.7, 0.8),
    "fear": (-0.8, 0.6),
    "surprise": (0.0, 0.9),
    "disgust": (-0.6, 0.4),
    "neutral": (0.0, 0.0),
}
