from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .capabilities import AdapterCapabilities


class AdapterBase(ABC):
    @abstractmethod
    def capabilities(self) -> AdapterCapabilities:
        raise NotImplementedError

    @abstractmethod
    def list_blocks(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def tokenize_with_tags(self, text: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def capture_activations(self, prompt: str, blocks: list[str]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def start_trace(self, trace_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def end_trace(self, trace_id: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def install_passive_hooks(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def remove_hooks(self) -> None:
        raise NotImplementedError

    def intervene(self, _trace_id: str, _patch: dict[str, Any]) -> dict[str, Any]:
        return {"status": "unsupported"}
