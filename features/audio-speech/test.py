"""Text-to-speech through AI Gateway connection."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("SPEECH_MODEL", "gpt-4o-mini-tts")


def main() -> int:
    cfg, _, aoai = build_clients()
    model = gateway_model(MODEL, cfg)
    print(f"::group::Audio speech {model}")
    out = Path(__file__).parent / "out.mp3"
    with aoai.audio.speech.with_streaming_response.create(
        model=model,
        voice="alloy",
        input="The quick brown fox jumps over the lazy dog.",
    ) as resp:
        resp.stream_to_file(out)
    print(f"OK: wrote {out} ({out.stat().st_size} bytes)")
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
