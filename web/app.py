"""Веб-версия. FastAPI, один файл, без шаблонов.

Полная версия с кнопками: темы, генерация, копирование, избранное (добавить /
показать / удалить), история (показать / очистить), график активности,
о программе.
"""
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from models.exceptions import ThemeNotFoundError, EmptyThemeError, GeneratorError
from storage.quote_repository import QuoteRepository
from storage.favorite_service import FavoriteService
from storage.history_service import HistoryService
from services.quote_generator import QuoteGenerator


DSN = os.getenv(
    "DATABASE_URL",
    "dbname=quote_generator user=postgres password=postgres host=localhost port=5432",
)

app = FastAPI()


@app.on_event("startup")
def startup():
    app.state.repo = QuoteRepository(DSN)
    app.state.history = HistoryService(app.state.repo.conn)
    app.state.favorites = FavoriteService(app.state.repo.conn)
    app.state.generator = QuoteGenerator(app.state.repo)
    # простой лог в памяти — последние 200 строк
    app.state.log: list[str] = []
    _log(app, "Веб-версия запущена. БД подключена.")


@app.on_event("shutdown")
def shutdown():
    app.state.repo.close()


def _log(app_obj, msg: str):
    """Пишет строку в лог с временной меткой."""
    ts = datetime.now().strftime("%H:%M:%S")
    app_obj.state.log.append(f"[{ts}] {msg}")
    # не храним больше 200 строк
    if len(app_obj.state.log) > 200:
        app_obj.state.log = app_obj.state.log[-200:]


@app.get("/api/themes")
def themes():
    return {"themes": app.state.repo.get_themes()}


@app.get("/api/quote")
def quote(theme: str):
    try:
        q = app.state.generator.generate(theme)
        app.state.history.add(q)
        _log(app, f"Сгенерирована цитата из темы «{theme}»")
        return {"id": q.id, "text": q.text, "author": q.author, "theme": q.theme}
    except ThemeNotFoundError:
        raise HTTPException(404, "Тема не найдена")
    except EmptyThemeError:
        raise HTTPException(404, "В теме нет цитат")
    except GeneratorError as e:
        raise HTTPException(500, str(e))


@app.get("/api/history")
def get_history(limit: int = 20):
    rows = app.state.history.get_recent(limit)
    return {"history": [
        {"id": r[0], "time": r[1].strftime("%Y-%m-%d %H:%M:%S"),
         "theme": r[2], "quote": r[3]}
        for r in rows
    ]}


@app.delete("/api/history")
def clear_history():
    app.state.history.clear()
    _log(app, "История очищена")
    return {"ok": True}


@app.get("/api/stats")
def stats():
    """Данные для столбчатой диаграммы: тема -> количество генераций."""
    return {"stats": app.state.history.count_by_theme()}


@app.get("/api/favorites")
def list_favorites():
    favs = app.state.favorites.get_all()
    return {"favorites": [
        {"id": q.id, "text": q.text, "author": q.author, "theme": q.theme}
        for q in favs
    ]}


@app.post("/api/favorites/{quote_id}")
def add_favorite(quote_id: int):
    try:
        q = app.state.repo.get_by_id(quote_id)
        app.state.favorites.add(q)
        _log(app, f"Цитата id={quote_id} добавлена в избранное")
        return {"ok": True}
    except GeneratorError as e:
        raise HTTPException(400, str(e))


@app.delete("/api/favorites/{quote_id}")
def remove_favorite(quote_id: int):
    try:
        app.state.favorites.remove(quote_id)
        _log(app, f"Цитата id={quote_id} удалена из избранного")
        return {"ok": True}
    except GeneratorError as e:
        raise HTTPException(400, str(e))


@app.get("/api/log")
def get_log(limit: int = 50):
    return {"log": app.state.log[-limit:]}


