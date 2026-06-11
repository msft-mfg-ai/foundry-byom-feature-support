"""Assistants API (threads + runs) through AI Gateway connection."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _shared import build_clients, gateway_model  # noqa: E402

MODEL = os.environ.get("CHAT_MODEL", "gpt-5-mini")


def main() -> int:
    cfg, _, aoai = build_clients()
    model = gateway_model(MODEL, cfg)
    print(f"::group::Assistants {model}")
    assistant = aoai.beta.assistants.create(
        name="byom-feature-test",
        instructions="You are a helpful test assistant. Answer briefly.",
        model=model,
    )
    try:
        thread = aoai.beta.threads.create()
        aoai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Say hello in one short sentence.",
        )
        run = aoai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
        for _ in range(60):
            run = aoai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run.status in {"completed", "failed", "cancelled", "expired"}:
                break
            time.sleep(1)
        if run.status != "completed":
            print(f"::error::Run ended with status {run.status}: {run.last_error}")
            return 1
        msgs = aoai.beta.threads.messages.list(thread_id=thread.id, order="desc")
        latest = next(m for m in msgs.data if m.role == "assistant")
        text = latest.content[0].text.value
        print("OK:", text)
    finally:
        try:
            aoai.beta.assistants.delete(assistant.id)
        except Exception:
            pass
    print("::endgroup::")
    return 0


if __name__ == "__main__":
    sys.exit(main())
