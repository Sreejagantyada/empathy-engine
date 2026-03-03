class EmotionToProsody:
    """Map dominant emotion to discrete prosody presets."""

    EMOTION_PRESETS = {
        "joy": {"rate": 230, "volume": 1.2},
        "anger": {"rate": 240, "volume": 1.3},
        "sadness": {"rate": 120, "volume": 0.7},
        "fear": {"rate": 220, "volume": 1.1},
        "surprise": {"rate": 250, "volume": 1.2},
        "neutral": {"rate": 170, "volume": 1.0},
    }

    def map(self, emotions: dict[str, float]) -> dict[str, float]:
        if not emotions:
            return self.EMOTION_PRESETS["neutral"]

        dominant = max(emotions, key=emotions.get)
        return self.EMOTION_PRESETS.get(dominant, self.EMOTION_PRESETS["neutral"])
