import logging
import re
import subprocess
import threading

from dotenv import set_key
from flask import Flask, jsonify, redirect, render_template_string, request

from config import Config
from core.emoji_lookup import label as with_emoji
from core.shopping_list import ShoppingListService
from frontends.whatsapp_client import WhatsAppClient

log = logging.getLogger(__name__)

_LOG_FILE = "bot.log"
_LOG_TAIL_LINES = 200
_SPLIT_RE = re.compile(r"[,\s]+")

_PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Shopping Bot Admin</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 2rem 1rem; min-height: 100vh;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    font-family: -apple-system, Segoe UI, Roboto, sans-serif;
    display: flex; justify-content: center;
  }
  .card {
    width: 100%; max-width: 560px; background: #ffffff; border-radius: 16px;
    padding: 1.75rem; box-shadow: 0 20px 60px rgba(0,0,0,.35); margin-bottom: 1.5rem;
  }
  h1 { font-size: 1.35rem; margin: 0 0 1.25rem; color: #0f172a; }
  h2 { font-size: 1rem; margin: 0 0 1rem; color: #0f172a; }
  .status-row { display: flex; gap: .6rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
  .badge {
    flex: 1; min-width: 140px; padding: .75rem 1rem; border-radius: 10px;
    background: #f1f5f9; font-size: .85rem; color: #475569;
  }
  .badge b { display: block; font-size: 1.1rem; color: #0f172a; }
  .badge.ok b { color: #16a34a; }
  .badge.warn b { color: #d97706; }
  label { display: block; font-size: .8rem; font-weight: 600; color: #334155; margin: 1rem 0 .3rem; }
  input[type=text], input[type=number] {
    width: 100%; padding: .6rem .7rem; border: 1px solid #cbd5e1; border-radius: 8px;
    font-size: .9rem; font-family: inherit;
  }
  input:focus { outline: 2px solid #6366f1; border-color: transparent; }
  button {
    margin-top: 1.5rem; width: 100%; padding: .8rem; border: none; border-radius: 10px;
    background: #4f46e5; color: white; font-size: .95rem; font-weight: 600; cursor: pointer;
  }
  button:hover { background: #4338ca; }
  button:disabled { background: #94a3b8; cursor: default; }
  .hint { font-size: .75rem; color: #64748b; margin-top: .3rem; }
  #banner {
    display: none; margin-top: 1rem; padding: .75rem 1rem; border-radius: 10px;
    background: #fef3c7; color: #92400e; font-size: .85rem;
  }

  .add-row { display: flex; gap: .5rem; margin: 0 0 1rem; }
  .add-row input { margin: 0; }
  .add-row button { margin: 0; width: auto; padding: .6rem 1.1rem; }
  .empty-hint { color: #94a3b8; font-size: .9rem; text-align: center; padding: 1rem 0; }
  .item-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: .55rem 0; border-bottom: 1px solid #f1f5f9; gap: .5rem;
  }
  .item-row form:first-child { flex: 1; }
  .item-row label { margin: 0; font-weight: 400; font-size: .95rem; color: #1e293b; display: flex; align-items: center; gap: .55rem; }
  .item-row input[type=checkbox] { width: 1.1rem; height: 1.1rem; accent-color: #4f46e5; }
  .item-row.collected label { color: #94a3b8; text-decoration: line-through; }
  .icon-btn {
    margin: 0; width: 2rem; height: 2rem; padding: 0; border-radius: 8px;
    background: transparent; color: #cbd5e1; font-size: 1rem;
  }
  .icon-btn:hover { background: #fee2e2; color: #dc2626; }
  .divider { border-top: 1px dashed #e2e8f0; margin: .3rem 0; }
  .clear-row { margin-top: 1rem; }
  .clear-row button { background: transparent; color: #dc2626; font-weight: 500; font-size: .8rem; padding: .3rem; width: auto; margin: 0; }
  .clear-row button:hover { background: #fef2f2; }

  #logs {
    margin: 0; max-height: 260px; overflow-y: auto; background: #0f172a; color: #cbd5e1;
    padding: .9rem; border-radius: 10px; font-family: ui-monospace, Consolas, monospace;
    font-size: .72rem; white-space: pre-wrap; overflow-wrap: anywhere; direction: ltr;
  }
</style>
</head>
<body>
  <div class="card">
    <h1>🛒 Shopping List Bot — Admin</h1>

    <div class="status-row">
      <div class="badge {{ 'ok' if connected else 'warn' }}">
        WhatsApp<b>{{ 'Connected' if connected else 'Waiting' }}</b>
      </div>
      <div class="badge">Pending<b>{{ pending_count }}</b></div>
      <div class="badge">Collected<b>{{ collected_count }}</b></div>
    </div>

    <h2>Shopping list</h2>
    <form method="post" action="/whatsapp/list/add" class="add-row">
      <input type="text" name="text" placeholder="Add item(s), comma/space/newline separated" autocomplete="off">
      <button type="submit">Add</button>
    </form>

    {% if not pending_items and not collected_items %}
    <p class="empty-hint">List is empty 🎉</p>
    {% endif %}

    {% for item in pending_items %}
    <div class="item-row">
      <form method="post" action="/whatsapp/list/toggle">
        <input type="hidden" name="name" value="{{ item.name }}">
        <label><input type="checkbox" name="checked" onchange="this.form.submit()"> {{ item.label }}</label>
      </form>
      <form method="post" action="/whatsapp/list/remove">
        <input type="hidden" name="name" value="{{ item.name }}">
        <button type="submit" class="icon-btn" title="Delete">✕</button>
      </form>
    </div>
    {% endfor %}

    {% if collected_items %}<div class="divider"></div>{% endif %}

    {% for item in collected_items %}
    <div class="item-row collected">
      <form method="post" action="/whatsapp/list/toggle">
        <input type="hidden" name="name" value="{{ item.name }}">
        <label><input type="checkbox" name="checked" checked onchange="this.form.submit()"> {{ item.label }}</label>
      </form>
      <form method="post" action="/whatsapp/list/remove">
        <input type="hidden" name="name" value="{{ item.name }}">
        <button type="submit" class="icon-btn" title="Delete">✕</button>
      </form>
    </div>
    {% endfor %}

    {% if pending_items or collected_items %}
    <form method="post" action="/whatsapp/list/clear" class="clear-row"
          onsubmit="return confirm('Clear the entire list?')">
      <button type="submit">Clear entire list</button>
    </form>
    {% endif %}
  </div>

  <div class="card">
    <h2>Configuration</h2>
    <form id="config-form">
      <label for="ALLOWED_CHAT_JID">Allowed chat JID</label>
      <input type="text" id="ALLOWED_CHAT_JID" name="ALLOWED_CHAT_JID"
             value="{{ allowed_chat_jid }}" list="seen-chats" autocomplete="off">
      <datalist id="seen-chats">
        {% for jid, seen_at in seen_chats.items() %}
        <option value="{{ jid }}">last seen {{ seen_at }}</option>
        {% endfor %}
      </datalist>
      <div class="hint">Pick a recently-seen chat, or paste a JID directly.</div>

      <label for="DB_PATH">Database path</label>
      <input type="text" id="DB_PATH" name="DB_PATH" value="{{ db_path }}">

      <label for="SESSION_PATH">WhatsApp session path</label>
      <input type="text" id="SESSION_PATH" name="SESSION_PATH" value="{{ session_path }}">

      <label for="ADMIN_PORT">Admin page port</label>
      <input type="number" id="ADMIN_PORT" name="ADMIN_PORT" value="{{ admin_port }}">

      <button type="submit">Save &amp; restart Raspberry Pi</button>
      <div id="banner"></div>
    </form>
  </div>

  <div class="card">
    <h2>Logs</h2>
    <pre id="logs">{{ initial_logs }}</pre>
  </div>

<script>
document.getElementById('config-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!confirm('Changes only take effect after restarting the Raspberry Pi. Save and restart now?')) {
    return;
  }
  const banner = document.getElementById('banner');
  const button = e.target.querySelector('button');
  button.disabled = true;
  banner.style.display = 'block';
  banner.textContent = 'Saving and restarting the Raspberry Pi… this page will stop responding shortly.';
  await fetch('/whatsapp/save', { method: 'POST', body: new FormData(e.target) });
});

const logsEl = document.getElementById('logs');
logsEl.scrollTop = logsEl.scrollHeight;
setInterval(async () => {
  const atBottom = logsEl.scrollTop + logsEl.clientHeight >= logsEl.scrollHeight - 10;
  try {
    const res = await fetch('/whatsapp/logs');
    const data = await res.json();
    logsEl.textContent = data.logs;
    if (atBottom) logsEl.scrollTop = logsEl.scrollHeight;
  } catch (e) { /* ignore transient network errors */ }
}, 4000);
</script>
</body>
</html>
"""


def _read_log_tail() -> str:
    try:
        with open(_LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return "No logs yet."
    return "".join(lines[-_LOG_TAIL_LINES:])


def create_admin_app(
    config: Config, whatsapp_client: WhatsAppClient, service: ShoppingListService, env_path: str = ".env"
) -> Flask:
    app = Flask(__name__)

    @app.get("/whatsapp")
    def dashboard():
        pending, collected = service.get_list()
        return render_template_string(
            _PAGE,
            connected=whatsapp_client.is_connected,
            pending_count=len(pending),
            collected_count=len(collected),
            pending_items=[{"name": name, "label": with_emoji(name)} for name in pending],
            collected_items=[{"name": name, "label": with_emoji(name)} for name in collected],
            allowed_chat_jid=whatsapp_client.allowed_chat_jid,
            db_path=config.db_path,
            session_path=config.session_path,
            admin_port=config.admin_port,
            seen_chats=whatsapp_client.seen_chats,
            initial_logs=_read_log_tail(),
        )

    @app.get("/whatsapp/logs")
    def logs():
        return jsonify(logs=_read_log_tail())

    @app.post("/whatsapp/list/add")
    def list_add():
        items = [item for item in _SPLIT_RE.split(request.form.get("text", "").strip()) if item]
        if items:
            service.add_items(items)
        return redirect("/whatsapp")

    @app.post("/whatsapp/list/toggle")
    def list_toggle():
        name = request.form.get("name", "")
        if name:
            if "checked" in request.form:
                service.mark_collected([name])
            else:
                service.unmark([name])
        return redirect("/whatsapp")

    @app.post("/whatsapp/list/remove")
    def list_remove():
        name = request.form.get("name", "")
        if name:
            service.remove_items([name])
        return redirect("/whatsapp")

    @app.post("/whatsapp/list/clear")
    def list_clear():
        service.clear_all()
        return redirect("/whatsapp")

    @app.post("/whatsapp/save")
    def save():
        for key in ("ALLOWED_CHAT_JID", "DB_PATH", "SESSION_PATH", "ADMIN_PORT"):
            set_key(env_path, key, request.form.get(key, ""))
        log.info("הגדרות עודכנו מדף הניהול, מפעיל מחדש את הראזפברי פיי")
        threading.Timer(1.5, _reboot).start()
        return jsonify(ok=True)

    return app


def _reboot():
    subprocess.run(["sudo", "reboot"])


def run_admin_server(app: Flask, host: str = "0.0.0.0", port: int = 80):
    app.run(host=host, port=port)
