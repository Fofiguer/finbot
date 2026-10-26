"""API de Finbot."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


def _cargar_env(ruta: Path = Path(__file__).resolve().parent.parent / ".env") -> None:
    """Carga variables KEY=valor desde .env sin sobrescribir las ya definidas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip("\"'"))


_cargar_env()

from app.bot import responder  # noqa: E402

app = FastAPI(title="Finbot", description="Asistente de educación financiera para Chile")


class Pregunta(BaseModel):
    mensaje: str = Field(min_length=1, max_length=2000)


class Respuesta(BaseModel):
    respuesta: str
    fuente: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=Respuesta)
def chat(pregunta: Pregunta) -> dict:
    return responder(pregunta.mensaje)


PAGINA = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Finbot</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 640px; margin: 0 auto; padding: 16px; }
  #chat { border: 1px solid #ccc; border-radius: 8px; height: 60vh; overflow-y: auto; padding: 12px; }
  .msg { margin: 8px 0; padding: 8px 12px; border-radius: 8px; white-space: pre-wrap; }
  .yo { background: #e3f2fd; text-align: right; }
  .bot { background: #f1f1f1; }
  .fuente { font-size: 0.75em; color: #666; }
  form { display: flex; gap: 8px; margin-top: 12px; }
  input { flex: 1; padding: 8px; font-size: 1em; }
  button { padding: 8px 16px; font-size: 1em; }
</style>
</head>
<body>
<h1>Finbot</h1>
<p>Pregúntame por créditos, ahorro, interés compuesto o conceptos como UF, CAE o APV.</p>
<div id="chat"></div>
<form id="form">
  <input id="mensaje" autocomplete="off" placeholder="Ej.: crédito de $5.000.000 a 36 meses al 18% anual" required>
  <button>Enviar</button>
</form>
<script>
  const chat = document.getElementById("chat");
  const input = document.getElementById("mensaje");

  function agregar(texto, clase, fuente) {
    const div = document.createElement("div");
    div.className = "msg " + clase;
    div.textContent = texto;
    if (fuente) {
      const f = document.createElement("div");
      f.className = "fuente";
      f.textContent = "fuente: " + fuente;
      div.appendChild(f);
    }
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  document.getElementById("form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const mensaje = input.value.trim();
    if (!mensaje) return;
    agregar(mensaje, "yo");
    input.value = "";
    try {
      const r = await fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mensaje }),
      });
      const datos = await r.json();
      agregar(datos.respuesta ?? "Error al procesar el mensaje.", "bot", datos.fuente);
    } catch {
      agregar("No se pudo conectar con el servidor.", "bot");
    }
  });
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def inicio() -> str:
    return PAGINA
