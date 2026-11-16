import altair as alt
import streamlit as st

import datos
import tema

T = tema.T
ALTO = 300


def miles(x):
    return f"{x:,.0f}".replace(",", ".")


def dibujar(chart, descripcion):
    st.altair_chart(tema.estilo_altair(chart), theme=None, alt=descripcion)


def barras(color=None):
    return dict(color=color or T["violet"], stroke=T["ink"], strokeWidth=1, cornerRadius=0)


def barras_grupo(df, x, y, titulo_y, descripcion, secuencial=False):
    """Barras por grupo. Categorías: un color por grupo. Secuencial: más oscuro = más límite."""
    if secuencial:
        color = alt.Color(f"{y}:Q", legend=None,
                          scale=alt.Scale(range=[tema.COLOR_LAVANDA, T["violet"]]))
    else:
        color = alt.Color(f"{x}:N", legend=None,
                          scale=alt.Scale(domain=list(df[x]), range=tema.CATEGORIAS[:len(df)]))
    chart = alt.Chart(df).mark_bar(stroke=T["ink"], strokeWidth=1, cornerRadius=0).encode(
        x=alt.X(f"{x}:N", sort=None, title=None),
        y=alt.Y(f"{y}:Q", title=titulo_y, axis=alt.Axis(format=",.0f")),
        color=color,
        tooltip=[alt.Tooltip(f"{x}:N", title="Grupo"),
                 alt.Tooltip("clientes:Q", title="Clientes", format=",.0f"),
                 alt.Tooltip(f"{y}:Q", title=titulo_y, format=",.0f")],
    ).properties(height=ALTO)
    dibujar(chart, descripcion)


# Filtros en la barra lateral: valores iniciales y botón para restaurarlos
RANGOS = datos.rangos()
INICIALES = datos.filtros_vacios()


def restaurar_filtros():
    for k, v in INICIALES.items():
        st.session_state[f"f_{k}"] = v


for k, v in INICIALES.items():
    st.session_state.setdefault(f"f_{k}", v)

with st.sidebar:
    tema.chart_title("Filtros")
    st.pills("Educación", INICIALES["educacion"], selection_mode="multi", key="f_educacion")
    st.pills("Estado civil", INICIALES["estado_civil"], selection_mode="multi",
             key="f_estado_civil")
    st.slider("Edad", *RANGOS["edad"], key="f_edad")
    st.slider("Límite (NT$)", *RANGOS["limite"], step=10_000, key="f_limite")
    st.multiselect("Estado de pago en septiembre (PAY_0)", RANGOS["pay0"], key="f_pay0")
    st.button("Restaurar filtros", on_click=restaurar_filtros, icon=":material/restart_alt:",
              width="stretch")

filtros = {k: st.session_state[f"f_{k}"] for k in INICIALES}
clave = datos.clave(filtros)
total = datos.resumen(datos.clave(INICIALES))["filas"]
r = datos.resumen(clave)

tema.page_title("/01 — DASHBOARD", "Análisis de los datos",
                "Límite de crédito, perfil e historial")

if r["filas"] == 0:
    st.warning("Ningún cliente cumple los filtros. Amplía alguno o restáuralos.",
               title="Sin datos")
    st.stop()

with st.container(horizontal=True):
    st.metric("Clientes", miles(r["filas"]), border=True)
    st.metric("Límite medio (NT$)", miles(r["media_limite"]), border=True)
    st.metric("Edad mediana", f"{r['edad_mediana']:.0f}", border=True)
tema.signal_card(miles(r["mediana_limite"]), "Límite mediano (NT$)")

# 02 Target
tema.section_header("/02", "TARGET", "Límite de crédito", "Distribución de LIMIT_BAL")
with tema.card("target"):
    tema.chart_title("Clientes por tramo de límite")
    h = datos.histograma_limite(clave)
    chart = alt.Chart(h).mark_bar(**barras()).encode(
        x=alt.X("desde:Q", title="LIMIT_BAL (NT$)", axis=alt.Axis(format=",.0f")),
        x2="hasta:Q",
        y=alt.Y("clientes:Q", title="Clientes"),
        tooltip=[alt.Tooltip("desde:Q", title="Desde", format=",.0f"),
                 alt.Tooltip("hasta:Q", title="Hasta", format=",.0f"),
                 alt.Tooltip("clientes:Q", title="Clientes", format=",.0f")],
    ).properties(height=ALTO)
    dibujar(chart, "Histograma del límite de crédito de los clientes")

