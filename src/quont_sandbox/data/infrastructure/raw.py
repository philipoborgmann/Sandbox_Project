"""Local append-only raw storage with checksums and safe filenames."""

import hashlib
import re
from datetime import datetime
from pathlib import Path, PureWindowsPath
from uuid import UUID, uuid4

from quont_sandbox.common import DataError, ValidationError, to_utc

from ..storage import RawArtifact


class LocalRawStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def storage_path(self, artifact_id: UUID, filename: str) -> Path:
        """Reject separators, drive paths, reserved Windows names and unsafe suffixes."""
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,199}", filename)
            or filename.endswith((".", " "))
            or PureWindowsPath(filename).is_reserved()
        ):
            raise ValidationError("Raw filename must be a safe single path component")
        path = (self.root / str(artifact_id) / filename).resolve()
        if not path.is_relative_to(self.root):
            raise ValidationError("Raw path escapes the storage root")
        return path

    def store_bytes(
        self, content: bytes, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact:
        acquired_at = to_utc(acquired_at)
        artifact_id = uuid4()
        path = self.storage_path(artifact_id, filename)
        try:
            path.parent.mkdir(parents=True, exist_ok=False)
            with path.open("xb") as destination:
                destination.write(content)
        except OSError as error:
            raise DataError("Could not persist raw artifact") from error
        return RawArtifact(
            artifact_id=artifact_id,
            provider_id=provider_id,
            acquired_at=acquired_at,
            path=path,
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            size_bytes=len(content),
        )

    def store_text(
        self, content: str, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact:
        return self.store_bytes(
            content.encode("utf-8"),
            provider_id=provider_id,
            acquired_at=acquired_at,
            filename=filename,
        )

    def store_file(
        self, source: Path, *, provider_id: UUID, acquired_at: datetime, filename: str
    ) -> RawArtifact:
        try:
            content = source.read_bytes()
        except OSError as error:
            raise DataError("Could not read raw source file") from error
        return self.store_bytes(
            content,
            provider_id=provider_id,
            acquired_at=acquired_at,
            filename=filename,
        )
