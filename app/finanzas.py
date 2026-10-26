"""Funciones financieras puras. Las tasas se expresan en decimales (0.12 = 12%)."""


def tasa_anual_a_mensual(tasa_anual: float) -> float:
    """Convierte una tasa nominal anual en tasa mensual (convención usada en créditos)."""
    return tasa_anual / 12


def cuota_mensual(monto: float, tasa_mensual: float, meses: int) -> float:
    """Cuota fija de un crédito con sistema francés."""
    if monto <= 0 or meses <= 0 or tasa_mensual < 0:
        raise ValueError("monto y meses deben ser positivos y la tasa no negativa")
    if tasa_mensual == 0:
        return monto / meses
    return monto * tasa_mensual / (1 - (1 + tasa_mensual) ** -meses)


def total_pagado_e_intereses(monto: float, tasa_mensual: float, meses: int) -> tuple[float, float]:
    """Devuelve (total pagado, intereses pagados) de un crédito con sistema francés."""
    total = cuota_mensual(monto, tasa_mensual, meses) * meses
    return total, total - monto


def ahorro_mensual_para_meta(meta: float, meses: int, tasa_mensual: float = 0.0) -> float:
    """Depósito mensual (a fin de mes) necesario para juntar `meta` en `meses`."""
    if meta <= 0 or meses <= 0 or tasa_mensual < 0:
        raise ValueError("meta y meses deben ser positivos y la tasa no negativa")
    if tasa_mensual == 0:
        return meta / meses
    return meta * tasa_mensual / ((1 + tasa_mensual) ** meses - 1)


def interes_compuesto(capital: float, tasa_anual: float, anios: float) -> float:
    """Monto final de `capital` invertido a una tasa efectiva anual durante `anios`."""
    if capital <= 0 or anios < 0 or tasa_anual <= -1:
        raise ValueError("capital debe ser positivo, años no negativos y tasa mayor a -100%")
    return capital * (1 + tasa_anual) ** anios
