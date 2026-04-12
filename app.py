import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
import math

# ---------------------------
# Constantes (sem controles de limites)
# ---------------------------
V_MAX = 30.0      # slider tensão
R_MIN = 10.0      # slider resistência
R_MAX = 2000.0

st.set_page_config(
    page_title="Simulador Resistor Física 2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Formatação: 3 algarismos significativos (com zeros quando necessário)
# ---------------------------
def fmt_sig(x: float, sig: int = 3) -> str:
    """Formata com 'sig' algarismos significativos, preservando zeros."""
    if x == 0 or abs(x) < 1e-300:
        # 0 com sig dígitos -> "0.00" para sig=3
        return "0." + "0" * (sig - 1)
    ax = abs(x)
    exp = math.floor(math.log10(ax))
    dec = sig - exp - 1
    if dec > 0:
        return f"{x:.{dec}f}"
    # dec <= 0 => arredonda para dezenas/centenas etc.
    rounded = round(x, -dec)
    return f"{rounded:.0f}"

def fmt_V(x: float) -> str:
    return f"{fmt_sig(x, 3)} V"

def fmt_R(x: float) -> str:
    return f"{fmt_sig(x, 3)} Ω"

def fmt_mA(I_A: float) -> str:
    # sempre em mA (pedido)
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
    st.session_state["R_slider"] = 220.0
if "R_input" not in st.session_state:
    st.session_state["R_input"] = 220.0

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
# Sidebar: controles (renomeados)
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
    on_click=toggle_switch,     # ✅ elimina “dois cliques”
    key="btn_switch"
)
st.sidebar.write(f"**Estado:** {'ON (fechado)' if st.session_state['sw'] else 'OFF (aberto)'}")

# Valores finais (sincronizados)
Vsrc = float(st.session_state["V_slider"])
R = float(st.session_state["R_slider"])
sw = bool(st.session_state["sw"])

# ---------------------------
# Modelo elétrico
# ---------------------------
if sw:
    I = Vsrc / R if R > 0 else 0.0   # A
    V_R = Vsrc
else:
    I = 0.0
    V_R = 0.0

# ---------------------------
# Layout principal
# ---------------------------
left, right = st.columns([1.2, 1.0], gap="large")

