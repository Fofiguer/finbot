# Finbot

Asistente de educación financiera para Chile, construido con FastAPI.

## Qué hace

- **Cálculos por reglas**: cuota de un crédito (sistema francés) con total pagado e intereses,
  ahorro mensual para una meta e interés compuesto.
- **Glosario**: UF, CAE, APV, inflación y fondo mutuo.
- **Preguntas abiertas**: si defines `OPENAI_API_KEY`, las responde la API de OpenAI;
  si no, Finbot muestra una guía de uso.

## Instalación y uso

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # opcional: agrega tu OPENAI_API_KEY
uvicorn app.main:app --reload
```

Abre http://127.0.0.1:8000 para usar el chat.

## API

- `GET /health` → `{"status": "ok"}`
- `POST /chat` con `{"mensaje": "..."}` → `{"respuesta": "...", "fuente": "..."}`

`fuente` puede ser `calculo`, `glosario`, `openai` o `reglas`.

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"mensaje": "crédito de $5.000.000 a 36 meses al 18% anual"}'
```

## Ejemplos de mensajes

- «crédito de $5.000.000 a 36 meses al 1,5% mensual»
- «quiero ahorrar 2 millones en 12 meses»
- «interés compuesto de $1.000.000 al 6% por 5 años»
- «¿qué es la UF?»

Las tasas se interpretan como nominales anuales (se dividen por 12) salvo que el mensaje diga «mensual».
Los resultados son referenciales y con fines educativos.

## Pruebas

```bash
pip install -r requirements-dev.txt
python -m pytest
```

## Docker

```bash
docker build -t finbot .
docker run --rm -p 8080:8080 --env-file .env finbot
```

El contenedor escucha en `0.0.0.0` y en el puerto de la variable `PORT` (por defecto 8080),
como exige Cloud Run. En Cloud Run, define `OPENAI_API_KEY` como variable de entorno o secreto.
