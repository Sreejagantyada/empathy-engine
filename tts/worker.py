import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import wave

import pyttsx3


def merge_wavs(input_paths: list[Path], output_path: Path) -> None:
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


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python -m tts.worker <payload_json_path> <output_wav_path>", file=sys.stderr)
        return 2

    payload_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not payload:
        print("Payload is empty.", file=sys.stderr)
        return 2

    engine = pyttsx3.init()

    with TemporaryDirectory(prefix="empathy_tts_worker_chunks_") as temp_dir:
        chunk_paths: list[Path] = []
        for idx, item in enumerate(payload):
            chunk_path = Path(temp_dir) / f"chunk_{idx}.wav"
            chunk_paths.append(chunk_path)
            engine.setProperty("rate", int(item["rate"]))
            engine.setProperty("volume", float(item["volume"]))
            engine.save_to_file(str(item["text"]), str(chunk_path))

        engine.runAndWait()
        engine.stop()
        merge_wavs(chunk_paths, output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
