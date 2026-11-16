import streamlit as st

import datos
import modelo
import tema

MESES = ["Septiembre", "Agosto", "Julio", "Junio", "Mayo", "Abril"]
ESTADOS_PAGO = "-2 sin consumo, -1 pagado, 0 crédito rotativo, 1 a 8 meses de retraso"

v = modelo.valores_columnas()


def numero(etiqueta, col, key, paso=1, ayuda=None):
    """Campo numérico con rango y valor inicial sacados de los datos."""
    return st.number_input(
        etiqueta, min_value=v[col]["min"], max_value=v[col]["max"],
        value=v[col]["mediana"], step=paso, key=key, help=ayuda,
    )


tema.page_title("/02 — PREDICCIÓN", "Predicción", "Límite recomendado para un cliente")
tema.insight(
    "Introduce el perfil y el historial de los últimos 6 meses. Los campos del "
    "historial parten de la mediana de los clientes.",
)

with st.form("form_prediccion"):
    c1, c2, c3 = st.columns(3)
    with c1:
        edad = numero("Edad", "AGE", "edad")
    with c2:
        educacion = st.selectbox(
            "Educación", list(datos.ETIQUETAS["EDUCATION"]),
            index=list(datos.ETIQUETAS["EDUCATION"]).index(v["EDUCATION"]["mediana"]),
            format_func=datos.ETIQUETAS["EDUCATION"].get, key="educacion",
        )
    with c3:
        estado_civil = st.selectbox(
            "Estado civil", list(datos.ETIQUETAS["MARRIAGE"]),
            index=list(datos.ETIQUETAS["MARRIAGE"]).index(v["MARRIAGE"]["mediana"]),
            format_func=datos.ETIQUETAS["MARRIAGE"].get, key="estado_civil",
        )

    with st.expander("Historial de 6 meses", expanded=False):
        st.caption(f"Estado de pago: {ESTADOS_PAGO}.")
        for i, mes in enumerate(MESES, start=1):
            st.markdown(f"**{mes}**")
            a, b, c = st.columns(3)
            with a:
                numero("Estado de pago", f"PAY_{i}", f"pay_{i}")
            with b:
                numero("Factura", f"BILL_AMT{i}", f"bill_{i}", paso=1000)
            with c:
                numero("Pago", f"PAY_AMT{i}", f"payamt_{i}", paso=1000)

    enviado = st.form_submit_button("Calcular límite", type="primary",
                                    icon=":material/calculate:", key="calcular")

if enviado:
    entradas = {"AGE": edad, "EDUCATION": educacion, "MARRIAGE": estado_civil}
    for i in range(1, 7):
        entradas[f"PAY_{i}"] = st.session_state[f"pay_{i}"]
        entradas[f"BILL_AMT{i}"] = st.session_state[f"bill_{i}"]
        entradas[f"PAY_AMT{i}"] = st.session_state[f"payamt_{i}"]
    prediccion, redondeada = modelo.predecir(entradas)
    st.session_state["resultado"] = {
        "entradas": entradas, "prediccion": prediccion, "redondeada": redondeada,
    }
    st.session_state["feedback_guardado"] = False

resultado = st.session_state.get("resultado")
if resultado:
    limite = f"{resultado['redondeada']:,}".replace(",", ".")
    mae = f"{modelo.METRICAS_TEST['MAE']:,}".replace(",", ".")
    tema.signal_card(f"{limite} NT$", "Límite recomendado")
    tema.insight(
        f"Margen de error típico: unos {mae} NT$ arriba o abajo (error absoluto "
        "medio en test).",
    )

    tema.chart_title("¿Te parece adecuado?")
    with st.form("form_feedback", clear_on_submit=False):
        opinion = st.segmented_control("Opinión", modelo.OPINIONES, key="opinion")
        limite_real = st.number_input(
            "Límite real, si lo conoces (0 si no)", min_value=0, value=0,
            step=10_000, key="limite_real",
        )
        guardar = st.form_submit_button("Guardar feedback", icon=":material/save:",
                                        key="guardar_feedback")

    if guardar:
        if st.session_state.get("feedback_guardado"):
            st.info("Ya guardaste el feedback de esta predicción.")
        elif opinion is None and not limite_real:
            st.warning("Elige una opinión o indica el límite real.")
        else:
            modelo.guardar_feedback(
                resultado["entradas"], resultado["prediccion"], resultado["redondeada"],
                opinion, int(limite_real) or None,
            )
            st.session_state["feedback_guardado"] = True
            st.success("Feedback guardado. Gracias.")
