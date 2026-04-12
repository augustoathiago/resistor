import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

# ---------------------------
# Constantes
# ---------------------------
V_MAX = 30.0          # Slider e eixo Y do gráfico (0..30 V)
R_MIN = 1000.0        # (pedido) 1000..1300 Ω
R_MAX = 1300.0
X_MAX_mA = 40.0       # Eixo X fixo (0..40 mA)

# Tamanho fixo do gráfico (pedido: manter horizontal fixo)
CHART_WIDTH = 520
CHART_HEIGHT = 260

st.set_page_config(
    page_title="Simulador Resistor Física 2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Formatação: 3 algarismos significativos em todo o app
# ---------------------------
def fmt_sig(x: float, sig: int = 3) -> str:
    """Formata com 'sig' algarismos significativos, preservando zeros."""
    if x == 0 or abs(x) < 1e-300:
        return "0." + "0" * (sig - 1)  # sig=3 => 0.00
    ax = abs(x)
    exp = math.floor(math.log10(ax))
    dec = sig - exp - 1
    if dec > 0:
        return f"{x:.{dec}f}"
    rounded = round(x, -dec)
    return f"{rounded:.0f}"

def fmt_mA(I_A: float) -> str:
    # Sempre em mA (pedido)
    return f"{fmt_sig(I_A * 1000.0, 3)} mA"

# ---------------------------
# Sincronização slider <-> input
# ---------------------------
def sync(from_key: str, to_key: str):
    st.session_state[to_key] = st.session_state[from_key]

def toggle_switch():
    st.session_state["sw"] = not st.session_state.get("sw", True)

# ---------------------------
# Estado inicial
# ---------------------------
if "V_slider" not in st.session_state:
    st.session_state["V_slider"] = 5.0
if "V_input" not in st.session_state:
    st.session_state["V_input"] = 5.0

if "R_slider" not in st.session_state:
    st.session_state["R_slider"] = 1100.0
if "R_input" not in st.session_state:
    st.session_state["R_input"] = 1100.0

if "sw" not in st.session_state:
    st.session_state["sw"] = True

# ---------------------------
# Cabeçalho (logo + título + descrição)
# ---------------------------
top_left, top_right = st.columns([0.18, 0.82], vertical_alignment="center")
with top_left:
    try:
        st.image("logo_maua.png", use_container_width=True)
    except Exception:
        st.empty()

with top_right:
    st.title("Simulador Resistor Física 2")
    st.write("Estude o comportamento de um resistor em um circuito simples.")

st.divider()

# ---------------------------
# Sidebar: controles
# ---------------------------
st.sidebar.title("Controles")

st.sidebar.subheader("Tensão da fonte (V)")
cV1, cV2 = st.sidebar.columns([1, 1], gap="small")
with cV1:
    st.slider(
        "Tensão da fonte (slider)",
        min_value=0.0,
        max_value=float(V_MAX),
        value=float(st.session_state["V_slider"]),
        step=0.1,
        key="V_slider",
        on_change=sync,
        args=("V_slider", "V_input"),
        label_visibility="collapsed",
    )
with cV2:
    st.number_input(
        "Tensão da fonte (digite)",
        min_value=0.0,
        max_value=float(V_MAX),
        value=float(st.session_state["V_input"]),
        step=0.1,
        key="V_input",
        on_change=sync,
        args=("V_input", "V_slider"),
        label_visibility="collapsed",
    )

st.sidebar.subheader("Resistência do resistor (Ω)")
cR1, cR2 = st.sidebar.columns([1, 1], gap="small")
with cR1:
    st.slider(
        "Resistência do resistor (slider)",
        min_value=float(R_MIN),
        max_value=float(R_MAX),
        value=float(st.session_state["R_slider"]),
        step=1.0,
        key="R_slider",
        on_change=sync,
        args=("R_slider", "R_input"),
        label_visibility="collapsed",
    )
with cR2:
    st.number_input(
        "Resistência do resistor (digite)",
        min_value=float(R_MIN),
        max_value=float(R_MAX),
        value=float(st.session_state["R_input"]),
        step=1.0,
        key="R_input",
        on_change=sync,
        args=("R_input", "R_slider"),
        label_visibility="collapsed",
    )

st.sidebar.subheader("Interruptor")
btn_label = "Abrir circuito (OFF)" if st.session_state["sw"] else "Fechar circuito (ON)"
st.sidebar.button(btn_label, use_container_width=True, on_click=toggle_switch, key="btn_switch")
st.sidebar.write(f"**Estado:** {'ON (fechado)' if st.session_state['sw'] else 'OFF (aberto)'}")

# Valores finais
Vsrc = float(st.session_state["V_slider"])
R = float(st.session_state["R_slider"])
sw = bool(st.session_state["sw"])

# ---------------------------
# Modelo elétrico
# ---------------------------
if sw:
    I = Vsrc / R if R > 0 else 0.0  # A
    V_R = Vsrc
else:
    I = 0.0
    V_R = 0.0

I_mA = I * 1000.0

# ---------------------------
# Layout principal
# ---------------------------
left, right = st.columns([1.35, 1.0], gap="large")

# ---------------------------
# Circuito (SVG) - fontes bem grandes + resistor com borda amarela grossa
# ---------------------------
with left:
    st.markdown("## Circuito (visual)")

    # Comprimento do resistor cresce com R (1000..1300)
    r_norm = (R - R_MIN) / (R_MAX - R_MIN) if R_MAX > R_MIN else 0.0
    r_norm = float(np.clip(r_norm, 0.0, 1.0))
    base_len = 340
    extra = int(260 * r_norm)
    res_len = base_len + extra

    wire_color = "#22c55e" if sw else "#94a3b8"
    glow_style = "filter: drop-shadow(0px 0px 12px rgba(34,197,94,0.55));" if sw else ""

    # Canvas bem largo (para nunca cortar)
    W, H = 2200, 620
    x0, y0 = 140, 360

    # Interruptor
    x_sw1 = x0 + 330
    x_sw2 = x_sw1 + 140
    arm_x2 = x_sw1 + 88
    arm_y2 = y0 - (52 if not sw else 0)

    # Resistor
    xR1 = x_sw2 + 170
    xR2 = xR1 + res_len

    # Amperímetro
    xA = xR2 + 240
    rA = 44

    # Fechamento
    x_end = xA + 420
    y_bot = y0 + 190

    # Voltímetro (sobre o resistor)
    yV_top = y0 - 200
    vm_w, vm_h = 320, 82
    vm_x = (xR1 + xR2) / 2 - vm_w / 2
    vm_y = yV_top - 110

    # Display corrente
    am_w, am_h = 320, 82
    am_x = xA + 160
    am_y = y0 - 120

    # Textos (3 alg. sig.)
    Vtxt = fmt_sig(Vsrc, 3)
    VRtxt = fmt_sig(V_R, 3)
    Itxt_mA = fmt_sig(I_mA, 3)

    # Fontes maiores (pedido 2)
    fs_title = 30     # labels: FONTE, Voltímetro, Amperímetro
    fs_body = 28      # textos do componente
    fs_mono = 34      # displays numéricos
    fs_small = 24     # textos secundários

    # Resistor com borda amarela grossa (pedido 4)
    resistor_rx = 30
    resistor_stroke_w = 10  # grossa

    svg = f"""
    <div style="background:#0b1220;border-radius:18px;padding:18px;{glow_style}">
      <svg width="100%" height="540" viewBox="0 0 {W} {H}"
           preserveAspectRatio="xMidYMid meet"
           xmlns="http://www.w3.org/2000/svg">

        <!-- fio superior: fonte -> interruptor -->
        <line x1="{x0}" y1="{y0}" x2="{x_sw1}" y2="{y0}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>

        <!-- interruptor -->
        <circle cx="{x_sw1}" cy="{y0}" r="14" fill="#e5e7eb"/>
        <circle cx="{x_sw2}" cy="{y0}" r="14" fill="#e5e7eb"/>
        <line x1="{x_sw1}" y1="{y0}" x2="{arm_x2}" y2="{arm_y2}" stroke="#e5e7eb"
              stroke-width="12" stroke-linecap="round"/>

        <text x="{(x_sw1+x_sw2)/2}" y="{y0-76}" fill="#e5e7eb" font-size="{fs_small}"
              font-family="ui-sans-serif" text-anchor="middle">
          INTERRUPTOR ({'ON' if sw else 'OFF'})
        </text>

        <!-- fio: interruptor -> resistor -->
        <line x1="{x_sw2}" y1="{y0}" x2="{xR1}" y2="{y0}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>

        <!-- resistor (retângulo com cantos arredondados e borda amarela grossa) -->
        <rect x="{xR1}" y="{y0-62}" width="{res_len}" height="124" rx="{resistor_rx}"
              fill="#111827" stroke="#fbbf24" stroke-width="{resistor_stroke_w}"/>

        <text x="{xR1 + res_len/2}" y="{y0-92}" fill="#e5e7eb" font-size="{fs_body}"
              font-family="ui-sans-serif" text-anchor="middle">
          RESISTOR (R = {fmt_sig(R,3)} Ω)
        </text>

        <!-- fio: resistor -> amperímetro -->
        <line x1="{xR2}" y1="{y0}" x2="{xA - rA}" y2="{y0}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>

        <!-- amperímetro -->
        <circle cx="{xA}" cy="{y0}" r="{rA}" fill="#0f172a" stroke="#10b981" stroke-width="4"/>
        <text x="{xA}" y="{y0+12}" fill="#86efac" font-size="{fs_mono}"
              font-family="ui-monospace" text-anchor="middle">A</text>

        <!-- fio: amperímetro -> final -->
        <line x1="{xA + rA}" y1="{y0}" x2="{x_end}" y2="{y0}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>

        <!-- retorno inferior -->
        <line x1="{x_end}" y1="{y0}" x2="{x_end}" y2="{y_bot}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>
        <line x1="{x_end}" y1="{y_bot}" x2="{x0}" y2="{y_bot}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>
        <line x1="{x0}" y1="{y_bot}" x2="{x0}" y2="{y0}" stroke="{wire_color}"
              stroke-width="14" stroke-linecap="round"/>

        <!-- fonte -->
        <rect x="{x0-92}" y="{y0-140}" width="184" height="280" rx="30"
              fill="#111827" stroke="#334155" stroke-width="3.2"/>
        <text x="{x0}" y="{y0-84}" fill="#e5e7eb" font-size="{fs_title}"
              font-family="ui-sans-serif" text-anchor="middle">FONTE</text>
        <rect x="{x0-64}" y="{y0-22}" width="128" height="62" rx="16"
              fill="#0f172a" stroke="#475569" stroke-width="2.6"/>
        <text x="{x0}" y="{y0+22}" fill="#38bdf8" font-size="{
