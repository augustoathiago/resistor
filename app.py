import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

# ---------------------------
# Constantes fixas do simulador
# ---------------------------
V_MAX = 30.0           # tensão máxima (V) e limite superior do eixo Y
R_MIN = 100.0         # resistência mínima (Ω)
R_MAX = 1300.0         # resistência máxima (Ω)
X_MAX_mA = 40.0        # limite do eixo X (mA)

# Gráfico com tamanho fixo (não responsivo)
CHART_WIDTH = 980
CHART_HEIGHT = 360

st.set_page_config(
    page_title="Simulador Resistor Física 2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Formatação: 3 algarismos significativos
# ---------------------------
def fmt_sig(x: float, sig: int = 3) -> str:
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

# ---------------------------
# Modelo elétrico
# ---------------------------
Vsrc = float(st.session_state["V_slider"])
R = float(st.session_state["R_slider"])
sw = bool(st.session_state["sw"])

if sw:
    I = Vsrc / R if R > 0 else 0.0  # A
    V_R = Vsrc
else:
    I = 0.0
    V_R = 0.0

I_mA = I * 1000.0

# ---------------------------
# Layout: circuito em cima, gráfico embaixo
# ---------------------------
st.markdown("## Circuito (visual)")

# ---------------------------
# Circuito (SVG) - viewBox dinâmico para não cortar
# ---------------------------
r_norm = (R - R_MIN) / (R_MAX - R_MIN) if R_MAX > R_MIN else 0.0
r_norm = float(np.clip(r_norm, 0.0, 1.0))

# Tamanho do resistor (controlado para não explodir)
base_len = 520
extra = int(260 * r_norm)
res_len = base_len + extra

wire_color = "#22c55e" if sw else "#94a3b8"
glow_style = "filter: drop-shadow(0px 0px 12px rgba(34,197,94,0.55));" if sw else ""

# Geometria base
H = 720
x0, y0 = 200, 430

# Fonte
src_w, src_h = 240, 340
src_x = x0 - (src_w // 2)
src_y = y0 - (src_h // 2)

# Interruptor (mais comprido e fecha no ON)
x_sw1 = x0 + 430
gap_sw = 240
x_sw2 = x_sw1 + gap_sw

arm_x2_on = x_sw2
arm_y2_on = y0
arm_x2_off = x_sw1 + int(gap_sw * 0.70)
arm_y2_off = y0 - 95

# Resistor
xR1 = x_sw2 + 260
xR2 = xR1 + res_len

# Amperímetro (símbolo em série)
xA = xR2 + 280
rA = 62

# Display do amperímetro (bem à direita)
am_w, am_h = 420, 110
am_x = xA + 220
am_y = y0 - 160

# Fim do fio superior e retorno
x_end = xA + 520
y_bot = y0 + 240

# Voltímetro (fios antes/depois do resistor)
yV_top = y0 - 255
vm_w, vm_h = 420, 110
vm_x = (xR1 + xR2) / 2 - vm_w / 2
vm_y = yV_top - 160

# ✅ Largura dinâmica do viewBox (para não cortar à direita)
rightmost = max(x_end, am_x + am_w, xR2 + 80)
W = int(rightmost + 260)  # margem final

# Fontes (grandes)
fs_title = 44
fs_body = 40
fs_mono = 46
fs_small = 34

Vtxt = fmt_sig(Vsrc, 3)
VRtxt = fmt_sig(V_R, 3)
Itxt = fmt_sig(I_mA, 3)

# Resistor com borda amarela grossa
resistor_rx = 44
resistor_stroke_w = 16

# Posições de texto
res_label_y = y0 - 135
sw_label_y = y0 - 130

arm_x2 = arm_x2_on if sw else arm_x2_off
arm_y2 = arm_y2_on if sw else arm_y2_off

svg = f"""
<div style="background:#0b1220;border-radius:18px;padding:18px;{glow_style}">
  <svg width="100%" height="560" viewBox="0 0 {W} {H}"
       preserveAspectRatio="xMinYMid meet"
       xmlns="http://www.w3.org/2000/svg">

    <!-- fio superior: fonte -> interruptor -->
    <line x1="{x0}" y1="{y0}" x2="{x_sw1}" y2="{y0}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>

    <!-- interruptor: pinos -->
    <circle cx="{x_sw1}" cy="{y0}" r="18" fill="#e5e7eb"/>
    <circle cx="{x_sw2}" cy="{y0}" r="18" fill="#e5e7eb"/>

    <!-- interruptor: braço (fecha no ON) -->
    <line x1="{x_sw1}" y1="{y0}" x2="{arm_x2}" y2="{arm_y2}"
          stroke="#e5e7eb" stroke-width="16" stroke-linecap="round"/>

    <text x="{(x_sw1+x_sw2)/2}" y="{sw_label_y}" fill="#e5e7eb"
          font-size="{fs_small}" font-family="ui-sans-serif" text-anchor="middle">
      INTERRUPTOR ({'ON' if sw else 'OFF'})
    </text>

    <!-- fio: interruptor -> resistor -->
    <line x1="{x_sw2}" y1="{y0}" x2="{xR1}" y2="{y0}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>

    <!-- resistor -->
    <rect x="{xR1}" y="{y0-90}" width="{res_len}" height="180" rx="{resistor_rx}"
          fill="#111827" stroke="#fbbf24" stroke-width="{resistor_stroke_w}"/>

    <text x="{xR1 + res_len/2}" y="{res_label_y}" fill="#e5e7eb"
          font-size="{fs_body}" font-family="ui-sans-serif" text-anchor="middle">
      RESISTOR (R = {fmt_sig(R,3)} Ω)
    </text>

    <!-- fio: resistor -> amperímetro -->
    <line x1="{xR2}" y1="{y0}" x2="{xA - rA}" y2="{y0}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>

    <!-- amperímetro (símbolo em série) -->
    <circle cx="{xA}" cy="{y0}" r="{rA}" fill="#0f172a" stroke="#10b981" stroke-width="5"/>
    <text x="{xA}" y="{y0+16}" fill="#86efac"
          font-size="{fs_mono}" font-family="ui-monospace" text-anchor="middle">A</text>

    <!-- fio: amperímetro -> final -->
    <line x1="{xA + rA}" y1="{y0}" x2="{x_end}" y2="{y0}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>

    <!-- retorno inferior -->
    <line x1="{x_end}" y1="{y0}" x2="{x_end}" y2="{y_bot}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>
    <line x1="{x_end}" y1="{y_bot}" x2="{x0}" y2="{y_bot}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>
    <line x1="{x0}" y1="{y_bot}" x2="{x0}" y2="{y0}"
          stroke="{wire_color}" stroke-width="18" stroke-linecap="round"/>

    <!-- fonte -->
    <rect x="{src_x}" y="{src_y}" width="{src_w}" height="{src_h}" rx="44"
          fill="#111827" stroke="#334155" stroke-width="4"/>
    <text x="{x0}" y="{src_y + 85}" fill="#e5e7eb"
          font-size="{fs_title}" font-family="ui-sans-serif" text-anchor="middle">FONTE</text>

    <rect x="{x0-90}" y="{y0-28}" width="180" height="86" rx="22"
          fill="#0f172a" stroke="#475569" stroke-width="3"/>
    <text x="{x0}" y="{y0+32}" fill="#38bdf8"
          font-size="{fs_mono}" font-family="ui-monospace" text-anchor="middle">{Vtxt} V</text>

    <!-- voltímetro (fios antes e depois do resistor) -->
    <line x1="{xR1}" y1="{y0}" x2="{xR1}" y2="{yV_top}" stroke="#a78bfa" stroke-width="7"/>
    <line x1="{xR2}" y1="{y0}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="7"/>
    <line x1="{xR1}" y1="{yV_top}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="7"/>

    <text x="{(xR1+xR2)/2}" y="{vm_y-18}" fill="#e5e7eb"
          font-size="{fs_title}" font-family="ui-sans-serif" text-anchor="middle">Voltímetro</text>

    <rect x="{vm_x}" y="{vm_y}" width="{vm_w}" height="{vm_h}" rx="22"
          fill="#0f172a" stroke="#7c3aed" stroke-width="4"/>
    <text x="{vm_x + vm_w/2}" y="{vm_y + 72}" fill="#c4b5fd"
          font-size="{fs_mono}" font-family="ui-monospace" text-anchor="middle">
      V<tspan baseline-shift="sub" font-size="{fs_body}">R</tspan> = {VRtxt} V
    </text>

    <!-- amperímetro (display) -->
    <text x="{am_x + am_w/2}" y="{am_y-18}" fill="#e5e7eb"
          font-size="{fs_title}" font-family="ui-sans-serif" text-anchor="middle">Amperímetro</text>
    <rect x="{am_x}" y="{am_y}" width="{am_w}" height="{am_h}" rx="22"
          fill="#0f172a" stroke="#10b981" stroke-width="4"/>
    <text x="{am_x + am_w/2}" y="{am_y + 72}" fill="#86efac"
          font-size="{fs_mono}" font-family="ui-monospace" text-anchor="middle">
      I = {Itxt} mA
    </text>
  </svg>
</div>
"""
st.components.v1.html(svg, height=600)

# ---------------------------
# Gráfico com eixos e tamanho totalmente fixos
#  - X: 0..40 (2 em 2)
#  - Y: 0..30 (5 em 5)
#  - sem clamp
#  - reta para ao chegar em 30 V (NaN acima de 30)
# ---------------------------
st.markdown("## Gráfico: Tensão × Corrente (V×I)")

I_line_mA = np.linspace(0.0, X_MAX_mA, 401)
V_line = R * (I_line_mA / 1000.0)

# ✅ não achata: corta a reta quando passar de 30 V
V_line_plot = np.where(V_line <= V_MAX + 1e-9, V_line, np.nan)

df_line = pd.DataFrame({"corrente_mA": I_line_mA, "tensao_V": V_line_plot})
df_point = pd.DataFrame({"corrente_mA": [I_mA], "tensao_V": [V_R]})

x_ticks = list(range(0, 41, 2))
y_ticks = list(range(0, 31, 5))

base = alt.Chart(df_line).encode(
    x=alt.X(
        "corrente_mA:Q",
        title="Corrente (mA)",
        scale=alt.Scale(domain=[0, X_MAX_mA], nice=False),
        axis=alt.Axis(values=x_ticks, grid=True, labelFontSize=14, titleFontSize=16),
    ),
    y=alt.Y(
        "tensao_V:Q",
        title="Tensão (V)",
        scale=alt.Scale(domain=[0, V_MAX], nice=False),
        axis=alt.Axis(values=y_ticks, grid=True, labelFontSize=14, titleFontSize=16),
    ),
)

line = base.mark_line()
point_color = "#ef4444" if sw else "#64748b"
point = alt.Chart(df_point).mark_point(size=180, filled=True).encode(
    x="corrente_mA:Q",
    y="tensao_V:Q",
    color=alt.value(point_color),
)

chart = (line + point).properties(
    width=CHART_WIDTH,
    height=CHART_HEIGHT,
    padding={"left": 70, "right": 25, "top": 20, "bottom": 60},
).configure_view(
    strokeWidth=0
).configure_axis(
    tickSize=6
)

# ✅ não responsivo: tamanho nunca muda
st.altair_chart(chart, use_container_width=False)

# ---------------------------
# Leituras (símbolo embaixo do nome)
# ---------------------------
st.markdown("### Leituras")

I_txt = f"{fmt_sig(I_mA,3)} mA"
VR_txt = f"{fmt_sig(V_R,3)} V"
R_txt = f"{fmt_sig(R,3)} Ω"

def leitura_card(nome: str, simbolo_html: str, valor: str):
    st.markdown(
        f"""
        <div style="line-height:1.05;">
          <div style="font-weight:700;">{nome}</div>
          <div style="opacity:0.9; font-weight:700; margin-top:2px;">{simbolo_html}</div>
          <div style="font-size:30px;font-weight:900;margin-top:8px;">{valor}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

c1, c2, c3 = st.columns(3)
with c1:
    leitura_card("Corrente", "I", I_txt)
with c2:
    leitura_card("Tensão do resistor", "<span style='white-space:nowrap;'>V<sub>R</sub></span>", VR_txt)
with c3:
    leitura_card("Resistência", "R", R_txt)
