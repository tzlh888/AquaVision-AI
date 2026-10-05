"""Synthetic HTTP/ZIP responses test safety without using public network services."""

import io
import zipfile

import pytest

from aquavision.data.download import ByteBudget, DownloadLimitError, HTTPRangeReader, RangeProtocolError, read_member, save_member


class FakeResponse:
    def __init__(self, body, status, headers):
        self.raw = io.BytesIO(body)
        self.status_code, self.headers = status, headers

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class SyntheticServer:
    def __init__(self, payload, *, status=206, wrong_range=False, truncate=False):
        self.payload, self.status = payload, status
        self.wrong_range, self.truncate = wrong_range, truncate
        self.responses = []

    def get(self, url, *, headers, **kwargs):
        a, b = map(int, headers["Range"].removeprefix("bytes=").split("-"))
        body = self.payload[a:b + 1]
        content_range = f"bytes {a}-{b}/{len(self.payload)}"
        response = FakeResponse(body[:-1] if self.truncate else body, self.status,
                                {"Content-Range": "bad" if self.wrong_range else content_range,
                                 "Content-Length": str(len(body))})
        self.responses.append(response)
        return response


def test_remote_zip_selective_decode_crc(synthetic_zip):
    server = SyntheticServer(synthetic_zip)
    budget = ByteBudget(len(synthetic_zip) * 2)
    with HTTPRangeReader("https://synthetic.invalid/archive", len(synthetic_zip), budget, session=server) as reader:
        with zipfile.ZipFile(reader) as archive:
            cyan_name = next(n for n in archive.namelist() if n.endswith("cyan.npy"))
            payload = read_member(archive, cyan_name)
            assert payload.startswith(b"\x93NUMPY")
        assert budget.used < len(synthetic_zip)  # Images were not fetched.
        assert all(r["status"] == 206 for r in reader.requests_log)


def test_server_ignoring_range_rejected_before_body_read():
    server = SyntheticServer(b"synthetic", status=200)
    reader = HTTPRangeReader("https://synthetic.invalid", 9, ByteBudget(10), session=server)
    with pytest.raises(RangeProtocolError, match="full downloads are disabled"):
        reader.read(2)
    assert server.responses[0].raw.tell() == 0


@pytest.mark.parametrize("options", [{"wrong_range": True}, {"truncate": True}])
def test_bad_partial_responses(options):
    reader = HTTPRangeReader("https://synthetic.invalid", 9, ByteBudget(10), session=SyntheticServer(b"synthetic", **options))
    with pytest.raises(RangeProtocolError):
        reader.read(2)


def test_budget_refuses_request_before_network():
    server = SyntheticServer(b"synthetic")
    reader = HTTPRangeReader("https://synthetic.invalid", 9, ByteBudget(1), session=server)
    with pytest.raises(DownloadLimitError):
        reader.read(2)
    assert not server.responses


def test_seek_and_end_of_file():
    reader = HTTPRangeReader("https://synthetic.invalid", 9, ByteBudget(20), session=SyntheticServer(b"synthetic"))
    assert reader.seek(-3, io.SEEK_END) == 6
    assert reader.read() == b"tic"
    assert reader.read() == b""
    with pytest.raises(ValueError):
        reader.seek(-1)


def test_decompression_bound(synthetic_zip):
    with zipfile.ZipFile(io.BytesIO(synthetic_zip)) as archive:
        with pytest.raises(DownloadLimitError):
            read_member(archive, archive.namelist()[0], max_bytes=100)


def test_existing_different_file_cannot_be_overwritten(tmp_path):
    path = tmp_path / "synthetic.npy"
    digest = save_member(path, b"synthetic A")
    assert save_member(path, b"synthetic A") == digest
    with pytest.raises(FileExistsError):
        save_member(path, b"synthetic B")
    assert path.read_bytes() == b"synthetic A"


def test_gzipped_catalog_is_decoded_and_validated(tmp_path, monkeypatch):
    """Regression for the real server's gzip encoding, using synthetic JSON only."""
    import gzip
    import json
    from urllib3.response import HTTPResponse
    from aquavision.data.download import fetch_record

    payload = json.dumps({"id": 14230064, "files": [{"synthetic_test": True}]}).encode()
    response = FakeResponse(b"", 200, {})
    response.raw = HTTPResponse(body=io.BytesIO(gzip.compress(payload)),
                                headers={"Content-Encoding": "gzip"}, preload_content=False)
    response.raise_for_status = lambda: None
    monkeypatch.setattr("aquavision.data.download.requests.get", lambda *args, **kwargs: response)
    path = tmp_path / "synthetic_catalog.json"
    assert fetch_record(path)["id"] == 14230064
    assert path.read_bytes() == payload


def test_catalog_decompressed_budget(tmp_path, monkeypatch):
    import gzip
    from urllib3.response import HTTPResponse
    from aquavision.data.download import fetch_record

    response = FakeResponse(b"", 200, {})
    response.raw = HTTPResponse(body=io.BytesIO(gzip.compress(b"x" * 1000)),
                                headers={"Content-Encoding": "gzip"}, preload_content=False)
    response.raise_for_status = lambda: None
    monkeypatch.setattr("aquavision.data.download.requests.get", lambda *args, **kwargs: response)
    with pytest.raises(DownloadLimitError):
        fetch_record(tmp_path / "synthetic_catalog.json", max_bytes=100)
    assert not (tmp_path / "synthetic_catalog.json").exists()


def test_member_crc_corruption_rejected():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("synthetic.npy", b"synthetic_payload_for_crc")
    payload = data.getvalue().replace(b"synthetic_payload_for_crc", b"corrupted_payload_for_crc")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        with pytest.raises(zipfile.BadZipFile):
            read_member(archive, "synthetic.npy")
