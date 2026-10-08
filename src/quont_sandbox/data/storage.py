"""Raw source evidence storage port and result metadata."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import UUID

from quont_sandbox.common import to_utc


@dataclass(frozen=True)
class RawArtifact:
    artifact_id: UUID
    provider_id: UUID
    acquired_at: datetime
    path: Path
    checksum_sha256: str
    size_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "acquired_at", to_utc(self.acquired_at))


class RawStorage(Protocol):
    def store_bytes(
        self, content: bytes, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact: ...

    def store_text(
        self, content: str, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact: ...

    def store_file(
        self, source: Path, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact: ...
