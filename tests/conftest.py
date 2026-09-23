import socket

import pytest


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail any test that opens a connection: the suite must run offline."""

    def refuse(*args, **kwargs):
        raise RuntimeError("tests must not touch the network")

    monkeypatch.setattr(socket.socket, "connect", refuse)