# ---------------------------
# Circuito (SVG) - agora cabe inteiro (viewBox amplo + altura maior)
#  - voltímetro com fios antes/depois do resistor
#  - amperímetro em série com fios visíveis
#  - V_R com subíndice no SVG
# ---------------------------
with left:
    st.markdown("## Circuito (visual)")

    # Resistor muda de tamanho com R (log suave)
    r_norm = (np.log10(R) - np.log10(R_MIN)) / (np.log10(R_MAX) - np.log10(R_MIN))
    r_norm = float(np.clip(r_norm, 0.0, 1.0))
    base_len = 140
    extra = int(260 * r_norm)
    res_len = base_len + extra

    wire_color = "#22c55e" if sw else "#94a3b8"
    glow_style = "filter: drop-shadow(0px 0px 7px rgba(34,197,94,0.55));" if sw else ""

    # Canvas amplo para nunca cortar
    W, H = 1200, 460

    x0, y0 = 110, 250

    # Interruptor
    x_sw1 = x0 + 240
    x_sw2 = x_sw1 + 95
    arm_x2 = x_sw1 + 60
    arm_y2 = y0 - (32 if not sw else 0)

    # Resistor
    xR1 = x_sw2 + 95
    xR2 = xR1 + res_len

    # Amperímetro em série
    xA = xR2 + 150
    rA = 28

    # Fechamento do circuito
    x_end = xA + 240
    y_bot = y0 + 140

    # Voltímetro
    yV_top = y0 - 130
    vm_w, vm_h = 170, 44
    vm_x = (xR1 + xR2) / 2 - vm_w / 2
    vm_y = yV_top - 62

    # Display da corrente
    am_w, am_h = 165, 44
    am_x = xA + 80
    am_y = y0 - 68

    Vtxt = fmt_sig(Vsrc, 3)
    Itxt = fmt_sig(I * 1000.0, 3)   # mA sempre
    VRtxt = fmt_sig(V_R, 3)

    svg = f"""
    <div style="background:#0b1220;border-radius:18px;padding:16px;{glow_style}">
      <svg width="100%" height="420" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet"
           xmlns="http://www.w3.org/2000/svg">

        <!-- fios superiores: fonte -> interruptor -->
        <line x1="{x0}" y1="{y0}" x2="{x_sw1}" y2="{y0}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>

        <!-- interruptor: pinos -->
        <circle cx="{x_sw1}" cy="{y0}" r="10" fill="#e5e7eb"/>
        <circle cx="{x_sw2}" cy="{y0}" r="10" fill="#e5e7eb"/>

        <!-- interruptor: braço -->
        <line x1="{x_sw1}" y1="{y0}" x2="{arm_x2}" y2="{arm_y2}" stroke="#e5e7eb"
              stroke-width="8" stroke-linecap="round"/>

        <text x="{(x_sw1+x_sw2)/2}" y="{y0-46}" fill="#e5e7eb" font-size="13"
              font-family="ui-sans-serif" text-anchor="middle">
          INTERRUPTOR ({'ON' if sw else 'OFF'})
        </text>

        <!-- fio: interruptor -> resistor -->
        <line x1="{x_sw2}" y1="{y0}" x2="{xR1}" y2="{y0}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>

        <!-- resistor -->
        <rect x="{xR1}" y="{y0-38}" width="{res_len}" height="76" rx="20"
              fill="#111827" stroke="#64748b" stroke-width="2.2"/>
        <path d="M {xR1+26} {y0}
                 l 26 -18 l 26 36 l 26 -36 l 26 36 l 26 -36 l 26 36 l 26 -18"
              fill="none" stroke="#fbbf24" stroke-width="4" stroke-linejoin="round"/>
        <text x="{xR1 + res_len/2}" y="{y0-58}" fill="#e5e7eb" font-size="13"
              font-family="ui-sans-serif" text-anchor="middle">
          RESISTOR (R = {fmt_sig(R,3)} Ω)
        </text>

        <!-- fio: resistor -> amperímetro (até a borda do círculo) -->
        <line x1="{xR2}" y1="{y0}" x2="{xA - rA}" y2="{y0}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>

        <!-- amperímetro -->
        <circle cx="{xA}" cy="{y0}" r="{rA}" fill="#0f172a" stroke="#10b981" stroke-width="3"/>
        <text x="{xA}" y="{y0+6}" fill="#86efac" font-size="15" font-family="ui-monospace" text-anchor="middle">A</text>

        <!-- fio: amperímetro -> final -->
        <line x1="{xA + rA}" y1="{y0}" x2="{x_end}" y2="{y0}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>

        <!-- retorno inferior -->
        <line x1="{x_end}" y1="{y0}" x2="{x_end}" y2="{y_bot}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>
        <line x1="{x_end}" y1="{y_bot}" x2="{x0}" y2="{y_bot}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>
        <line x1="{x0}" y1="{y_bot}" x2="{x0}" y2="{y0}" stroke="{wire_color}" stroke-width="9" stroke-linecap="round"/>

        <!-- fonte -->
        <rect x="{x0-62}" y="{y0-88}" width="124" height="176" rx="20"
              fill="#111827" stroke="#334155" stroke-width="2.2"/>
        <text x="{x0}" y="{y0-48}" fill="#e5e7eb" font-size="14"
              font-family="ui-sans-serif" text-anchor="middle">FONTE</text>
        <rect x="{x0-42}" y="{y0-14}" width="84" height="38" rx="11"
              fill="#0f172a" stroke="#475569" stroke-width="1.7"/>
        <text x="{x0}" y="{y0+14}" fill="#38bdf8" font-size="16"
              font-family="ui-monospace" text-anchor="middle">{Vtxt} V</text>

        <!-- voltímetro: fios antes e depois do resistor -->
        <line x1="{xR1}" y1="{y0}" x2="{xR1}" y2="{yV_top}" stroke="#a78bfa" stroke-width="4"/>
        <line x1="{xR2}" y1="{y0}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="4"/>
        <line x1="{xR1}" y1="{yV_top}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="4"/>

        <rect x="{vm_x}" y="{vm_y}" width="{vm_w}" height="{vm_h}" rx="13"
              fill="#0f172a" stroke="#7c3aed" stroke-width="2"/>

        <!-- "V_R" com subíndice no SVG -->
        <text x="{vm_x + vm_w/2}" y="{vm_y + 28}" fill="#c4b5fd"
              font-size="15" font-family="ui-monospace" text-anchor="middle">
          V<tspan baseline-shift="sub" font-size="12">R</tspan> = {VRtxt} V
        </text>

        <!-- display corrente (sempre mA) -->
        <rect x="{am_x}" y="{am_y}" width="{am_w}" height="{am_h}" rx="13"
              fill="#0f172a" stroke="#10b981" stroke-width="2"/>
        <text x="{am_x + am_w/2}" y="{am_y + 28}" fill="#86efac"
              font-size="15" font-family="ui-monospace" text-anchor="middle">
          I = {Itxt} mA
        </text>
      </svg>
    </div>
    """
    # altura maior para evitar corte em telas menores
    st.components.v1.html(svg, height=460)


