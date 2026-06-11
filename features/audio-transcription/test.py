"""Speech-to-text through AI Gateway connection.

Generates a short audio clip via the audio-speech endpoint first, then
transcribes it. If the speech endpoint is not yet supported, falls back to
a checked-in sample.wav (if present) - otherwise the test is skipped.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("TRANSCRIPTION_MODEL", "whisper")
SPEECH_MODEL = os.environ.get("SPEECH_MODEL", "gpt-4o-mini-tts")


def main() -> int:
    cfg, _, aoai = build_clients()

    audio_path = Path(__file__).parent / "sample.mp3"
    if not audio_path.exists():
        print("Generating sample audio via TTS...")
        try:
            with aoai.audio.speech.with_streaming_response.create(
                model=gateway_model(SPEECH_MODEL, cfg),
                voice="alloy",
                input="Hello world, this is a transcription test.",
            ) as r:
                r.stream_to_file(audio_path)
        except Exception as e:
            print(f"::warning::Cannot generate sample (TTS failed): {e}")
            print("::warning::Skipping transcription test (no sample.mp3 available)")
            return 0

    model = gateway_model(MODEL, cfg)
    print(f"::group::Audio transcription {model}")
    with open(audio_path, "rb") as f:
        t = aoai.audio.transcriptions.create(model=model, file=f)
    print("OK:", t.text)
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