# 03 Perfil
tema.section_header("/03", "PERFIL", "Perfil del cliente", "Mediana del límite por grupo")
c1, c2 = st.columns(2)
with c1, tema.card("educacion"):
    tema.chart_title("Por educación")
    barras_grupo(datos.limite_por(clave, "EDUCATION"), "grupo", "limite_mediano",
                 "Límite mediano (NT$)",
                 "Barras con la mediana del límite por nivel de educación")
with c2, tema.card("estado_civil"):
    tema.chart_title("Por estado civil")
    barras_grupo(datos.limite_por(clave, "MARRIAGE"), "grupo", "limite_mediano",
                 "Límite mediano (NT$)",
                 "Barras con la mediana del límite por estado civil")
with tema.card("edad"):
    tema.chart_title("Por tramo de edad")
    barras_grupo(datos.limite_por_edad(clave), "tramo", "limite_mediano",
                 "Límite mediano (NT$)",
                 "Barras con la mediana del límite por tramo de edad", secuencial=True)

# 04 Historial
tema.section_header("/04", "HISTORIAL", "Estado de pago", "Septiembre (PAY_0)")
p = datos.limite_por_pay0(clave)
p["situacion"] = p["PAY_0"].map(lambda v: "Al día" if v <= 0 else "Retraso")
COLOR_SITUACION = alt.Color("situacion:N", scale=alt.Scale(
    domain=["Al día", "Retraso"], range=[tema.COLOR_TEAL, tema.COLOR_NARANJA]))
with tema.card("pay0_limite"):
    tema.chart_title("Límite medio por estado de pago")
    chart = alt.Chart(p).mark_bar(**barras()).encode(
        x=alt.X("PAY_0:O", title="PAY_0"),
        color=COLOR_SITUACION,
        y=alt.Y("limite_medio:Q", title="Límite medio (NT$)",
                axis=alt.Axis(format=",.0f")),
        tooltip=[alt.Tooltip("PAY_0:O", title="PAY_0"),
                 alt.Tooltip("clientes:Q", title="Clientes", format=",.0f"),
                 alt.Tooltip("limite_medio:Q", title="Límite medio", format=",.0f")],
    ).properties(height=ALTO)
    dibujar(chart, "Barras con el límite medio por estado de pago en septiembre")
    st.caption("Al día: PAY_0 negativo o 0. Retraso: de 1 a 8 meses.")
with tema.card("pay0_clientes"):
    tema.chart_title("Clientes por estado de pago")
    chart = alt.Chart(p).mark_bar(**barras()).encode(
        x=alt.X("PAY_0:O", title="PAY_0"),
        color=COLOR_SITUACION,
        y=alt.Y("clientes:Q", title="Clientes", axis=alt.Axis(format=",.0f")),
        tooltip=[alt.Tooltip("PAY_0:O", title="PAY_0"),
                 alt.Tooltip("clientes:Q", title="Clientes", format=",.0f")],
    ).properties(height=ALTO)
    dibujar(chart, "Barras con el número de clientes por estado de pago en septiembre")

# 05 Correlaciones
tema.section_header("/05", "CORRELACIONES", "Correlación con el límite",
                    "Pearson con LIMIT_BAL")
cor = datos.correlaciones(clave)
cor["grupo"] = cor["variable"].map(
    lambda v: "Pagos" if v.startswith("PAY_AMT") else "Facturas" if v.startswith("BILL")
    else "Estado de pago")
with tema.card("correlaciones"):
    tema.chart_title("Correlación por variable")
    chart = alt.Chart(cor).mark_bar(stroke=T["ink"], strokeWidth=1, cornerRadius=0).encode(
        y=alt.Y("variable:N", sort=None, title=None),
        x=alt.X("correlacion:Q", title="Correlación"),
        color=alt.Color("grupo:N", scale=alt.Scale(
            domain=["Estado de pago", "Facturas", "Pagos"],
            range=[T["violet"], tema.COLOR_TEAL, tema.COLOR_NARANJA])),
        tooltip=[alt.Tooltip("variable:N", title="Variable"),
                 alt.Tooltip("grupo:N", title="Grupo"),
                 alt.Tooltip("correlacion:Q", title="Correlación", format=".2f")],
    ).properties(height=ALTO + 200)
    dibujar(chart, "Barras horizontales con la correlación de cada variable con el límite")

tema.status_bar(f"DATOS: UCI_CREDIT_CARD.CSV · {miles(r['filas'])} DE {miles(total)} CLIENTES "
                f"CON LOS FILTROS ACTUALES")
