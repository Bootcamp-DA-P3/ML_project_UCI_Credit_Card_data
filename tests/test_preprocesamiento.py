import numpy as np
import pandas as pd
import pytest

from src.preprocesamiento import (
    COLS_BILL, COLS_NUMERICAS, COLS_PAY_AMT, agrupar_codigos, crear_preprocesador, log_con_signo,
)

COLUMNAS = (
    ["SEX", "EDUCATION", "MARRIAGE", "AGE"]
    + [f"PAY_{i}" for i in range(1, 7)] + COLS_BILL + COLS_PAY_AMT
)


def clientes(n=6):
    """Clientes sintéticos con las 22 columnas que espera el pipeline."""
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.integers(0, 3, size=(n, len(COLUMNAS))), columns=COLUMNAS)
    df["EDUCATION"] = [1, 2, 3, 4, 2, 1][:n]
    df["MARRIAGE"] = [1, 2, 3, 2, 1, 2][:n]
    df["AGE"] = rng.integers(21, 70, size=n)
    return df


def test_agrupar_codigos_pasa_codigos_raros_a_otros():
    X = pd.DataFrame({"EDUCATION": [0, 1, 5, 6, 2], "MARRIAGE": [0, 1, 2, 3, 0]})
    r = agrupar_codigos(X)
    assert r["EDUCATION"].tolist() == [4, 1, 4, 4, 2]
    assert r["MARRIAGE"].tolist() == [3, 1, 2, 3, 3]


def test_agrupar_codigos_no_modifica_la_entrada():
    X = pd.DataFrame({"EDUCATION": [0], "MARRIAGE": [0]})
    agrupar_codigos(X)
    assert X["EDUCATION"].iloc[0] == 0


def test_agrupar_codigos_ignora_columnas_ausentes():
    X = pd.DataFrame({"AGE": [30, 40]})
    assert agrupar_codigos(X).equals(X)


def test_log_con_signo_conserva_el_signo_y_el_cero():
    r = log_con_signo(pd.Series([-100.0, 0.0, 100.0]))
    assert r.iloc[0] < 0 < r.iloc[2]
    assert r.iloc[1] == 0
    assert r.iloc[0] == pytest.approx(-r.iloc[2])


def test_preprocesador_descarta_sex_por_defecto():
    p = crear_preprocesador()
    salida = p.fit_transform(clientes())
    nombres = p.get_feature_names_out()
    assert salida.shape[0] == 6
    assert not any("SEX" in n for n in nombres)


def test_preprocesador_con_sex_anade_columnas():
    base = crear_preprocesador().fit(clientes()).get_feature_names_out()
    con_sex = crear_preprocesador(incluir_sex=True).fit(clientes()).get_feature_names_out()
    assert len(con_sex) > len(base)


def test_preprocesador_escala_las_numericas():
    X = clientes()
    p = crear_preprocesador()
    salida = pd.DataFrame(p.fit_transform(X), columns=p.get_feature_names_out())
    for col in COLS_NUMERICAS:
        assert salida[f"numericas__{col}"].mean() == pytest.approx(0, abs=1e-9)


def test_preprocesador_acepta_categoria_desconocida():
    p = crear_preprocesador().fit(clientes())
    nuevo = clientes(1)
    nuevo["EDUCATION"] = 9
    assert p.transform(nuevo).shape[0] == 1
