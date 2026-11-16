import pandas as pd
import pytest

import modelo


@pytest.mark.parametrize("valor, esperado", [
    (4_999, 10_000),     # nunca baja del mínimo real
    (94_000, 90_000),
    (96_000, 100_000),
    (250_000, 250_000),
])
def test_redondear_limite(valor, esperado):
    assert modelo.redondear_limite(valor) == esperado


def test_modelo_final_predice_un_limite_valido():
    m = modelo.cargar_modelo()
    fila = {c: v["mediana"] for c, v in modelo.valores_columnas().items()}
    prediccion, redondeada = modelo.predecir(fila)
    assert list(m.feature_names_in_) == list(fila)
    assert prediccion > 0
    assert redondeada % 10_000 == 0 and redondeada >= 10_000


def test_guardar_feedback_crea_el_csv_con_cabecera(tmp_path, monkeypatch):
    monkeypatch.setattr(modelo, "RUTA_FEEDBACK", tmp_path / "feedback.csv")
    entradas = {"AGE": 30, "EDUCATION": 1, "MARRIAGE": 2}
    modelo.guardar_feedback(entradas, 95_478.4, 100_000, "Adecuado", None)
    modelo.guardar_feedback(entradas, 80_000.0, 80_000, None, 200_000)
    df = pd.read_csv(tmp_path / "feedback.csv")
    assert len(df) == 2
    assert df.loc[0, "opinion"] == "Adecuado"
    assert df.loc[1, "limite_real"] == 200_000
    assert df.loc[0, "prediccion_redondeada"] == 100_000
