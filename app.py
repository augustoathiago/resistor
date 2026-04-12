import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

# ---------------------------
# Configurações fixas (sem controles de limites na UI)
# ---------------------------
V_MAX = 30.0      # faixa do slider da fonte
R_MIN = 10.0      # faixa do slider do resistor
R_MAX = 2000.0

st.set_page_config(
    page_title="Simulador Resistor Física 2",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------
# Helpers
# ---------------------------
def _sync(key_from: str, key_to: str):
    """Sincroniza valores entre slider e campo digitável."""
    st.session_state[key_to] = st.session_state[key_from]

def fmt_current(I):
    if I < 1:
        return f"{I*1000:.2f} mA"
    return f"{I:.4f} A"

def fmt_voltage(V):
    return f"{V:.2f} V"

def clamp(x, a, b):
    return max(a, min(b, x))

# ---------------------------
# Estado inicial
# ---------------------------
if "V_slider" not in st.session_state:
    st.session_state.V_slider = 5.0
if "V_input" not in st.session_state:
    st.session_state.V_input = 5.0

if "R_slider" not in st.session_state:
    st.session_state.R_slider = 220.0
if "R_input" not in st.session_state:
    st.session_state.R_input = 220.0

if "sw" not in st.session_state:
    st.session_state.sw = True

# ---------------------------
# Cabeçalho (logo + título + descrição)
# ---------------------------
top_left, top_right = st.columns([0.18, 0.82], vertical_alignment="center")
with top_left:
    # Se o arquivo não existir, o app continua sem quebrar
    try:
        st.image("logo_maua.png", use_container_width=True)
    except Exception:
        st.empty()

with top_right:
    st.title("Simulador Resistor Física 2")
    st.write("Estude o comportamento de um resistor em um circuito simples.")

st.divider()

# ---------------------------
# Sidebar: controles (somente fonte e resistor + botão do interruptor)
# ---------------------------
st.sidebar.title("Controles")

st.sidebar.subheader("Fonte (tensão)")
cV1, cV2 = st.sidebar.columns([1, 1], gap="small")
with cV1:
    st.slider(
        "V (slider)",
        min_value=0.0,
        max_value=float(V_MAX),
        value=float(st.session_state.V_slider),
        step=0.1,
        key="V_slider",
        on_change=_sync,
        args=("V_slider", "V_input"),
        label_visibility="collapsed",
    )
with cV2:
    st.number_input(
        "V (digite)",
        min_value=0.0,
        max_value=float(V_MAX),
        value=float(st.session_state.V_input),
        step=0.1,
        key="V_input",
        on_change=_sync,
        args=("V_input", "V_slider"),
        label_visibility="collapsed",
    )

st.sidebar.subheader("Resistor (resistência)")
cR1, cR2 = st.sidebar.columns([1, 1], gap="small")
with cR1:
    st.slider(
        "R (slider)",
        min_value=float(R_MIN),
        max_value=float(R_MAX),
        value=float(st.session_state.R_slider),
        step=1.0,
        key="R_slider",
        on_change=_sync,
        args=("R_slider", "R_input"),
        label_visibility="collapsed",
    )
with cR2:
    st.number_input(
        "R (digite)",
        min_value=float(R_MIN),
        max_value=float(R_MAX),
        value=float(st.session_state.R_input),
        step=1.0,
        key="R_input",
        on_change=_sync,
        args=("R_input", "R_slider"),
        label_visibility="collapsed",
    )

st.sidebar.subheader("Interruptor")
btn_label = "Abrir circuito (OFF)" if st.session_state.sw else "Fechar circuito (ON)"
if st.sidebar.button(btn_label, use_container_width=True):
    st.session_state.sw = not st.session_state.sw

st.sidebar.write(f"**Estado:** {'ON (fechado)' if st.session_state.sw else 'OFF (aberto)'}")

# Valores finais (sincronizados)
Vsrc = float(st.session_state.V_slider)
R = float(st.session_state.R_slider)
sw = bool(st.session_state.sw)

# ---------------------------
# Modelo elétrico
# ---------------------------
if sw:
    I = Vsrc / R if R > 0 else 0.0
    V_R = Vsrc
else:
    I = 0.0
    V_R = 0.0

# ---------------------------
# Layout principal
# ---------------------------
left, right = st.columns([1.15, 1.0], gap="large")

# ---------------------------
# Circuito (SVG) - ajustado para:
#  - aparecer inteiro
#  - voltímetro ligado antes/depois do resistor (não em cima do componente)
#  - amperímetro com fios aparecendo (inserido em série na linha)
#  - remover textos indesejados (dica/potência)
# ---------------------------
with left:
    st.markdown("## Circuito (visual)")

    # Resistor muda de tamanho com R (escala log suave)
    r_norm = (np.log10(R) - np.log10(R_MIN)) / (np.log10(R_MAX) - np.log10(R_MIN))
    r_norm = float(np.clip(r_norm, 0.0, 1.0))
    base_len = 120
    extra = int(220 * r_norm)
    res_len = base_len + extra

    # Cores
    wire_color = "#22c55e" if sw else "#94a3b8"
    glow_style = "filter: drop-shadow(0px 0px 7px rgba(34,197,94,0.55));" if sw else ""

    # Dimensões e coordenadas (viewBox amplo para não cortar)
    W, H = 980, 400
    x0, y0 = 100, 210

    # Segmento até o interruptor
    x_sw1 = x0 + 210
    x_sw2 = x_sw1 + 85

    # Resistor
    xR1 = x_sw2 + 80            # ponto antes do resistor (no fio)
    xR2 = xR1 + res_len          # ponto depois do resistor (no fio)

    # Amperímetro (em série após o resistor)
    xA = xR2 + 120
    rA = 26

    # Fechamento do circuito
    x_end = xA + 180
    y_bot = y0 + 120

    # Interruptor (braço)
    arm_x2 = x_sw1 + 55
    arm_y2 = y0 - (28 if not sw else 0)

    # Voltímetro (conecta ANTES e DEPOIS do resistor)
    yV_top = y0 - 110
    vm_w, vm_h = 150, 40
    vm_x = (xR1 + xR2) / 2 - vm_w / 2
    vm_y = yV_top - 52

    Vtxt = fmt_voltage(Vsrc)
    Itxt = fmt_current(I)
    VRtxt = fmt_voltage(V_R)

    # Amperímetro display
    am_w, am_h = 140, 40
    am_x = xA + 55
    am_y = y0 - 58

    svg = f"""
    <div style="background:#0b1220;border-radius:18px;padding:16px;{glow_style}">
      <svg width="100%" height="360" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet"
           xmlns="http://www.w3.org/2000/svg">

        <!-- Fios (superior) até fonte->interruptor -->
        <line x1="{x0}" y1="{y0}" x2="{x_sw1}" y2="{y0}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>

        <!-- Interruptor (pinos) -->
        <circle cx="{x_sw1}" cy="{y0}" r="9" fill="#e5e7eb"/>
        <circle cx="{x_sw2}" cy="{y0}" r="9" fill="#e5e7eb"/>

        <!-- Interruptor (braço) -->
        <line x1="{x_sw1}" y1="{y0}" x2="{arm_x2}" y2="{arm_y2}" stroke="#e5e7eb"
              stroke-width="7" stroke-linecap="round"/>

        <text x="{(x_sw1+x_sw2)/2}" y="{y0-40}" fill="#e5e7eb" font-size="12"
              font-family="ui-sans-serif" text-anchor="middle">
          INTERRUPTOR ({'ON' if sw else 'OFF'})
        </text>

        <!-- Fio entre interruptor e resistor -->
        <line x1="{x_sw2}" y1="{y0}" x2="{xR1}" y2="{y0}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>

        <!-- Resistor (retângulo central) -->
        <rect x="{xR1}" y="{y0-34}" width="{res_len}" height="68" rx="18"
              fill="#111827" stroke="#64748b" stroke-width="2"/>
        <path d="M {xR1+22} {y0}
                 l 22 -16 l 22 32 l 22 -32 l 22 32 l 22 -32 l 22 32 l 22 -16"
              fill="none" stroke="#fbbf24" stroke-width="3.6" stroke-linejoin="round"/>
        <text x="{xR1 + res_len/2}" y="{y0-52}" fill="#e5e7eb" font-size="12"
              font-family="ui-sans-serif" text-anchor="middle">
          RESISTOR (R = {R:.1f} Ω)
        </text>

        <!-- Fio após o resistor até o amperímetro -->
        <line x1="{xR2}" y1="{y0}" x2="{xA - rA}" y2="{y0}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>

        <!-- Amperímetro (em série) -->
        <circle cx="{xA}" cy="{y0}" r="{rA}" fill="#0f172a" stroke="#10b981" stroke-width="2.5"/>
        <text x="{xA}" y="{y0+5}" fill="#86efac" font-size="14" font-family="ui-monospace" text-anchor="middle">A</text>

        <!-- Fio após o amperímetro até o final (superior) -->
        <line x1="{xA + rA}" y1="{y0}" x2="{x_end}" y2="{y0}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>

        <!-- Retorno inferior -->
        <line x1="{x_end}" y1="{y0}" x2="{x_end}" y2="{y_bot}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>
        <line x1="{x_end}" y1="{y_bot}" x2="{x0}" y2="{y_bot}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>
        <line x1="{x0}" y1="{y_bot}" x2="{x0}" y2="{y0}" stroke="{wire_color}" stroke-width="8" stroke-linecap="round"/>

        <!-- Fonte -->
        <rect x="{x0-55}" y="{y0-75}" width="110" height="150" rx="18"
              fill="#111827" stroke="#334155" stroke-width="2"/>
        <text x="{x0}" y="{y0-40}" fill="#e5e7eb" font-size="13"
              font-family="ui-sans-serif" text-anchor="middle">FONTE</text>
        <rect x="{x0-38}" y="{y0-12}" width="76" height="34" rx="10"
              fill="#0f172a" stroke="#475569" stroke-width="1.5"/>
        <text x="{x0}" y="{y0+12}" fill="#38bdf8" font-size="15"
              font-family="ui-monospace" text-anchor="middle">{Vtxt}</text>

        <!-- Voltímetro: fios antes e depois do resistor -->
        <line x1="{xR1}" y1="{y0}" x2="{xR1}" y2="{yV_top}" stroke="#a78bfa" stroke-width="3.5"/>
        <line x1="{xR2}" y1="{y0}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="3.5"/>
        <line x1="{xR1}" y1="{yV_top}" x2="{xR2}" y2="{yV_top}" stroke="#a78bfa" stroke-width="3.5"/>

        <rect x="{vm_x}" y="{vm_y}" width="{vm_w}" height="{vm_h}" rx="12"
              fill="#0f172a" stroke="#7c3aed" stroke-width="1.8"/>
        <text x="{vm_x + vm_w/2}" y="{vm_y + 26}" fill="#c4b5fd"
              font-size="14" font-family="ui-monospace" text-anchor="middle">
          V_R = {VRtxt}
        </text>

        <!-- Display da corrente (próximo ao amperímetro) -->
        <rect x="{am_x}" y="{am_y}" width="{am_w}" height="{am_h}" rx="12"
              fill="#0f172a" stroke="#10b981" stroke-width="1.8"/>
        <text x="{am_x + am_w/2}" y="{am_y + 26}" fill="#86efac"
              font-size="14" font-family="ui-monospace" text-anchor="middle">
          I = {Itxt}
        </text>
      </svg>
    </div>
    """
    st.components.v1.html(svg, height=390)


# ---------------------------
# Gráfico V × I
# Correção do "às vezes não aparece":
#  - domínio sempre válido (Imax nunca 0)
#  - linha sempre com pelo menos 2 pontos e sem NaN
# ---------------------------
with right:
    st.markdown("## Gráfico: Tensão × Corrente (V×I)")

    # Domínios robustos
    # I máximo teórico para a faixa do app: V_MAX / R_MIN
    Imax_theoretical = V_MAX / R_MIN
    Imax = max(0.05, Imax_theoretical)  # nunca zero

    # Linhas e ponto
    I_line = np.linspace(0.0, Imax, 250)
    V_line = R * I_line

    # Se por algum motivo aparecer NaN (não deve), limpa
    mask = np.isfinite(I_line) & np.isfinite(V_line)
    df_line = pd.DataFrame({"corrente": I_line[mask], "tensao": V_line[mask]})

    df_point = pd.DataFrame({"corrente": [I], "tensao": [V_R]})

    # Chart
    base = alt.Chart(df_line).encode(
        x=alt.X("corrente:Q", title="Corrente (A)", scale=alt.Scale(domain=[0, Imax])),
        y=alt.Y("tensao:Q", title="Tensão (V)", scale=alt.Scale(domain=[0, V_MAX])),
    )

    line = base.mark_line().properties()

    point_color = "#ef4444" if sw else "#64748b"
    point = alt.Chart(df_point).mark_point(size=170, filled=True).encode(
        x="corrente:Q",
        y="tensao:Q",
        color=alt.value(point_color),
        tooltip=[
            alt.Tooltip("corrente:Q", title="I (A)", format=".6f"),
            alt.Tooltip("tensao:Q", title="V_R (V)", format=".2f"),
        ],
    )

    st.altair_chart((line + point).properties(height=350), use_container_width=True)

    st.markdown("### Leituras")
    c1, c2, c3 = st.columns(3)
    c1.metric("Corrente (I)", fmt_current(I))
    c2.metric("Tensão no resistor (V_R)", fmt_voltage(V_R))
    c3.metric("Resistência (R)", f"{R:.1f} Ω")
