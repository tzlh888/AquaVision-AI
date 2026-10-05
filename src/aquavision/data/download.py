"""Read selected ZIP members over HTTP ranges, never fall back to a full download.

ZIP central directories are metadata: reading them does not decompress images.
Python's zipfile handles ZIP64 and verifies each downloaded member's CRC32.
Archive MD5 values are recorded, but cannot be verified without the full ZIP.
"""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import requests

RECORD_ID = 14230064
RECORD_URL = f"https://zenodo.org/api/records/{RECORD_ID}"


class DownloadLimitError(RuntimeError):
    """The server or caller attempted to exceed a declared byte limit."""


class RangeProtocolError(RuntimeError):
    """The server did not return exactly the requested byte range."""


class ByteBudget:
    """Shared response-body budget across all archives in one invocation."""

    def __init__(self, limit: int):
        if limit <= 0:
            raise ValueError("Budget must be positive")
        self.limit = limit
        self.used = 0

    def reserve(self, count: int) -> None:
        if count < 0 or self.used + count > self.limit:
            raise DownloadLimitError(f"Byte budget exceeded: {self.used} + {count} > {self.limit}")
        # Reserved bytes remain charged even if a request fails.
        self.used += count


def fetch_record(destination: Path, *, max_bytes: int = 1_000_000) -> dict[str, Any]:
    """Fetch and save the version-specific catalog, with a strict response cap."""
    with requests.get(RECORD_URL, stream=True, timeout=(15, 45)) as response:
        response.raise_for_status()
        content = response.raw.read(max_bytes + 1, decode_content=True)
    if len(content) > max_bytes:
        raise DownloadLimitError("Catalog response exceeds limit")
    record = json.loads(content)
    if record.get("id") != RECORD_ID or not record.get("files"):
        raise ValueError("Unexpected Zenodo record")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return record


class HTTPRangeReader(io.RawIOBase):
    """Seekable, bounded remote reader for zipfile; no speculative read-ahead.

    Require HTTP 206, matching Content-Range and unencoded bytes before reading
    the body. An ignored Range header therefore cannot cause a huge download.
    The shared budget includes central-directory and member requests.
    """

    def __init__(self, url: str, size: int, budget: ByteBudget, *, session=None):
        super().__init__()
        if size <= 0:
            raise ValueError("Remote size must be positive")
        self.url, self.size, self.budget = url, size, budget
        self.position = 0
        self.session = session or requests.Session()
        self.owns_session = session is None
        self.requests_log: list[dict[str, Any]] = []

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END):
            raise ValueError("Invalid seek mode")
        target = offset + {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}[whence]
        if target < 0:
            raise ValueError("Cannot seek before start")
        self.position = target
        return target

    def read(self, size=-1):
        if self.closed:
            raise ValueError("Reader is closed")
        count = max(0, self.size - self.position)
        if size >= 0:
            count = min(count, size)
        if not count:
            return b""
        self.budget.reserve(count)
        start, end = self.position, self.position + count - 1
        headers = {"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"}
        with self.session.get(self.url, headers=headers, stream=True, timeout=(15, 45)) as response:
            if response.status_code != 206:
                raise RangeProtocolError(f"Expected 206, got {response.status_code}; full downloads are disabled")
            expected = f"bytes {start}-{end}/{self.size}"
            if response.headers.get("Content-Range") != expected:
                raise RangeProtocolError(f"Expected Content-Range {expected!r}")
            if response.headers.get("Content-Encoding", "identity") != "identity":
                raise RangeProtocolError("Encoded byte ranges are unsupported")
            declared = response.headers.get("Content-Length")
            if declared is not None and int(declared) != count:
                raise RangeProtocolError("Content-Length disagrees with requested range")
            body = response.raw.read(count + 1)
            if len(body) != count:
                raise RangeProtocolError("Truncated or overlong byte-range response")
        self.position += count
        self.requests_log.append({"start": start, "end": end, "bytes": count, "status": 206})
        return body

    def close(self):
        if self.owns_session:
            self.session.close()
        super().close()


def read_member(archive: zipfile.ZipFile, name: str, *, max_bytes: int = 2_000_000) -> bytes:
    """Bound decompression; never extract archive paths to the filesystem."""
    info = archive.getinfo(name)
    if info.file_size > max_bytes or info.compress_size > max_bytes:
        raise DownloadLimitError(f"Member too large: {name}")
    if info.flag_bits & 1:
        raise ValueError("Encrypted members are unsupported")
    with archive.open(info) as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) != info.file_size:
        raise ValueError(f"Member size mismatch: {name}")
    return payload


def save_member(destination: Path, payload: bytes) -> str:
    """Idempotent write; reject an existing file with different contents."""
    digest = hashlib.sha256(payload).hexdigest()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if hashlib.sha256(destination.read_bytes()).hexdigest() != digest:
            raise FileExistsError(f"Refusing to replace different data: {destination}")
    else:
        with destination.open("xb") as stream:
            stream.write(payload)
    return digest
