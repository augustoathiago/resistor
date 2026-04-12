import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

# ---------------------------
# Constantes
# ---------------------------
V_MAX = 30.0        # Eixo Y fixo 0..30 V e slider da fonte 0..30
R_MIN = 1000.0      # (pedido) 1000..2000 Ω
R_MAX = 2000.0
X_MAX_mA = 40.0     # (pedido) eixo X fixo 0..40 mA

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

def fmt_V(x: float) -> str:
    return f"{fmt_sig(x, 3)} V"

def fmt_R(x: float) -> str:
    return f"{fmt_sig(x, 3)} Ω"

def fmt_mA(I_A: float) -> str:
    return f"{fmt_sig(I_A * 1000.0, 3)} mA"

# ---------------------------
# Sincronização slider <-> input
# ---------------------------
def sync(from_key: str, to_key: str):
    st.session_state[to_key] = st.session_state[from_key]

def toggle_switch():
    st.session_state["sw"] = not st.session_state.get("sw", True)

# ---------------------------
# Estado inicial (valores dentro do intervalo 1000..2000)
# ---------------------------
if "V_slider" not in st.session_state:
    st.session_state["V_slider"] = 5.0
if "V_input" not in st.session_state:
    st.session_state["V_input"] = 5.0

if "R_slider" not in st.session_state:
    st.session_state["R_slider"] = 1500.0
if "R_input" not in st.session_state:
    st.session_state["R_input"] = 1500.0

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
st.sidebar.button(
    btn_label,
    use_container_width=True,
    on_click=toggle_switch,
    key="btn_switch",
)
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
left, right = st.columns([1.25, 1.0], gap="large")

# ---------------------------
# Circuito (SVG) - fontes bem maiores
# ---------------------------
with left:
    st.markdown("## Circuito (visual)")

    # Comprimento do resistor cresce com R (intervalo 1000..2000)
    r_norm = (R - R_MIN) / (R_MAX - R_MIN) if R_MAX > R_MIN else 0.0
    r_norm = float(np.clip(r_norm, 0.0, 1.0))
    base_len = 260
    extra = int(260 * r_norm)
    res_len = base_len + extra

    wire_color = "#22c55e" if sw else "#94a3b8"
    glow_style = "filter: drop-shadow(0px 0px 10px rgba(34,197,94,0.55));" if sw else ""

    # Canvas bem largo para não cortar (mesmo com resistor grande)
    W, H = 1900, 560
    x0, y0 = 130, 320

    # Interruptor
    x_sw1 = x0 + 300
    x_sw2 = x_sw1 + 120
    arm_x2 = x_sw1 + 76
    arm_y2 = y0 - (42 if not sw else 0)

    # Resistor
    xR1 = x_sw2 + 140
    xR2 = xR1 + res_len

    # Amperímetro
    xA = xR2 + 200
    rA = 36

    # Fechamento
    x_end = xA + 320
    y_bot = y0 + 170

    # Voltímetro
    yV_top = y0 - 170
    vm_w, vm_h = 260, 64
    vm_x = (xR1 + xR2) / 2 - vm_w / 2
    vm_y = yV_top - 90

    # Display corrente + rótulo
    am_w, am_h = 260, 64
    am_x = xA + 120
    am_y = y0 - 95

    # Textos (3 alg. sig.)
    Vtxt = fmt_sig(Vsrc, 3)
    VRtxt = fmt_sig(V_R, 3)
    Itxt_mA = fmt_sig(I_mA, 3)

    # Resistor como linha amarela grossa
    resistor_line_y = y0
    resistor_line_x1 = xR1 + 22
    resistor_line_x2 = xR2 - 22

    # Fontes grandes (pedido)
    fs_title = 22     # labels gerais (FONTE, Voltímetro, Amperímetro)
    fs_body = 20      # textos principais
    fs_mono = 24      # displays numéricos
    fs_small = 18     # textos secundários

    svg = f"""
    <div style="background:#0b1220;border-radius:18px;padding:18px;{glow_style}">
      <svg width="100%" height="520" viewBox="0 0 {W} {H}"
           preserveAspectRatio="xMidYMid meet"
           xmlns="http://www.w3.org/2000/svg">

        <!-- fio superior: fonte -> interruptor -->
        <line x1="{x0}" y1="{y0}" x2="{x_sw1}" y2="{y0}" stroke="{wire_color}" stroke-width="12" stroke-linecap="round"/>

        <!-- interruptor: pinos -->
        <circle cx="{x_sw1}" cy="{y0}" r="12" fill="#e5e7eb"/>
        <circle cx="{x_sw2}" cy="{y0}" r="12" fill="#e5e7eb"/>

        <!-- interruptor: braço -->
        <line x1="{x_sw1}" y1="{y0}" x2="{arm_x2}" y2="{arm_y2}"
              stroke="#e5e7eb" stroke-width="10" stroke-linecap="round"/>

        <text x="{(x_sw1+x_sw2)/2}" y="{y0-62}" fill="#e5e7eb" font-size="{fs_small}"
              font-family="ui-sans-serif" text-anchor="middle">
          INTERRUPTOR ({'ON' if sw else 'OFF'})
        </text>

        <!-- fio: interruptor -> resistor -->
        <line x1="{x_sw2}" y1="{y0}" x2="{xR1}" y2="{y0}" stroke="{wire_color}" stroke-width="12" stroke-linecap="round"/>

        <!-- corpo do resistor -->
        <rect x="{xR1}" y="{y0-52}" width="{res_len}" height="104" rx="26"
              fill="#111827" stroke="#64748b" stroke-width="3"/>

        <!-- resistor como linha amarela grossa -->
        <line x1="{resistor_line_x1}" y1="{resistor_line_y}" x2="{resistor_line_x2}" y2="{resistor_line_y}"
