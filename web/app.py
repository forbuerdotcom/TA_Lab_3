import os
import random

from fastapi import FastAPI, HTTPException
import psycopg2

from models.quote import Quote
from models.exceptions import ThemeNotFoundError, EmptyThemeError, GeneratorError
from storage.quote_repository import QuoteRepository
from storage.history_service import HistoryService
from services.quote_generator import QuoteGenerator
from fastapi.responses import HTMLResponse


DSN = os.getenv(
    "DATABASE_URL",
    "dbname=quote_generator user=postgres password=postgres host=localhost port=5432",
)

app = FastAPI()


@app.on_event("startup")
def startup():
    app.state.repo = QuoteRepository(DSN)
    app.state.history = HistoryService(app.state.repo.conn)
    app.state.generator = QuoteGenerator(app.state.repo)


@app.on_event("shutdown")
def shutdown():
    app.state.repo.close()


HTML = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8">
<title>Генератор цитат</title>
<style>
body { font-family: Georgia; max-width: 700px; margin: 30px auto; padding: 20px; }
h1 { color: #1f3764; }
.quote { background: #f0f0f0; padding: 20px; margin: 10px 0; font-size: 18px; }
.history { background: white; padding: 10px; border: 1px solid #ccc; max-height: 200px; overflow-y: auto; }
.item { padding: 5px; border-bottom: 1px solid #eee; font-size: 13px; }
button { background: #3a7bd5; color: white; border: none; padding: 10px; cursor: pointer; font-size: 14px; }
select { padding: 10px; font-size: 14px; }
</style></head>
<body>
<h1>Генератор цитат/фактов</h1>

<label>Тема:</label>
<select id="theme"></select>
<button onclick="gen()">Сгенерировать</button>

<div class="quote" id="q">Нажмите «Сгенерировать»</div>

<h3>История:</h3>
<div class="history" id="h"></div>

<script>
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
    const r = await fetch('/api/quote?theme=' + encodeURIComponent(theme));
    if (!r.ok) { alert('Ошибка'); return; }
    const q = await r.json();
    document.getElementById('q').innerHTML = '«' + q.text + '»' + (q.author ? '<br>— ' + q.author : '');
    loadHistory();
}
async function loadHistory() {
    const r = await fetch('/api/history');
    const d = await r.json();
    document.getElementById('h').innerHTML = d.history.map(
        h => '<div class="item">[' + h.time + '] ' + h.theme + ': «' + h.quote + '»</div>'
    ).join('');
}
loadThemes();
loadHistory();
</script>
</body></html>"""




@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(content=HTML)


@app.get("/api/themes")
def themes():
    return {"themes": app.state.repo.get_themes()}


@app.get("/api/quote")
def quote(theme: str):
    try:
        q = app.state.generator.generate(theme)
        app.state.history.add(q)
        return {"id": q.id, "text": q.text, "author": q.author, "theme": q.theme}
    except ThemeNotFoundError:
        raise HTTPException(404, "Тема не найдена")
    except EmptyThemeError:
        raise HTTPException(404, "В теме нет цитат")
    except GeneratorError as e:
        raise HTTPException(500, str(e))


@app.get("/api/history")
def history(limit: int = 20):
    rows = app.state.history.get_recent(limit)
    return {"history": [
        {"id": r[0], "time": r[1].strftime("%Y-%m-%d %H:%M:%S"), "theme": r[2], "quote": r[3]}
        for r in rows
    ]}