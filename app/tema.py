"""Tema de la app: colores, CSS, pequeños helpers de HTML y estilo de Altair."""
import html

import streamlit as st

TOKENS = {
    "paper": "#f2f2ef",
    "surface": "#fafaf8",
    "ink": "#0a0a0a",
    "ink_muted": "#5c5c58",
    "line": "#b9b9b4",
    "violet": "#6b3df5",
    "on_violet": "#ffffff",
    "lime": "#d4ff3a",
    "on_lime": "#0a0a0a",
}
T = TOKENS

# Colores extra solo para distinguir categorías en los gráficos (lima queda para la tarjeta)
COLOR_TEAL = "#00a896"
COLOR_NARANJA = "#ff5a1f"
COLOR_LAVANDA = "#d9ceff"  # extremo claro de la escala violeta
CATEGORIAS = [T["violet"], COLOR_TEAL, COLOR_NARANJA, T["ink"]]

FONT_MONO = '"JetBrains Mono", ui-monospace, monospace'
FONT_DISPLAY = "Anton, Impact, 'Arial Narrow', sans-serif"
FONT_SANS = "Inter, system-ui, sans-serif"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&display=swap');
:root {{
  --paper: {T['paper']}; --surface: {T['surface']}; --ink: {T['ink']};
  --ink-muted: {T['ink_muted']}; --line: {T['line']}; --violet: {T['violet']};
  --lime: {T['lime']};
}}
.ui-brand {{ font-family: {FONT_MONO}; font-weight: 700; font-size: .85rem;
  letter-spacing: .08em; color: var(--ink); }}
.ui-label {{ font-family: {FONT_MONO}; font-weight: 500; font-size: .75rem;
  text-transform: uppercase; letter-spacing: .08em; color: var(--violet); }}
.ui-display {{ font-family: {FONT_DISPLAY}; text-transform: uppercase;
  color: var(--ink); line-height: 1; margin: 0; font-weight: 400; }}
.ui-title {{ font-size: clamp(2.6rem, 6vw, 4.5rem); }}
.ui-h2 {{ font-size: clamp(1.9rem, 3.5vw, 2.6rem); }}
.ui-kicker {{ font-family: {FONT_MONO}; font-weight: 500; font-size: .85rem;
  text-transform: uppercase; color: var(--violet); margin: .5rem 0 1rem; }}
.ui-rule {{ border-top: 1px solid var(--line); margin: 1rem 0; }}
.ui-chart-title {{ font-family: {FONT_MONO}; font-weight: 500; font-size: .75rem;
  text-transform: uppercase; letter-spacing: .08em; color: var(--ink-muted); }}
.ui-insight {{ font-family: {FONT_SANS}; font-size: 1rem; line-height: 1.6;
  max-width: 72ch; color: var(--ink); }}
.ui-status {{ font-family: {FONT_MONO}; font-size: .75rem; text-transform: uppercase;
  color: var(--ink-muted); border-top: 1px solid var(--line); padding-top: .5rem;
  margin-top: 2rem; }}
.ui-status a {{ color: var(--violet); border-bottom: 1px solid var(--violet);
  text-decoration: none; }}
.ui-signal {{ background: var(--lime); color: {T['on_lime']}; padding: 1rem;
  display: flex; align-items: baseline; gap: 1rem; flex-wrap: wrap; }}
.ui-signal b {{ font-family: {FONT_DISPLAY}; font-weight: 400;
  font-size: clamp(2rem, 4vw, 3rem); }}
.ui-signal span {{ font-family: {FONT_MONO}; font-weight: 500; font-size: .8rem;
  text-transform: uppercase; }}
[data-testid="stMetricLabel"] {{ font-family: {FONT_MONO}; text-transform: uppercase;
  font-size: .68rem; color: var(--ink-muted); }}
[data-testid="stMetricValue"] {{ font-family: {FONT_DISPLAY}; }}
"""


def inject_css():
    st.html(f"<style>{CSS}</style>")


def _e(texto):
    return html.escape(str(texto))


def brand(texto="PROYECTO 7 · REGRESIÓN"):
    st.html(f'<div class="ui-brand">{_e(texto)}</div>')


def page_title(etiqueta, titulo, kicker):
    st.html(
        f'<div class="ui-label">{_e(etiqueta)}</div>'
        f'<h1 class="ui-display ui-title">{_e(titulo)}</h1>'
        f'<div class="ui-kicker">{_e(kicker)}</div><div class="ui-rule"></div>'
    )


def section_header(numero, seccion, titulo, kicker):
    st.html(
        f'<div class="ui-label">{_e(numero)} — {_e(seccion)}</div>'
        f'<h2 class="ui-display ui-h2">{_e(titulo)}</h2>'
        f'<div class="ui-kicker">{_e(kicker)}</div>'
    )


def chart_title(texto):
    st.html(f'<div class="ui-chart-title">{_e(texto)}</div>')


def signal_card(valor, texto):
    st.html(f'<div class="ui-signal"><b>{_e(valor)}</b><span>{_e(texto)}</span></div>')


def insight(*frases):
    st.html(f'<p class="ui-insight">{_e(" ".join(frases))}</p>')


def status_bar(texto, link_texto=None, link_url=None):
    enlace = ""
    if link_texto and link_url:
        enlace = f' · <a href="{_e(link_url)}">{_e(link_texto)} ↗</a>'
    st.html(f'<div class="ui-status">● {_e(texto)}{enlace}</div>')


def card(nombre):
    return st.container(border=True, key=f"card_{nombre}")


def estilo_altair(chart):
    """Aplica el estilo del tema a un gráfico de Altair."""
    return (
        chart.configure(font="JetBrains Mono", background=T["surface"])
        .configure_view(stroke=T["line"])
        .configure_axis(
            gridColor=T["line"], domainColor=T["ink"], tickColor=T["ink"],
            labelColor=T["ink"], titleColor=T["ink_muted"],
            labelFontSize=11, titleFontSize=11, titleFontWeight=500,
        )
        .configure_legend(
            orient="top", title=None, labelColor=T["ink"], labelFontSize=11,
            symbolType="square", symbolStrokeColor=T["ink"], symbolStrokeWidth=1,
        )
    )
