import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def sin_openai(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def chat(mensaje):
    respuesta = client.post("/chat", json={"mensaje": mensaje})
    assert respuesta.status_code == 200
    return respuesta.json()


def test_health():
    respuesta = client.get("/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


def test_cuota_credito():
    datos = chat("crédito de $10.000.000 a 36 meses al 12% anual")
    assert datos["fuente"] == "calculo"
    assert "$332.143" in datos["respuesta"]


def test_meta_de_ahorro():
    datos = chat("quiero ahorrar 2 millones en 10 meses")
    assert datos["fuente"] == "calculo"
    assert "$200.000" in datos["respuesta"]


def test_glosario():
    datos = chat("¿Qué es la UF?")
    assert datos["fuente"] == "glosario"
    assert "Unidad de Fomento" in datos["respuesta"]


@pytest.mark.parametrize("cuerpo", [{"mensaje": ""}, {}])
def test_entrada_vacia_es_rechazada(cuerpo):
    assert client.post("/chat", json=cuerpo).status_code == 422
