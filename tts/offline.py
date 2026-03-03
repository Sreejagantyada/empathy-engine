from pathlib import Path
import re
from tempfile import TemporaryDirectory
from threading import Lock
from time import perf_counter
import wave

import logging
from TTS.api import TTS

from tts.base import BaseTTS


logger = logging.getLogger(__name__)


class OfflineTTS(BaseTTS):
    """Offline neural TTS backend using Coqui TTS."""

    _MODEL_CANDIDATES = [
        "tts_models/en/ljspeech/vits",
        "tts_models/en/ljspeech/tacotron2-DDC",
    ]
    _model: TTS | None = None
    _model_name: str | None = None
    _model_lock = Lock()

    def __init__(self) -> None:
        self._speak_lock = Lock()
        self._ensure_model()

    @classmethod
    def _ensure_model(cls) -> None:
        with cls._model_lock:
            if cls._model is None:
                last_error: Exception | None = None
                for model_name in cls._MODEL_CANDIDATES:
                    try:
                        cls._model = TTS(model_name=model_name, progress_bar=False, gpu=False)
                        cls._model_name = model_name
                        logger.info("tts_model_loaded model=%s", model_name)
                        return
                    except Exception as exc:  # pragma: no cover
                        last_error = exc
                        logger.warning("tts_model_load_failed model=%s error=%s", model_name, str(exc))
                raise RuntimeError("Unable to load any configured TTS model.") from last_error

    @property
    def model(self) -> TTS:
        if self.__class__._model is None:
            self._ensure_model()
        return self.__class__._model

    def speak(self, sentences_with_prosody: list[dict], output_path: str) -> None:
        """Synthesize sentence audio with per-sentence prosody and merge into one WAV."""
        if not sentences_with_prosody:
            raise ValueError("sentences_with_prosody cannot be empty")

        start_time = perf_counter()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with self._speak_lock:
            with TemporaryDirectory(prefix="empathy_tts_") as temp_dir:
                chunk_paths: list[Path] = []

                for index, item in enumerate(sentences_with_prosody):
                    chunk_path = Path(temp_dir) / f"chunk_{index}.wav"
                    chunk_paths.append(chunk_path)
                    self._synthesize_chunk(
                        text=self._sanitize_text(str(item["text"])),
                        rate=int(item["rate"]),
                        volume=float(item["volume"]),
                        output_path=chunk_path,
                    )

                self._merge_wavs(chunk_paths, output_file)

        generation_time = perf_counter() - start_time
        logger.info(
            "tts_generation_complete sentences=%d tts_generation_s=%.4f output=%s",
            len(sentences_with_prosody),
            generation_time,
            str(output_file),
        )

    def _synthesize_chunk(self, text: str, rate: int, volume: float, output_path: Path) -> None:
        _ = rate
        _ = volume
        # Use the model-native output path only; extra post-processing caused artifacts.
        self.model.tts_to_file(text=text, file_path=str(output_path))

    @staticmethod
    def _sanitize_text(text: str) -> str:
        # Prevent unstable attention from repeated punctuation patterns.
        cleaned = re.sub(r"([.!?]){2,}", r"\1", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned or " "

    @staticmethod
    def _merge_wavs(input_paths: list[Path], output_path: Path) -> None:
        if not input_paths:
            raise ValueError("input_paths cannot be empty")

        with wave.open(str(input_paths[0]), "rb") as first_wav:
            params = first_wav.getparams()
            frames = [first_wav.readframes(first_wav.getnframes())]

        for path in input_paths[1:]:
            with wave.open(str(path), "rb") as wav_file:
                if wav_file.getparams()[:3] != params[:3]:
                    raise ValueError("Inconsistent WAV parameters while merging audio chunks.")
                frames.append(wav_file.readframes(wav_file.getnframes()))

        with wave.open(str(output_path), "wb") as output_wav:
            output_wav.setparams(params)
            for audio_bytes in frames:
                output_wav.writeframes(audio_bytes)
