"""Modelo final: carga, predicción y recogida de feedback."""
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

import datos

RAIZ = Path(__file__).resolve().parents[1]
RUTA_MODELO = RAIZ / "models" / "modelo_final.joblib"
RUTA_FEEDBACK = RAIZ / "data" / "feedback.csv"

# Métricas de test de la sección 12 del notebook
METRICAS_TEST = {"R2": 0.511, "RMSE": 88233, "MAE": 64496}

OPINIONES = ["Adecuado", "Demasiado alto", "Demasiado bajo"]


@st.cache_resource
def cargar_modelo():
    """Pipeline completo (preprocesado y XGBoost). Se lee una sola vez."""
    return joblib.load(RUTA_MODELO)


@st.cache_data
def valores_columnas() -> dict:
    """Mínimo, máximo y mediana de cada columna de entrada, con PAY_0 renombrada a PAY_1."""
    df = datos.cargar_datos().rename(columns={"PAY_0": "PAY_1"})
    columnas = list(cargar_modelo().feature_names_in_)
    return {
        c: {"min": int(df[c].min()), "max": int(df[c].max()), "mediana": int(df[c].median())}
        for c in columnas
    }


def redondear_limite(valor: float) -> int:
    """Múltiplo de 10.000 más cercano, sin bajar de 10.000 (el mínimo real)."""
    return max(10_000, int(round(valor / 10_000)) * 10_000)


def predecir(entradas: dict) -> tuple[float, int]:
    """Devuelve la predicción sin redondear y redondeada.

    SEX no influye en el modelo, pero el pipeline espera la columna: usamos la mediana.
    """
    modelo = cargar_modelo()
    fila = {c: entradas.get(c, v["mediana"]) for c, v in valores_columnas().items()}
    prediccion = float(modelo.predict(pd.DataFrame([fila]))[0])
    return prediccion, redondear_limite(prediccion)


def guardar_feedback(entradas: dict, prediccion: float, redondeada: int,
                     opinion: str | None, limite_real: int | None) -> None:
    """Añade una fila a data/feedback.csv (se crea la primera vez)."""
    fila = {"fecha": datetime.now().isoformat(timespec="seconds"), **entradas,
            "prediccion": round(prediccion), "prediccion_redondeada": redondeada,
            "opinion": opinion, "limite_real": limite_real}
    RUTA_FEEDBACK.parent.mkdir(exist_ok=True)
    pd.DataFrame([fila]).to_csv(
        RUTA_FEEDBACK, mode="a", header=not RUTA_FEEDBACK.exists(), index=False
    )
