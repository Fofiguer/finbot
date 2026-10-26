"""Lógica conversacional de Finbot: reglas para cálculos, glosario y OpenAI como respaldo."""

import json
import os
import re
import unicodedata
import urllib.request

from app import finanzas

GLOSARIO = {
    "uf": (
        r"\buf\b",
        "La UF (Unidad de Fomento) es una unidad de cuenta reajustable según la inflación (IPC). "
        "El Banco Central de Chile publica su valor diario en pesos. Se usa en créditos "
        "hipotecarios, arriendos y seguros para que los montos mantengan su poder adquisitivo.",
    ),
    "cae": (
        r"\bcae\b",
        "La CAE (Carga Anual Equivalente) es un porcentaje que resume el costo total de un crédito "
        "en base anual: intereses, comisiones, seguros y gastos asociados. Las instituciones deben "
        "informarla, y sirve para comparar créditos: a menor CAE, más barato el crédito. "
        "(Ojo: en educación superior, CAE también es el Crédito con Aval del Estado).",
    ),
    "apv": (
        r"\bapv\b",
        "El APV (Ahorro Previsional Voluntario) es ahorro adicional a tu cotización obligatoria "
        "para mejorar tu pensión. Tiene beneficios tributarios: en el Régimen A el Estado bonifica "
        "un 15% de lo ahorrado (con tope anual de 6 UTM); en el Régimen B el aporte se descuenta "
        "de tu base imponible, lo que conviene más a quienes pagan más impuesto.",
    ),
    "inflacion": (
        r"inflacion",
        "La inflación es el alza sostenida y generalizada de los precios, que reduce el poder de "
        "compra del dinero. En Chile se mide con el IPC que publica el INE, y el Banco Central "
        "tiene como meta una inflación de 3% anual (dentro de un rango de 2% a 4%).",
    ),
    "fondo mutuo": (
        r"fondos? mutuos?",
        "Un fondo mutuo reúne el dinero de muchas personas para invertirlo en instrumentos como "
        "depósitos, bonos o acciones. Lo administra una AGF fiscalizada por la CMF, y cada "
        "inversionista posee cuotas cuyo valor varía. La rentabilidad no está garantizada: "
        "el riesgo depende del tipo de fondo.",
    ),
}

INTENCIONES = {
    "credito": r"\b(credito|prestamo|cuota|hipotecari\w*|financiar)",
    "interes_compuesto": r"(interes compuesto|invertir|inversion|rentabilidad|deposito a plazo)",
    "ahorro": r"\b(ahorr\w*|juntar|meta)\b",
}

AYUDA = (
    "Puedo ayudarte con:\n"
    "• Cuota de un crédito: «crédito de $5.000.000 a 36 meses al 18% anual»\n"
    "• Ahorro para una meta: «quiero ahorrar $2.000.000 en 12 meses»\n"
    "• Interés compuesto: «interés compuesto de $1.000.000 al 6% por 5 años»\n"
    "• Conceptos: UF, CAE, APV, inflación y fondo mutuo."
)

NOTA = "Cálculo referencial con fines educativos."

PROMPT_SISTEMA = (
    "Eres Finbot, un asistente de educación financiera para personas en Chile. Responde en "
    "español, de forma breve, clara y neutral. Usa conceptos y entidades chilenas cuando "
    "corresponda (UF, CMF, SERNAC, AFP). No des asesoría de inversión personalizada ni "
    "recomiendes productos específicos."
)


def _normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def _numero(texto: str) -> float:
    """Convierte '5.000.000' o '1,5' a float."""
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):
        return float(texto.replace(".", ""))
    return float(texto.replace(",", "."))


def _extraer_datos(texto: str) -> dict:
    """Extrae tasa, plazo (en meses) y monto de un texto normalizado."""
    datos = {}

    tasa = re.search(r"(\d+(?:[.,]\d+)?)\s*%", texto)
    if tasa:
        datos["tasa"] = _numero(tasa.group(1)) / 100
        datos["tasa_mensual"] = "mensual" in texto
        texto = texto.replace(tasa.group(0), " ")

    plazo = re.search(r"(\d+(?:[.,]\d+)?)\s*(meses|mes|anos|ano)\b", texto)
    if plazo:
        cantidad = _numero(plazo.group(1))
        datos["meses"] = round(cantidad * 12 if plazo.group(2).startswith("ano") else cantidad)
        texto = texto.replace(plazo.group(0), " ")

    montos = []
    patron = r"(\d{1,3}(?:\.\d{3})+|\d+(?:[.,]\d+)?)\s*(millones|millon|mil|lucas)?\b"
    for numero, sufijo in re.findall(patron, texto):
        multiplicador = {"millones": 1e6, "millon": 1e6, "mil": 1e3, "lucas": 1e3}.get(sufijo, 1)
        montos.append(_numero(numero) * multiplicador)
    if montos:
        datos["monto"] = max(montos)

    return datos


