import socket

import pytest

# A loopback port nothing listens on. GDAL's HTTP client is pointed at it as a
# proxy, so every remote read it attempts fails at once.
CLOSED_PROXY = "http://127.0.0.1:9"


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any test that opens a connection: the suite must run offline.

    Python's sockets are refused outright. GDAL, which rasterio reads COGs
    through, fetches with its own HTTP client and never touches them, so its
    requests are sent to a closed proxy instead, and a NO_PROXY in the
    environment is dropped so that nothing bypasses it.
    """

    def refuse(*args, **kwargs):
        raise RuntimeError("tests must not touch the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setenv("GDAL_HTTP_PROXY", CLOSED_PROXY)
    monkeypatch.setenv("GDAL_HTTPS_PROXY", CLOSED_PROXY)
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.delenv(name, raising=False)
