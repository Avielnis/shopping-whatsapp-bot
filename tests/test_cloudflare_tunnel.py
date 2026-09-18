import time

from frontends.cloudflare_tunnel import CloudflareTunnel


class FakeProcess:
    def __init__(self, lines):
        self.stdout = iter(lines)


def _wait_for(predicate, timeout=1.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_tunnel_extracts_public_url_from_cloudflared_output(monkeypatch):
    lines = [
        "some startup log line\n",
        "Your quick Tunnel has been created! Visit it at:\n",
        "https://abc-def-ghi.trycloudflare.com\n",
    ]
    monkeypatch.setattr(
        "frontends.cloudflare_tunnel.subprocess.Popen", lambda *a, **k: FakeProcess(lines)
    )
    tunnel = CloudflareTunnel(8080)
    tunnel.start()

    assert _wait_for(lambda: tunnel.public_url is not None)
    assert tunnel.public_url == "https://abc-def-ghi.trycloudflare.com"


def test_tunnel_handles_missing_cloudflared_binary(monkeypatch):
    def raise_not_found(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr("frontends.cloudflare_tunnel.subprocess.Popen", raise_not_found)
    tunnel = CloudflareTunnel(8080)
    tunnel.start()  # must not raise
    assert tunnel.public_url is None