# ─────────── Главная HTML-страница ───────────
HTML = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<title>Генератор цитат/фактов — Вариант №10</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
* { box-sizing: border-box; }
body { font-family: Georgia, serif; max-width: 1100px; margin: 0 auto; padding: 20px;
       background: #f7f8fa; color: #1f3764; }
h1 { color: #1f3764; margin: 0 0 20px; }
nav { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
button { background: #3a7bd5; color: white; border: none; padding: 10px 16px;
         cursor: pointer; font-size: 14px; border-radius: 4px; font-family: Georgia; }
button:hover { background: #2d63ad; }
button.danger { background: #c0392b; }
button.danger:hover { background: #a93226; }
button.ghost { background: #ecf0f1; color: #1f3764; }
button.ghost:hover { background: #dde3e7; }
select { padding: 10px; font-size: 14px; font-family: Georgia; border: 1px solid #ccc;
         border-radius: 4px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.card { background: white; padding: 18px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.card h2 { margin: 0 0 12px; font-size: 18px; }
.quote { background: #f0f0f0; padding: 20px; margin: 10px 0; font-size: 18px;
         border-left: 4px solid #3a7bd5; min-height: 60px; }
.list { max-height: 260px; overflow-y: auto; }
.item { padding: 8px; border-bottom: 1px solid #eee; font-size: 13px;
        display: flex; justify-content: space-between; gap: 8px; }
.item .txt { flex: 1; }
.item .del { background: #c0392b; padding: 2px 8px; cursor: pointer;
             border: none; color: white; border-radius: 3px; font-size: 11px; }
.log { font-family: Consolas, monospace; font-size: 12px; background: #1f3764;
       color: #d4e4ff; padding: 12px; border-radius: 4px; max-height: 180px; overflow-y: auto; }
.log div { padding: 2px 0; }
canvas { max-height: 240px; }
.muted { color: #888; font-size: 12px; }
</style></head>
<body>

<h1>Генератор цитат/фактов</h1>

<nav>
  <button onclick="gen()">Сгенерировать</button>
  <button onclick="copyQuote()" class="ghost">Копировать</button>
  <button onclick="fav()" class="ghost">В избранное</button>
  <button onclick="loadFavs()" class="ghost">Показать избранное</button>
  <button onclick="clearHistory()" class="danger">Очистить историю</button>
  <button onclick="about()" class="ghost">О программе</button>
</nav>

<div class="grid">

  <div class="card">
    <h2>Тема</h2>
    <select id="theme" style="width:100%"></select>
    <div class="quote" id="q">Нажмите «Сгенерировать»</div>
  </div>

  <div class="card">
    <h2>График активности по темам</h2>
    <canvas id="chart"></canvas>
  </div>

  <div class="card">
    <h2>История генераций</h2>
    <div class="list" id="h"></div>
  </div>

  <div class="card">
    <h2>Избранное</h2>
    <div class="list" id="fav"><div class="muted">Пусто. Сгенерируйте цитату и нажмите «В избранное».</div></div>
  </div>

  <div class="card" style="grid-column: 1 / -1">
    <h2>Лог</h2>
    <div class="log" id="log"></div>
  </div>

</div>

<script>
let currentQuoteId = null;
let chart = null;

async function loadThemes() {
    const r = await fetch('/api/themes');
    const d = await r.json();
    const sel = document.getElementById('theme');
    d.themes.forEach(t => {
        const o = document.createElement('option');
        o.value = t; o.textContent = t;
        sel.appendChild(o);
    });
}

async function gen() {
    const theme = document.getElementById('theme').value;
    if (!theme) { alert('Выберите тему'); return; }
    const r = await fetch('/api/quote?theme=' + encodeURIComponent(theme));
    if (!r.ok) { const e = await r.json(); alert(e.detail || 'Ошибка'); return; }
    const q = await r.json();
    currentQuoteId = q.id;
    document.getElementById('q').innerHTML =
        '«' + q.text + '»' + (q.author ? '<br>— ' + q.author : '');
    loadHistory(); loadStats(); loadLog();
}

async function copyQuote() {
    if (!currentQuoteId) { alert('Сначала сгенерируйте цитату'); return; }
    const text = document.getElementById('q').innerText;
    try {
        await navigator.clipboard.writeText(text);
        alert('Скопировано в буфер обмена');
    } catch (e) {
        alert('Не удалось скопировать: ' + e);
    }
}

async function fav() {
    if (!currentQuoteId) { alert('Сначала сгенерируйте цитату'); return; }
    const r = await fetch('/api/favorites/' + currentQuoteId, {method: 'POST'});
    if (!r.ok) { const e = await r.json(); alert(e.detail || 'Ошибка'); return; }
    alert('Добавлено в избранное');
    loadFavs(); loadLog();
}

async function loadFavs() {
    const r = await fetch('/api/favorites');
    const d = await r.json();
    const box = document.getElementById('fav');
    if (d.favorites.length === 0) {
        box.innerHTML = '<div class="muted">Пусто.</div>';
        return;
    }
    box.innerHTML = d.favorites.map(f =>
        '<div class="item"><span class="txt">«' + f.text + '»'
        + (f.author ? ' — ' + f.author : '')
        + ' <span class="muted">[' + f.theme + ']</span></span>'
        + '<button class="del" onclick="rmFav(' + f.id + ')">x</button></div>'
    ).join('');
}

async function rmFav(id) {
    const r = await fetch('/api/favorites/' + id, {method: 'DELETE'});
    if (!r.ok) { const e = await r.json(); alert(e.detail || 'Ошибка'); return; }
    loadFavs(); loadLog();
}

async function loadHistory() {
    const r = await fetch('/api/history');
    const d = await r.json();
    document.getElementById('h').innerHTML = d.history.map(
        h => '<div class="item"><span class="txt"><span class="muted">['
             + h.time + ']</span> <b>' + h.theme + '</b>: «' + h.quote + '»</span></div>'
    ).join('');
}

async function clearHistory() {
    if (!confirm('Точно очистить всю историю?')) return;
    await fetch('/api/history', {method: 'DELETE'});
    loadHistory(); loadStats(); loadLog();
}

async function loadStats() {
    const r = await fetch('/api/stats');
    const d = await r.json();
    const labels = Object.keys(d.stats);
    const data = Object.values(d.stats);
    if (chart) chart.destroy();
    chart = new Chart(document.getElementById('chart'), {
        type: 'bar',
        data: { labels: labels,
                datasets: [{ label: 'Генераций', data: data,
                              backgroundColor: '#3a7bd5' }] },
        options: { responsive: true, maintainAspectRatio: false,
                   plugins: { legend: { display: false } },
                   scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
    });
}

async function loadLog() {
    const r = await fetch('/api/log');
    const d = await r.json();
    document.getElementById('log').innerHTML =
        d.log.map(l => '<div>' + l + '</div>').join('');
    const box = document.getElementById('log');
    box.scrollTop = box.scrollHeight;
}

function about() {
    alert('Генератор цитат/фактов\\nВариант №10\\nЛабораторная работа №3');
}

// запуск
loadThemes();
loadHistory();
loadStats();
loadFavs();
loadLog();
// периодическое обновление лога (на случай если параллельно кто-то генерит)
setInterval(loadLog, 5000);
</script>

</body></html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML)