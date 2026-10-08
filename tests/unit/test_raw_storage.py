import hashlib
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from quont_sandbox.common import DataError, ValidationError
from quont_sandbox.data import RawArtifact, RawStorage
from quont_sandbox.data.infrastructure.raw import LocalRawStorage


def test_checksum_content_metadata_and_append_only_storage(tmp_path: Path) -> None:
    storage: RawStorage = LocalRawStorage(tmp_path / "raw")
    provider_id = uuid4()
    acquired_at = datetime(2024, 1, 1, tzinfo=UTC)
    first = storage.store_bytes(
        b"source", provider_id=provider_id, acquired_at=acquired_at, filename="response.json"
    )
    second = storage.store_text(
        "revision", provider_id=provider_id, acquired_at=acquired_at, filename="response.json"
    )
    assert first.path.read_bytes() == b"source"
    assert second.path.read_bytes() == b"revision"
    assert first.path != second.path
    assert first.checksum_sha256 == hashlib.sha256(b"source").hexdigest()
    assert first.provider_id == provider_id and first.size_bytes == 6
    assert first.acquired_at == acquired_at
    source = tmp_path / "input.xml"
    source.write_bytes(b"<test/>")
    imported = storage.store_file(
        source, provider_id=provider_id, acquired_at=acquired_at, filename="import.xml"
    )
    assert imported.path.read_bytes() == b"<test/>"
    with pytest.raises(DataError):
        storage.store_file(
            tmp_path / "missing",
            provider_id=provider_id,
            acquired_at=acquired_at,
            filename="missing.xml",
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        storage.store_bytes(
            b"bad", provider_id=provider_id, acquired_at=datetime(2024, 1, 1), filename="bad.json"
        )


@pytest.mark.parametrize(
    "filename",
    [
        "../escape",
        "..",
        "/absolute",
        "C:\\escape",
        "a/b",
        "a\\b",
        "file:stream",
        "NUL",
        "con.txt",
        "trailing.",
        "",
    ],
)
def test_path_traversal_and_windows_names_rejected(tmp_path: Path, filename: str) -> None:
    storage = LocalRawStorage(tmp_path)
    with pytest.raises(ValidationError):
        storage.storage_path(uuid4(), filename)


def test_artifact_metadata_requires_an_absolute_timestamp(tmp_path: Path) -> None:
    artifact_id = uuid4()
    provider_id = uuid4()
    # Validate direct metadata construction, not only the local adapter's return value.
    with pytest.raises(ValueError, match="timezone-aware"):
        RawArtifact(
            artifact_id=artifact_id,
            provider_id=provider_id,
            path=tmp_path / "artifact",
            checksum_sha256=hashlib.sha256(b"").hexdigest(),
            size_bytes=0,
            acquired_at=datetime(2024, 1, 1),
        )
    artifact = RawArtifact(
        artifact_id=artifact_id,
        provider_id=provider_id,
        path=tmp_path / "artifact",
        checksum_sha256=hashlib.sha256(b"").hexdigest(),
        size_bytes=0,
        acquired_at=datetime(2024, 1, 1, 2, tzinfo=timezone(timedelta(hours=2))),
    )
    assert artifact.acquired_at == datetime(2024, 1, 1, tzinfo=UTC)
