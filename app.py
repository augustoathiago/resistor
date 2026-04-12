import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

# ---------------------------
# Constantes
# ---------------------------
V_MAX = 30.0           # eixo Y fixo 0..30 V
R_MIN = 1000.0         # resistência 1000..1300 Ω
R_MAX = 1300.0
X_MAX_mA = 40.0        # eixo X fixo 0..40 mA

# Gráfico com tamanho FIXO
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
# Cabeçalho
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
# (Opcional) Circuito em cima - mantido como estava (resumido)
# ---------------------------
st.markdown("## Circuito (visual)")
st.info("Circuito mantido como na versão anterior. (Se quiser, eu colo aqui também a parte do SVG com o viewBox dinâmico.)")

# ---------------------------
# Gráfico embaixo — FIXO (e sem “achatamento” no topo)
# ---------------------------
st.markdown("## Gráfico: Tensão × Corrente (V×I)")

# Linha teórica: V = R * I
I_line_mA = np.linspace(0.0, X_MAX_mA, 401)
V_line = R * (I_line_mA / 1000.0)

# ✅ Truque para NÃO “achatar”: quando passar de 30 V, vira NaN (a linha para)
V_line_plot = np.where(V_line <= V_MAX + 1e-9, V_line, np.nan)

df_line = pd.DataFrame({"corrente_mA": I_line_mA, "tensao_V": V_line_plot})
df_point = pd.DataFrame({"corrente_mA": [I_mA], "tensao_V": [V_R]})

x_ticks = list(range(0, 41, 2))   # 0..40 de 2 em 2
y_ticks = list(range(0, 31, 5))   # 0..30 de 5 em 5

base = alt.Chart(df_line).encode(
    x=alt.X(
        "corrente_mA:Q",
        title="Corrente (mA)",
        scale=alt.Scale(domain=[0, X_MAX_mA], nice=False),   # ✅ sem clamp
        axis=alt.Axis(values=x_ticks, grid=True, labelFontSize=14, titleFontSize=16),
    ),
    y=alt.Y(
        "tensao_V:Q",
        title="Tensão (V)",
        scale=alt.Scale(domain=[0, V_MAX], nice=False),      # ✅ sem clamp
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

# ✅ Tamanho e eixos NÃO mudam
st.altair_chart(chart, use_container_width=False)

# ---------------------------
# Leituras
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
