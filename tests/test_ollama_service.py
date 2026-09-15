import asyncio

from app.services.ollama import OllamaService


class _Message:
    content = '{"ok": true}'


class _Response:
    message = _Message()


class _FakeClient:
    def __init__(self):
        self.kwargs = None

    def chat(self, **kwargs):
        self.kwargs = kwargs
        return _Response()


def test_chat_passes_system_prompt_and_structured_output_schema():
    service = OllamaService(
        base_url="http://localhost:11434",
        connect_timeout_seconds=2,
        generation_timeout_seconds=30,
        preferred_models=("qwen3:8b",),
    )
    client = _FakeClient()
    service.client = client
    service.selected_model = "qwen3:8b"
    schema = {
        "type": "object",
        "properties": {"ok": {"type": "boolean"}},
        "required": ["ok"],
    }

    result = asyncio.run(
        service.chat(
            "Return a valid object.",
            num_predict=100,
            temperature=0.2,
            system_prompt="Be precise.",
            format_schema=schema,
            think=False,
        )
    )

    assert result == '{"ok": true}'
    assert client.kwargs["format"] == schema
    assert client.kwargs["think"] is False
    assert client.kwargs["messages"][0] == {
        "role": "system",
        "content": "Be precise.",
    }
    assert client.kwargs["messages"][1]["role"] == "user"
