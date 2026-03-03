from abc import ABC, abstractmethod


class BaseTTS(ABC):
    """Abstract interface for text-to-speech backends."""

    @abstractmethod
    def speak(self, sentences_with_prosody: list[dict], output_path: str) -> None:
        """Generate audio for all sentences and write to a single WAV file."""
        raise NotImplementedError
