from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router
from core.emotion_model import EmotionClassifier
from core.emotion_to_prosody import EmotionToProsody
from core.sentence_processor import SentenceProcessor
from tts.offline import OfflineTTS
import config
import logging
import spacy


def setup_logging() -> None:
    """Configure application-wide structured logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    setup_logging()
    app = FastAPI(title="Empathy Engine")

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(router)

    @app.on_event("startup")
    def on_startup() -> None:
        logger = logging.getLogger(__name__)
        logger.info("startup_begin")

        app.state.emotion_classifier = EmotionClassifier(model_name=config.MODEL_NAME)
        app.state.nlp = spacy.load(config.SPACY_MODEL)
        app.state.sentence_processor = SentenceProcessor(app.state.nlp)
        app.state.emotion_to_prosody = EmotionToProsody()
        app.state.tts = OfflineTTS()

        config.STATIC_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("startup_complete model=%s spacy_model=%s", config.MODEL_NAME, config.SPACY_MODEL)

    return app


app = create_app()
