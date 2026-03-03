from functools import lru_cache
from time import perf_counter

from transformers import pipeline
import logging


logger = logging.getLogger(__name__)


class EmotionClassifier:
    """Sentence-level multi-class emotion classifier with cached inference."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._pipeline = pipeline(
            task="text-classification",
            model=model_name,
            top_k=None,
        )

    def classify(self, text: str) -> dict[str, float]:
        """Return the full emotion probability distribution for a sentence."""
        normalized_text = text.strip()
        if not normalized_text:
            return {}

        start_time = perf_counter()
        probabilities_tuple = self._classify_cached(normalized_text)
        inference_time = perf_counter() - start_time

        cache_info = self._classify_cached.cache_info()
        logger.info(
            "emotion_inference sentence_len=%d inference_s=%.4f cache_hits=%d cache_misses=%d",
            len(normalized_text),
            inference_time,
            cache_info.hits,
            cache_info.misses,
        )

        return dict(probabilities_tuple)

    @lru_cache(maxsize=4096)
    def _classify_cached(self, text: str) -> tuple[tuple[str, float], ...]:
        """Cached model inference returning a hashable representation."""
        output = self._pipeline(text)

        # Transformers can return either:
        # 1) [[{"label": "...", "score": ...}, ...]]
        # 2) [{"label": "...", "score": ...}, ...]
        if isinstance(output, list) and output:
            first_item = output[0]
            if isinstance(first_item, list):
                all_scores = first_item
            elif isinstance(first_item, dict):
                all_scores = output
            else:
                raise TypeError(f"Unexpected pipeline output item type: {type(first_item)!r}")
        else:
            raise TypeError(f"Unexpected pipeline output type: {type(output)!r}")

        normalized_scores = tuple(
            (str(item["label"]).lower(), float(item["score"])) for item in all_scores
        )
        return normalized_scores
