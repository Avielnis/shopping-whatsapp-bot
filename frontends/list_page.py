import logging
import re
import time

from flask import Flask, jsonify, render_template_string, request

from core.emoji_lookup import emoji_for
from core.shopping_list import ShoppingListService

log = logging.getLogger(__name__)

_SPLIT_RE = re.compile(r"[,\s]+")

_PAGE = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>רשימת קניות</title>
<style>
  :root {
    --bg: #0b0f17; --card: #141b28; --row: #1a2233; --border: #232c3f;
    --text: #f1f5f9; --muted: #7c8aa5; --accent: #22c55e;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
    min-height: 100vh; padding-bottom: 5.5rem;
  }
  header { padding: 1.25rem 1rem .75rem; }
  h1 { margin: 0 0 .3rem; font-size: 1.3rem; }
  #summary { color: var(--muted); font-size: .85rem; }
  #progress-track { height: 6px; background: var(--row); border-radius: 999px; margin-top: .8rem; overflow: hidden; }
  #progress-fill { height: 100%; background: var(--accent); width: 0%; transition: width .3s ease; }

  #empty { text-align: center; color: var(--muted); padding: 3rem 1rem; font-size: .95rem; }

  .section-label { padding: 1rem 1rem .4rem; font-size: .75rem; color: var(--muted); }
  ul { list-style: none; margin: 0; padding: 0 .75rem; }
  li {
    display: flex; align-items: center; gap: .75rem; background: var(--row);
    border-radius: 12px; padding: .8rem .9rem; margin-bottom: .5rem;
    transition: opacity .25s ease, transform .25s ease;
  }
  li.collected { opacity: .55; }
  li.collected .name { text-decoration: line-through; color: var(--muted); }
  .check {
    width: 1.4rem; height: 1.4rem; border-radius: 50%; border: 2px solid var(--muted);
    background: transparent; flex: none; cursor: pointer; display: flex;
    align-items: center; justify-content: center; color: var(--bg); font-size: .85rem;
  }
  li.collected .check { background: var(--accent); border-color: var(--accent); }
  .name { flex: 1; font-size: 1rem; }
  .emoji { font-size: 1.3rem; flex: none; }

  #add-bar {
    position: fixed; bottom: 0; inset-inline: 0; display: flex; gap: .5rem;
    padding: .75rem; background: var(--card); border-top: 1px solid var(--border);
  }
  #add-input {
    flex: 1; padding: .8rem 1rem; border-radius: 999px; border: 1px solid var(--border);
    background: var(--row); color: var(--text); font-size: 1rem; outline: none;
  }
  #add-input:focus { border-color: var(--accent); }
  #add-btn {
    width: 3rem; border: none; border-radius: 999px; background: var(--accent);
    color: #06280f; font-size: 1.4rem; font-weight: 700; cursor: pointer;
  }
</style>
</head>
<body>
  <header>
    <h1>🛒 רשימת קניות</h1>
    <div id="summary"></div>
    <div id="progress-track"><div id="progress-fill"></div></div>
  </header>

  <div id="empty" hidden>הרשימה ריקה 🎉</div>
  <ul id="pending-list"></ul>
  <div class="section-label" id="collected-label" hidden>נאספו</div>
  <ul id="collected-list"></ul>

  <form id="add-bar">
    <input id="add-input" type="text" placeholder="הוספת מוצר..." autocomplete="off">
    <button id="add-btn" type="submit">+</button>
  </form>

<script>
function rowHtml(item, collected) {
  return `<li class="${collected ? 'collected' : ''}" data-name="${item.name}">
    <button class="check" aria-label="סמן">${collected ? '✓' : ''}</button>
    <span class="name">${item.name}</span>
    <span class="emoji">${item.emoji}</span>
  </li>`;
}

function render(data) {
  const pendingEl = document.getElementById('pending-list');
  const collectedEl = document.getElementById('collected-list');
  const collectedLabel = document.getElementById('collected-label');
  const empty = document.getElementById('empty');

  pendingEl.innerHTML = data.pending.map(i => rowHtml(i, false)).join('');
  collectedEl.innerHTML = data.collected.map(i => rowHtml(i, true)).join('');
  collectedLabel.hidden = data.collected.length === 0;
  empty.hidden = data.pending.length + data.collected.length > 0;

  const total = data.pending.length + data.collected.length;
  document.getElementById('summary').textContent =
    total === 0 ? '' : `${data.pending.length} נותרו מתוך ${total}`;
  document.getElementById('progress-fill').style.width =
    total === 0 ? '0%' : `${(data.collected.length / total) * 100}%`;

  document.querySelectorAll('.check').forEach(btn => {
    btn.addEventListener('click', onToggle);
  });
}

async function fetchData() {
  const res = await fetch('/data');
  return res.json();
}

async function refresh() {
  render(await fetchData());
}

function onToggle(e) {
  const li = e.currentTarget.closest('li');
  const name = li.dataset.name;
  const nowCollected = !li.classList.contains('collected');

  // optimistic UI: move the row immediately, sync with the server after
  li.classList.toggle('collected', nowCollected);
  const target = nowCollected ? document.getElementById('collected-list') : document.getElementById('pending-list');
  target.appendChild(li);
  document.getElementById('collected-label').hidden = document.getElementById('collected-list').children.length === 0;
  e.currentTarget.textContent = nowCollected ? '✓' : '';

  const body = new URLSearchParams({ name });
  if (nowCollected) body.set('checked', 'on');
  fetch('/toggle', { method: 'POST', body }).then(refresh);
}

document.getElementById('add-bar').addEventListener('submit', async (e) => {
  e.preventDefault();
  const input = document.getElementById('add-input');
  if (!input.value.trim()) return;
  await fetch('/add', { method: 'POST', body: new URLSearchParams({ text: input.value }) });
  input.value = '';
  refresh();
});

refresh();
setInterval(refresh, 3000);
</script>
</body>
</html>
"""


def create_list_page_app(service: ShoppingListService) -> Flask:
    app = Flask(__name__)

    def _data():
        pending, collected = service.get_list()
        return {
            "pending": [{"name": name, "emoji": emoji_for(name)} for name in pending],
            "collected": [{"name": name, "emoji": emoji_for(name)} for name in collected],
        }

    @app.get("/")
    def page():
        return render_template_string(_PAGE)

    @app.get("/data")
    def data():
        return jsonify(_data())

    @app.post("/toggle")
    def toggle():
        name = request.form.get("name", "")
        if name:
            if "checked" in request.form:
                service.mark_collected([name])
            else:
                service.unmark([name])
        return jsonify(ok=True)

    @app.post("/add")
    def add():
        items = [item for item in _SPLIT_RE.split(request.form.get("text", "").strip()) if item]
        if items:
            service.add_items(items)
        return jsonify(ok=True)

    return app


def run_list_page_server(app: Flask, host: str = "0.0.0.0", port: int = 8081, retries: int = 5):
    for attempt in range(1, retries + 1):
        try:
            app.run(host=host, port=port)
            return
        except SystemExit:
            log.warning(
                "דף הרשימה נכשל בהאזנה ל-%s:%s (ניסיון %d/%d), מנסה שוב בעוד 2 שניות",
                host, port, attempt, retries,
            )
            time.sleep(2)
    log.error("דף הרשימה לא הצליח להאזין ל-%s:%s אחרי %d ניסיונות", host, port, retries)
