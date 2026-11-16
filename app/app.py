"""Punto de entrada de la app de Streamlit."""
import sys
from pathlib import Path

import streamlit as st

# Añadimos la carpeta app y la raíz del repo para poder importar src.*
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(APP_DIR.parent))

import tema  # noqa: E402

st.set_page_config(page_title="Límite de crédito", layout="wide")
tema.inject_css()

pagina = st.navigation(
    [
        st.Page("app_pages/inicio.py", title="Inicio", icon=":material/home:",
                default=True,
                help="Resumen del proyecto y de los datos."),
        st.Page("app_pages/dashboard.py", title="Dashboard",
                icon=":material/bar_chart:",
                help="Análisis del límite de crédito según perfil e historial."),
        st.Page("app_pages/prediccion.py", title="Predicción",
                icon=":material/calculate:",
                help="Estimación del límite con el modelo final."),
    ],
    position="top",
)

tema.brand()
pagina.run()