def _clp(valor: float) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def _pct(tasa: float) -> str:
    return f"{tasa * 100:.2f}%".replace(".", ",")


def _tasa_mensual(datos: dict) -> float:
    tasa = datos.get("tasa", 0.0)
    return tasa if datos.get("tasa_mensual") else finanzas.tasa_anual_a_mensual(tasa)


def _calcular(intencion: str, datos: dict) -> str | None:
    """Devuelve la respuesta del cálculo, o None si faltan datos."""
    monto, meses = datos.get("monto"), datos.get("meses")

    if intencion == "credito":
        if not (monto and meses and "tasa" in datos):
            return None
        tasa = _tasa_mensual(datos)
        cuota = finanzas.cuota_mensual(monto, tasa, meses)
        total, intereses = finanzas.total_pagado_e_intereses(monto, tasa, meses)
        return (
            f"Para un crédito de {_clp(monto)} a {meses} meses (tasa mensual {_pct(tasa)}), "
            f"la cuota fija es {_clp(cuota)}. Pagarías {_clp(total)} en total, de los cuales "
            f"{_clp(intereses)} son intereses. {NOTA} No incluye seguros ni comisiones: "
            "compara siempre la CAE."
        )

    if intencion == "ahorro":
        if not (monto and meses):
            return None
        tasa = _tasa_mensual(datos)
        cuota = finanzas.ahorro_mensual_para_meta(monto, meses, tasa)
        extra = f" con una rentabilidad mensual de {_pct(tasa)}" if tasa else " sin rentabilidad"
        return (
            f"Para juntar {_clp(monto)} en {meses} meses{extra}, necesitas ahorrar "
            f"{_clp(cuota)} al mes. {NOTA}"
        )

    if intencion == "interes_compuesto":
        if not (monto and meses and "tasa" in datos):
            return None
        tasa = datos["tasa"]
        tasa_anual = (1 + tasa) ** 12 - 1 if datos.get("tasa_mensual") else tasa
        anios = meses / 12
        final = finanzas.interes_compuesto(monto, tasa_anual, anios)
        return (
            f"Si inviertes {_clp(monto)} al {_pct(tasa_anual)} anual durante {anios:g} años, "
            f"tendrías {_clp(final)}: una ganancia de {_clp(final - monto)}. {NOTA} "
            "Considera que la inflación reduce el valor real de esa ganancia."
        )

    return None


def _faltan_datos(intencion: str) -> str:
    ejemplos = {
        "credito": "el monto, el plazo y la tasa. Ej.: «crédito de $5.000.000 a 36 meses al 18% anual»",
        "ahorro": "la meta y el plazo. Ej.: «quiero ahorrar $2.000.000 en 12 meses»",
        "interes_compuesto": "el capital, la tasa y el plazo. Ej.: «invertir $1.000.000 al 6% por 5 años»",
    }
    return f"Para calcularlo necesito {ejemplos[intencion]}."


def _preguntar_openai(mensaje: str) -> str | None:
    clave = os.getenv("OPENAI_API_KEY")
    if not clave:
        return None
    cuerpo = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": mensaje},
        ],
        "max_tokens": 400,
    }
    solicitud = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(cuerpo).encode(),
        headers={"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(solicitud, timeout=30) as respuesta:
            datos = json.load(respuesta)
        return datos["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def responder(mensaje: str) -> dict:
    """Responde un mensaje y devuelve {"respuesta", "fuente"}."""
    texto = _normalizar(mensaje)

    intencion = next((n for n, p in INTENCIONES.items() if re.search(p, texto)), None)
    if intencion:
        try:
            resultado = _calcular(intencion, _extraer_datos(texto))
        except (ValueError, OverflowError):
            resultado = None
        if resultado:
            return {"respuesta": resultado, "fuente": "calculo"}

    for patron, definicion in GLOSARIO.values():
        if re.search(patron, texto):
            return {"respuesta": definicion, "fuente": "glosario"}

    if intencion:
        return {"respuesta": _faltan_datos(intencion), "fuente": "reglas"}

    respuesta_ia = _preguntar_openai(mensaje)
    if respuesta_ia:
        return {"respuesta": respuesta_ia, "fuente": "openai"}

    return {"respuesta": AYUDA, "fuente": "reglas"}
