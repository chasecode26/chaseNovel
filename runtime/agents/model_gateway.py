from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ModelRequest:
    agent: str
    task: str
    prompt: str
    context: dict[str, object]
    temperature: float = 0.7

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ModelResponse:
    provider: str
    model: str
    text: str
    finish_reason: str
    metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class ModelGateway(Protocol):
    def complete(self, request: ModelRequest) -> ModelResponse:
        ...


class LocalDeterministicGateway:
    """Default gateway used when no external model provider is configured."""

    provider = "local"
    model = "deterministic-runtime"

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            provider=self.provider,
            model=self.model,
            text="",
            finish_reason="local-runtime-noop",
            metadata={
                "agent": request.agent,
                "task": request.task,
                "temperature": request.temperature,
                "prompt_chars": len(request.prompt),
                "context_keys": sorted(request.context.keys()),
            },
        )


def write_model_trace(project_dir: Path, chapter: int, response: ModelResponse) -> str:
    trace_dir = project_dir / "04_gate" / f"ch{chapter:03d}" / "model_traces"
    trace_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    path = trace_dir / f"{response.metadata.get('agent', 'agent')}-{timestamp}.json"
    import json

    path.write_text(json.dumps(response.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path.as_posix()
