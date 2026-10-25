import functools
import http.server
import socket
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest
import rasterio
from rasterio.errors import RasterioIOError

from satreg.ingest import GDAL_HTTP_OPTIONS

DATA = Path(__file__).parent / "data"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def served_fixture() -> Iterator[str]:
    """Serve the committed Beauce fixture over HTTP on the loopback interface."""
    handler = functools.partial(QuietHandler, directory=str(DATA))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/beauce_b04_320.tif"
    server.shutdown()
    server.server_close()


def test_python_connections_are_refused() -> None:
    with pytest.raises(RuntimeError, match="must not touch the network"):
        socket.create_connection(("127.0.0.1", 9))


def test_gdal_http_reads_are_refused(served_fixture: str) -> None:
    # GDAL fetches with its own HTTP client, which never goes through Python's
    # sockets: without the guard this read succeeds. The options are the ones
    # the chips are fetched with.
    with (
        pytest.raises(RasterioIOError),
        rasterio.Env(**GDAL_HTTP_OPTIONS),
        rasterio.open(served_fixture) as src,
    ):
        src.read(1)
