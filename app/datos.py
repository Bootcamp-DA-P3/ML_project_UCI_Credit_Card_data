"""Carga de datos y agregaciones para la app."""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from src.preprocesamiento import agrupar_codigos

RUTA_DATOS = Path(__file__).resolve().parents[1] / "data" / "UCI_Credit_Card.csv"

ETIQUETAS = {
    "EDUCATION": {1: "Posgrado", 2: "Universidad", 3: "Secundaria", 4: "Otros"},
    "MARRIAGE": {1: "Casado", 2: "Soltero", 3: "Otros"},
}
COLS_PAY = ["PAY_0"] + [f"PAY_{i}" for i in range(2, 7)]
COLS_BILL = [f"BILL_AMT{i}" for i in range(1, 7)]
COLS_PAYAMT = [f"PAY_AMT{i}" for i in range(1, 7)]


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    return pd.read_csv(RUTA_DATOS)


@st.cache_data
def rangos() -> dict:
    """Valores mínimo y máximo y categorías disponibles para los filtros."""
    df = cargar_datos()
    return {
        "edad": (int(df["AGE"].min()), int(df["AGE"].max())),
        "limite": (int(df["LIMIT_BAL"].min()), int(df["LIMIT_BAL"].max())),
        "pay0": sorted(int(v) for v in df["PAY_0"].unique()),
    }


def filtros_vacios() -> dict:
    """Filtros que no descartan ninguna fila."""
    r = rangos()
    return {
        "educacion": tuple(ETIQUETAS["EDUCATION"].values()),
        "estado_civil": tuple(ETIQUETAS["MARRIAGE"].values()),
        "edad": r["edad"],
        "limite": r["limite"],
        "pay0": tuple(r["pay0"]),
    }


def clave(f: dict) -> tuple:
    """Filtros como tupla, para que st.cache_data pueda usarlos como clave."""
    return (
        tuple(f["educacion"]), tuple(f["estado_civil"]),
        tuple(f["edad"]), tuple(f["limite"]), tuple(f["pay0"]),
    )


@st.cache_data
def _filtrado(clave: tuple) -> pd.DataFrame:
    educacion, civil, edad, limite, pay0 = clave
    df = agrupar_codigos(cargar_datos())
    mascara = (
        df["EDUCATION"].map(ETIQUETAS["EDUCATION"]).isin(educacion)
        & df["MARRIAGE"].map(ETIQUETAS["MARRIAGE"]).isin(civil)
        & df["AGE"].between(edad[0], edad[1])
        & df["LIMIT_BAL"].between(limite[0], limite[1])
        & df["PAY_0"].isin(pay0)
    )
    return df[mascara]


def filtrar(f: dict) -> pd.DataFrame:
    return _filtrado(clave(f))


@st.cache_data
def resumen(clave: tuple) -> dict:
    df = _filtrado(clave)
    return {
        "filas": len(df),
        "columnas": df.shape[1],
        "meses_historial": len(COLS_PAYAMT),
        "mediana_limite": float(df["LIMIT_BAL"].median()),
        "media_limite": float(df["LIMIT_BAL"].mean()),
        "edad_mediana": float(df["AGE"].median()),
    }


@st.cache_data
def histograma_limite(clave: tuple, bins: int = 40) -> pd.DataFrame:
    """Histograma ya agregado de LIMIT_BAL."""
    cuentas, bordes = np.histogram(_filtrado(clave)["LIMIT_BAL"], bins=bins)
    return pd.DataFrame({"desde": bordes[:-1], "hasta": bordes[1:], "clientes": cuentas})


@st.cache_data
def limite_por(clave: tuple, col: str) -> pd.DataFrame:
    df = _filtrado(clave)
    g = df.groupby(col)["LIMIT_BAL"].agg(clientes="count", limite_mediano="median")
    g = g.sort_index().reset_index()
    g[col] = g[col].map(ETIQUETAS[col])
    return g.rename(columns={col: "grupo"})


@st.cache_data
def limite_por_edad(clave: tuple) -> pd.DataFrame:
    df = _filtrado(clave)
    tramo = pd.cut(df["AGE"], bins=[20, 25, 30, 35, 40, 45, 50, 60, 80])
    g = df.groupby(tramo, observed=True)["LIMIT_BAL"].agg(
        clientes="count", limite_mediano="median"
    ).reset_index()
    g["tramo"] = g["AGE"].map(lambda i: f"{int(i.left) + 1}-{int(i.right)}")
    return g[["tramo", "clientes", "limite_mediano"]]


@st.cache_data
def limite_por_pay0(clave: tuple) -> pd.DataFrame:
    g = _filtrado(clave).groupby("PAY_0")["LIMIT_BAL"].agg(
        clientes="count", limite_medio="mean"
    )
    return g.reset_index()


@st.cache_data
def correlaciones(clave: tuple) -> pd.DataFrame:
    df = _filtrado(clave)
    cols = COLS_PAY + COLS_BILL + COLS_PAYAMT
    # Si un filtro deja una columna constante, su correlación no existe: la quitamos
    c = df[cols].corrwith(df["LIMIT_BAL"]).dropna()
    return (
        c.rename("correlacion").rename_axis("variable").reset_index()
        .sort_values("correlacion", ascending=False).reset_index(drop=True)
    )
