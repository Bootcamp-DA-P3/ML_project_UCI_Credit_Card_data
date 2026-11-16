import streamlit as st

import datos
import tema

r = datos.resumen(datos.clave(datos.filtros_vacios()))
filas = f"{r['filas']:,}".replace(",", ".")

tema.page_title("/00 — PROYECTO", "Límite de crédito",
                "Revisión de límite de cliente existente")
tema.insight(
    "Trabajamos con clientes de tarjeta de un banco de Taiwán, de abril a "
    "septiembre de 2005, con importes en dólares taiwaneses (NT$).",
    "Queremos estimar el límite de crédito (LIMIT_BAL) a partir del perfil y "
    "del historial de 6 meses de facturas y pagos.",
    "La app muestra el análisis de los datos y estima el límite de un cliente "
    "con el modelo final.",
)

with st.container(horizontal=True):
    st.metric("Clientes", filas, border=True)
    st.metric("Variables", r["columnas"], border=True)
    st.metric("Meses de historial", r["meses_historial"], border=True)

with st.container(horizontal=True):
    st.page_link("app_pages/dashboard.py", label="Ver el dashboard",
                 icon=":material/arrow_outward:")
    st.page_link("app_pages/prediccion.py", label="Calcular un límite",
                 icon=":material/arrow_outward:")
tema.status_bar(f"DATOS: UCI_CREDIT_CARD.CSV · {filas} FILAS")
