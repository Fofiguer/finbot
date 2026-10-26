import pytest

from app import finanzas


def test_tasa_anual_a_mensual():
    assert finanzas.tasa_anual_a_mensual(0.12) == pytest.approx(0.01)


def test_cuota_10_millones_36_meses_12_anual():
    tasa = finanzas.tasa_anual_a_mensual(0.12)
    assert round(finanzas.cuota_mensual(10_000_000, tasa, 36)) == 332_143


def test_cuota_sin_interes():
    assert finanzas.cuota_mensual(1_200_000, 0, 12) == 100_000


def test_total_pagado_e_intereses():
    total, intereses = finanzas.total_pagado_e_intereses(10_000_000, 0.01, 36)
    assert round(total) == 11_957_152
    assert intereses == pytest.approx(total - 10_000_000)


def test_ahorro_mensual_sin_rentabilidad():
    assert finanzas.ahorro_mensual_para_meta(2_000_000, 10) == 200_000


def test_ahorro_mensual_con_rentabilidad_alcanza_la_meta():
    tasa, meses = 0.005, 24
    deposito = finanzas.ahorro_mensual_para_meta(1_000_000, meses, tasa)
    saldo = 0.0
    for _ in range(meses):
        saldo = saldo * (1 + tasa) + deposito
    assert saldo == pytest.approx(1_000_000)
    assert deposito < 1_000_000 / meses


def test_interes_compuesto():
    assert finanzas.interes_compuesto(1_000_000, 0.06, 5) == pytest.approx(1_338_225.5776)


def test_interes_compuesto_cero_anios():
    assert finanzas.interes_compuesto(500_000, 0.1, 0) == 500_000


@pytest.mark.parametrize(
    "funcion, args",
    [
        (finanzas.cuota_mensual, (0, 0.01, 12)),
        (finanzas.cuota_mensual, (1000, 0.01, 0)),
        (finanzas.cuota_mensual, (1000, -0.01, 12)),
        (finanzas.ahorro_mensual_para_meta, (1000, 0)),
        (finanzas.interes_compuesto, (-1, 0.05, 1)),
    ],
)
def test_entradas_invalidas(funcion, args):
    with pytest.raises(ValueError):
        funcion(*args)
