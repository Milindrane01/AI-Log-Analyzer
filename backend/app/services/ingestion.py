"""Ingestion use-cases: accept a log (upload or paste), store it, queue analysis."""

import hashlib
import uuid
from pathlib import Path

import structlog
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import DomainError
from app.models import Analysis, LogFile

log = structlog.get_logger()

_CHUNK = 1024 * 1024  # 1MB read chunks — 50MB files never sit in memory whole


class FileTooLargeError(DomainError):
    status_code = 413
    code = "file_too_large"


class IngestionService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    async def ingest_upload(self, user_id: str, upload: UploadFile) -> Analysis:
        """Stream the upload to disk with size enforcement, then register it."""
        dest = self._destination(user_id, upload.filename or "upload.log")
        digest = hashlib.sha256()
        size = 0
        with open(dest, "wb") as out:
            while chunk := await upload.read(_CHUNK):
                size += len(chunk)
                if size > self._settings.max_upload_bytes:
                    out.close()
                    dest.unlink(missing_ok=True)  # never keep partial oversized files
                    raise FileTooLargeError(
                        f"File exceeds {self._settings.max_upload_bytes // (1024*1024)}MB limit"
                    )
                digest.update(chunk)
                out.write(chunk)
        if size == 0:
            dest.unlink(missing_ok=True)
            raise DomainError("Uploaded file is empty")
        return await self._register(
            user_id, upload.filename or "upload.log", dest, size, digest.hexdigest(), "upload"
        )

    async def ingest_paste(self, user_id: str, content: str, filename: str) -> Analysis:
        data = content.encode()
        if len(data) > self._settings.max_paste_bytes:
            raise FileTooLargeError(
                f"Pasted content exceeds {self._settings.max_paste_bytes // 1024}KB limit"
            )
        if not content.strip():
            raise DomainError("Pasted content is empty")
        dest = self._destination(user_id, filename)
        dest.write_bytes(data)
        return await self._register(
            user_id, filename, dest, len(data), hashlib.sha256(data).hexdigest(), "paste"
        )

    def _destination(self, user_id: str, filename: str) -> Path:
        # Never trust client filenames for paths: our own uuid names the file.
        safe_suffix = Path(filename).suffix[:16] or ".log"
        directory = Path(self._settings.upload_dir) / user_id
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{uuid.uuid4()}{safe_suffix}"

    async def _register(
        self, user_id: str, filename: str, path: Path, size: int, sha: str, source: str
    ) -> Analysis:
        log_file = LogFile(
            user_id=user_id,
            filename=filename[:255],
            storage_path=str(path),
            size_bytes=size,
            content_hash=sha,
            source=source,
        )
        self._session.add(log_file)
        await self._session.flush()
        analysis = Analysis(user_id=user_id, log_file_id=log_file.id)
        self._session.add(analysis)
        await self._session.flush()
        log.info(
            "log_ingested",
            log_file_id=log_file.id,
            analysis_id=analysis.id,
            size_bytes=size,
            source=source,
        )
        return analysis
