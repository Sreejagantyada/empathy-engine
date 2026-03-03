from pathlib import Path
from time import perf_counter
from time import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import logging
import config


logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")


class GenerateRequest(BaseModel):
    text: str


class SentenceResult(BaseModel):
    text: str
    emotions: dict[str, float]
    dominant_emotion: str
    rate: int
    volume: float


class GenerateResponse(BaseModel):
    sentences: list[SentenceResult]
    audio_url: str


def get_emotion_classifier(request: Request) -> Any:
    return request.app.state.emotion_classifier


def get_sentence_processor(request: Request) -> Any:
    return request.app.state.sentence_processor


def get_emotion_to_prosody(request: Request) -> Any:
    return request.app.state.emotion_to_prosody


def get_tts(request: Request) -> Any:
    return request.app.state.tts


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@router.post("/generate", response_model=GenerateResponse)
def generate(
    payload: GenerateRequest,
    sentence_processor: Any = Depends(get_sentence_processor),
    emotion_classifier: Any = Depends(get_emotion_classifier),
    emotion_to_prosody: Any = Depends(get_emotion_to_prosody),
    tts: Any = Depends(get_tts),
) -> GenerateResponse:
    start_time = perf_counter()
    text = payload.text.strip()

    if not text:
        raise HTTPException(status_code=400, detail="Text input cannot be empty.")

    sentences = sentence_processor.split_sentences(text)
    if not sentences:
        raise HTTPException(status_code=400, detail="No valid sentences found.")

    sentence_results: list[SentenceResult] = []
    tts_inputs: list[dict[str, Any]] = []

    for sentence in sentences:
        emotions = emotion_classifier.classify(sentence)
        dominant = max(emotions, key=emotions.get) if emotions else "neutral"
        prosody = emotion_to_prosody.map(emotions)
        rate = int(prosody["rate"])
        volume = float(prosody["volume"])

        tts_sentence = sentence
        if dominant == "joy":
            tts_sentence = sentence + "!"
        elif dominant == "sadness":
            tts_sentence = sentence
        elif dominant == "anger":
            tts_sentence = sentence + "!"
        elif dominant == "fear":
            tts_sentence = sentence

        sentence_results.append(
            SentenceResult(
                text=sentence,
                emotions=emotions,
                dominant_emotion=dominant,
                rate=rate,
                volume=volume,
            )
        )
        tts_inputs.append({"text": tts_sentence, "rate": rate, "volume": volume})

    output_filename = f"output_{int(time() * 1000)}.wav"
    output_path = Path(config.STATIC_AUDIO_DIR) / output_filename
    try:
        tts.speak(tts_inputs, str(output_path))
    except Exception as exc:
        logger.exception("tts_generation_failed sentences=%d error=%s", len(tts_inputs), str(exc))
        raise HTTPException(status_code=503, detail="TTS backend is temporarily unavailable. Please retry.") from exc

    sentence_count = len(sentence_results)
    total_pipeline_time = perf_counter() - start_time

    logger.info(
        "pipeline_complete sentences=%d total_pipeline_s=%.4f",
        sentence_count,
        total_pipeline_time,
    )

    return GenerateResponse(
        sentences=sentence_results,
        audio_url=f"/static/audio/{output_filename}",
    )
