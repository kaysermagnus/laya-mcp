"""models.yaml registry: the candidate set route_model chooses among."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = "models.yaml"


class RegistryError(RuntimeError):
    """Registry missing or malformed — message names file and fix."""


@dataclass(frozen=True)
class Entry:
    label: str
    criteria: str
    default: bool = False


@dataclass(frozen=True)
class Registry:
    """Parsed candidate entries; `default` is the marked one or the first."""

    entries: tuple[Entry, ...]
    path: str = DEFAULT_PATH

    @property
    def default(self) -> Entry:
        return next((e for e in self.entries if e.default), self.entries[0])

    @property
    def labels(self) -> list[str]:
        return [e.label for e in self.entries]

    def check_routable(self) -> None:
        """route_model needs at least two candidates to choose between."""
        if len(self.entries) < 2:
            raise RegistryError(
                f"registry at {self.path} has {len(self.entries)} entries — "
                f"route_model needs at least 2; add entries to models.yaml"
            )

    @classmethod
    def load(cls, path: str | Path | None = None) -> Registry:
        p = Path(path or os.environ.get("LAYA_REGISTRY", DEFAULT_PATH))
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except OSError as e:
            raise RegistryError(f"cannot read registry at {p}: {e}") from e
        raw = (doc or {}).get("models") or []
        entries = tuple(
            Entry(
                label=str(e["label"]),
                criteria=str(e.get("criteria", "")),
                default=bool(e.get("default", False)),
            )
            for e in raw
        )
        return cls(entries=entries, path=str(p))
