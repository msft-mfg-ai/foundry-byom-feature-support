"""BYOM test: tool-memory

Foundry Memory Stores take a `chat_model` and an `embedding_model` at create
time. Both must resolve to a real deployment on the Foundry account — neither
accepts a `{conn}/{deployment}` BYOM prefix. Assert the rejection so the card
stays honest when Foundry either fixes it or breaks the current shape.
"""
import os
import pytest
from azure.ai.projects import AIProjectClient
from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential


@pytest.mark.not_supported
def test_memory_store_rejects_byom_prefix(cfg):
    try:
        from azure.ai.projects.models import MemoryStoreDefaultDefinition
    except ImportError as e:
        pytest.skip(f"MemoryStoreDefaultDefinition not available: {e}")

    preview_project = AIProjectClient(
        endpoint=os.environ["PROJECT_ENDPOINT"],
        credential=DefaultAzureCredential(),
        allow_preview=True,
    )

    gateway = cfg.resolve_gateway("static")
    chat_deployment = os.environ.get("CHAT_MODEL", "gpt-4o-mini")

    with pytest.raises(HttpResponseError) as excinfo:
        preview_project.beta.memory_stores.create(
            name="byom-memstore-probe",
            definition=MemoryStoreDefaultDefinition(
                chat_model=f"{gateway}/{chat_deployment}",
                embedding_model="text-embedding-3-small",
            ),
        )

    msg = str(excinfo.value)
    assert "not found" in msg.lower() or "bad_request" in msg.lower(), (
        f"Expected 'deployment not found' rejection; got: {msg}"
    )

