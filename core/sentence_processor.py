from spacy.language import Language


class SentenceProcessor:
    """Split free-form text into sentence units using spaCy."""

    def __init__(self, nlp: Language) -> None:
        self._nlp = nlp

    def split_sentences(self, text: str) -> list[str]:
        """Return cleaned sentence strings extracted by spaCy."""
        doc = self._nlp(text)
        return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
