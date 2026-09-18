import logging
import re
import subprocess
import threading

log = logging.getLogger(__name__)

_URL_RE = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")


class CloudflareTunnel:
    """Runs `cloudflared tunnel --url ...` and exposes the public URL it
    prints once established. Free, no account or domain needed - the Pi only
    opens an outbound connection to Cloudflare, same principle as the
    WhatsApp bot itself. The URL changes every time this process restarts."""

    def __init__(self, local_port: int):
        self._local_port = local_port
        self.public_url: str | None = None

    def start(self):
        try:
            process = subprocess.Popen(
                ["cloudflared", "tunnel", "--url", f"http://localhost:{self._local_port}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
        except FileNotFoundError:
            log.warning("cloudflared לא מותקן - לא יהיה קישור ציבורי")
            return
        threading.Thread(target=self._watch_output, args=(process,), daemon=True).start()

    def _watch_output(self, process: subprocess.Popen):
        for line in process.stdout:
            match = _URL_RE.search(line)
            if match:
                self.public_url = match.group(0)
                log.info("מנהרת Cloudflare פעילה: %s", self.public_url)