# ---------------------------
# Gráfico V × I (robusto + corrente em mA + domínio adaptativo)
# - Evita "sumir" porque agora o eixo x é ajustado para mostrar V até V_MAX
# ---------------------------
with right:
    st.markdown("## Gráfico: Tensão × Corrente (V×I)")

    # Corrente necessária para atingir V_MAX na reta V = R*I:
    # I_at_Vmax = V_MAX / R (em A) => em mA: 1000*V_MAX/R
    I_at_Vmax_mA = 1000.0 * (V_MAX / R)
    I_op_mA = 1000.0 * I

    # eixo x sempre mostra pelo menos até o ponto de operação e até V_MAX (com margem)
    x_max = max(I_at_Vmax_mA, I_op_mA, 1.0) * 1.10  # mínimo 1 mA
    # limita para não ficar absurdo em R muito pequeno (aqui R_MIN=10 => 3000 mA a Vmax)
    x_max = min(x_max, 1000.0 * (V_MAX / R_MIN) * 1.10)

    # dados da reta (em mA)
    I_line_mA = np.linspace(0.0, x_max, 300)
    V_line = R * (I_line_mA / 1000.0)  # V = R * I(A)

    df_line = pd.DataFrame({"corrente_mA": I_line_mA, "tensao_V": V_line})
    df_point = pd.DataFrame({"corrente_mA": [I_op_mA], "tensao_V": [V_R]})

    base = alt.Chart(df_line).encode(
        x=alt.X("corrente_mA:Q", title="Corrente (mA)", scale=alt.Scale(domain=[0, x_max])),
        y=alt.Y("tensao_V:Q", title="Tensão (V)", scale=alt.Scale(domain=[0, V_MAX])),
    )

    line = base.mark_line()

    point_color = "#ef4444" if sw else "#64748b"
    point = alt.Chart(df_point).mark_point(size=180, filled=True).encode(
        x="corrente_mA:Q",
        y="tensao_V:Q",
        color=alt.value(point_color),
        tooltip=[
            alt.Tooltip("corrente_mA:Q", title="I (mA)", format=".3f"),
            alt.Tooltip("tensao_V:Q", title="V_R (V)", format=".3f"),
        ],
    )

    st.altair_chart((line + point).properties(height=350), use_container_width=True)

    # Leituras (sem tensão da fonte, sem potência)
    st.markdown("### Leituras")

    # Valores com 3 algarismos significativos (pedido)
    I_txt = fmt_sig(I_op_mA, 3) + " mA"
    VR_txt = fmt_sig(V_R, 3) + " V"
    R_txt = fmt_sig(R, 3) + " Ω"

    # UI com rótulos + subíndice via LaTeX
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Corrente (I)**")
        st.markdown(f"<div style='font-size:28px;font-weight:700'>{I_txt}</div>", unsafe_allow_html=True)
    with c2:
        st.markdown(r"**Tensão do resistor ($V_R$)**")
        st.markdown(f"<div style='font-size:28px;font-weight:700'>{VR_txt}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("**Resistência (R)**")
        st.markdown(f"<div style='font-size:28px;font-weight:700'>{R_txt}</div>", unsafe_allow_html=True)
