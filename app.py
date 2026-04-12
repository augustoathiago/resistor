import streamlit as st
import numpy as np
import pandas as pd
import altair as alt

st.set_page_config(page_title="Simulação: Fonte + Resistor + Interruptor (V×I)", layout="wide")

# ---------------------------
# Helpers (sincronização slider <-> campo digitável)
# ---------------------------
def _sync(key_from: str, key_to: str):
    st.session_state[key_to] = st.session_state[key_from]

def fmt_current(I):
    if I < 1:
        return f"{I*1000:.2f} mA"
    return f"{I:.4f} A"

def fmt_voltage(V):
    return f"{V:.2f} V"

def fmt_power(P):
    if P < 1:
        return f"{P*1000:.2f} mW"
    return f"{P:.3f} W"


# ---------------------------
# Estado inicial (se necessário)
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
# Sidebar: parâmetros do experimento
# ---------------------------
st.sidebar.title("Controles")

st.sidebar.caption("Ajuste os limites conforme a atividade didática.")
Vmax = st.sidebar.number_input("Tensão máxima da fonte (V)", min_value=1.0, value=24.0, step=1.0)
Rmin = st.sidebar.number_input("Resistência mínima (Ω)", min_value=0.1, value=10.0, step=1.0)
Rmax = st.sidebar.number_input("Resistência máxima (Ω)", min_value=float(Rmin) + 0.1, value=2000.0, step=10.0)

st.sidebar.divider()
st.sidebar.subheader("Fonte (tensão)")

# Slider + campo digitável sincronizados
cV1, cV2 = st.sidebar.columns([1, 1], gap="small")
with cV1:
    st.slider(
        "V (slider)",
        min_value=0.0,
        max_value=float(Vmax),
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
        max_value=float(Vmax),
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
        min_value=float(Rmin),
        max_value=float(Rmax),
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
        min_value=float(Rmin),
        max_value=float(Rmax),
        value=float(st.session_state.R_input),
        step=1.0,
        key="R_input",
        on_change=_sync,
        args=("R_input", "R_slider"),
        label_visibility="collapsed",
    )

st.sidebar.divider()
st.sidebar.subheader("Interruptor")
st.sidebar.toggle("Fechado (ON)", key="sw", value=bool(st.session_state.sw))

# Parâmetros finais (valores já sincronizados)
Vsrc = float(st.session_state.V_slider)
R = float(st.session_state.R_slider)
sw = bool(st.session_state.sw)

# ---------------------------
# Modelo elétrico (fonte ideal + resistor)
# ---------------------------
if sw:
    I = Vsrc / R if R > 0 else 0.0
    V_R = Vsrc
else:
    I = 0.0
    V_R = 0.0

P = V_R * I

# ---------------------------
# Layout principal
# ---------------------------
left, right = st.columns([1.15, 1.0], gap="large")

# ---------------------------
# Desenho do circuito em SVG
# ---------------------------
with left:
    st.markdown("## Circuito (visual)")

    # Resistor cresce com R (escala log para ficar mais “agradável” em ranges grandes)
    # Normaliza R em [0,1] por log
    r_norm = (np.log10(R) - np.log10(Rmin)) / (np.log10(Rmax) - np.log10(Rmin))
    r_norm = float(np.clip(r_norm, 0.0, 1.0))

    base_len = 100
    extra = int(220 * r_norm)   # 0..220 px
    res_len = base_len + extra

    wire_color = "#22c55e" if sw else "#94a3b8"
    glow_style = "filter: drop-shadow(0px 0px 7px rgba(34,197,94,0.55));" if sw else ""

    # Coordenadas
    W, H = 860, 340
    x0, y0 = 90, 185
    x1 = x0 + 180
    x2 = x1 + res_len
    x3 = x2 + 180

    # Switch
    sw_x = x1 - 60
    sw_y = y0
    arm_x2 = sw_x + 48
    arm_y2 = sw_y - (26 if not sw else 0)

    Vtxt = fmt_voltage(Vsrc)
    Itxt = fmt_current(I)
    VRtxt = fmt_voltage(V_R)
    Ptxt = fmt_power(P)

    svg = f"""
    <div style="background:#0b1220;border-radius:18px;padding:16px;{glow_style}">
      <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
        <!-- fios superiores -->
        <line x1="{x0}" y1="{y0}" x2="{sw_x}" y2="{y0}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>
        <line x1="{sw_x+70}" y1="{y0}" x2="{x1}" y2="{y0}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>
        <line x1="{x1}" y1="{y0}" x2="{x2}" y2="{y0}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>
        <line x1="{x2}" y1="{y0}" x2="{x3}" y2="{y0}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>

        <!-- retorno inferior -->
        <line x1="{x3}" y1="{y0}" x2="{x3}" y2="{y0+100}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>
        <line x1="{x3}" y1="{y0+100}" x2="{x0}" y2="{y0+100}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>
        <line x1="{x0}" y1="{y0+100}" x2="{x0}" y2="{y0}" stroke="{wire_color}" stroke-width="7" stroke-linecap="round"/>

        <!-- Fonte -->
        <rect x="{x0-50}" y="{y0-62}" width="100" height="124" rx="16"
              fill="#111827" stroke="#334155" stroke-width="2"/>
        <text x="{x0}" y="{y0-28}" fill="#e5e7eb" font-size="13"
              font-family="ui-sans-serif" text-anchor="middle">FONTE</text>
        <rect x="{x0-36}" y="{y0-10}" width="72" height="32" rx="10"
              fill="#0f172a" stroke="#475569" stroke-width="1.5"/>
        <text x="{x0}" y="{y0+12}" fill="#38bdf8" font-size="15"
              font-family="ui-monospace" text-anchor="middle">{Vtxt}</text>

        <!-- Interruptor -->
        <circle cx="{sw_x}" cy="{sw_y}" r="8" fill="#e5e7eb"/>
        <circle cx="{sw_x+70}" cy="{sw_y}" r="8" fill="#e5e7eb"/>
        <line x1="{sw_x}" y1="{sw_y}" x2="{arm_x2}" y2="{arm_y2}" stroke="#e5e7eb"
              stroke-width="6" stroke-linecap="round"/>
        <text x="{sw_x+35}" y="{sw_y-36}" fill="#e5e7eb" font-size="12"
              font-family="ui-sans-serif" text-anchor="middle">
          INTERRUPTOR ({'ON' if sw else 'OFF'})
        </text>

        <!-- Resistor -->
        <rect x="{x1}" y="{y0-30}" width="{res_len}" height="60" rx="16"
              fill="#111827" stroke="#64748b" stroke-width="2"/>
        <path d="M {x1+18} {y0}
                 l 20 -14 l 20 28 l 20 -28 l 20 28 l 20 -28 l 20 28 l 20 -14"
              fill="none" stroke="#fbbf24" stroke-width="3.3" stroke-linejoin="round"/>
        <text x="{x1 + res_len/2}" y="{y0-44}" fill="#e5e7eb" font-size="12"
              font-family="ui-sans-serif" text-anchor="middle">
          RESISTOR (R = {R:.1f} Ω)
        </text>

        <!-- Voltímetro (paralelo ao resistor) -->
        <line x1="{x1+12}" y1="{y0-30}" x2="{x1+12}" y2="{y0-92}" stroke="#a78bfa" stroke-width="3"/>
        <line x1="{x2-12}" y1="{y0-30}" x2="{x2-12}" y2="{y0-92}" stroke="#a78bfa" stroke-width="3"/>
        <line x1="{x1+12}" y1="{y0-92}" x2="{x2-12}" y2="{y0-92}" stroke="#a78bfa" stroke-width="3"/>
        <rect x="{(x1+x2)/2 - 62}" y="{y0-132}" width="124" height="36" rx="10"
              fill="#0f172a" stroke="#7c3aed" stroke-width="1.5"/>
        <text x="{(x1+x2)/2}" y="{y0-108}" fill="#c4b5fd" font-size="14"
              font-family="ui-monospace" text-anchor="middle">V_R = {VRtxt}</text>

        <!-- Amperímetro (em série, à direita) -->
        <rect x="{x2+40}" y="{y0-54}" width="126" height="36" rx="10"
              fill="#0f172a" stroke="#10b981" stroke-width="1.5"/>
        <text x="{x2+103}" y="{y0-30}" fill="#86efac" font-size="14"
              font-family="ui-monospace" text-anchor="middle">I = {Itxt}</text>

        <!-- Potência (extra) -->
        <text x="{x2+103}" y="{y0+20}" fill="#e5e7eb" font-size="12"
              font-family="ui-monospace" text-anchor="middle">P = {Ptxt}</text>
      </svg>
    </div>
    """
    st.components.v1.html(svg, height=380)

    st.caption("Dica: resistor cresce com R (escala log). Interruptor OFF zera a corrente e o ponto no gráfico vai para (0,0).")


# ---------------------------
# Gráfico V × I (reta e ponto)
# ---------------------------
with right:
    st.markdown("## Gráfico: Tensão × Corrente (V×I)")

    # Limites para o gráfico
    # Imax baseado no pior caso: Vmax / Rmin
    Imax = float(Vmax / Rmin) if Rmin > 0 else 1.0
    Imax = max(Imax, 0.01)

    # Linha teórica para esse R: V = R*I
    I_line = np.linspace(0, Imax, 200)
    V_line = R * I_line

    df_line = pd.DataFrame({"corrente": I_line, "tensao": V_line})
    df_point = pd.DataFrame({"corrente": [I], "tensao": [V_R]})

    line = alt.Chart(df_line).mark_line().encode(
        x=alt.X("corrente:Q", title="Corrente (A)", scale=alt.Scale(domain=[0, Imax])),
        y=alt.Y("tensao:Q", title="Tensão (V)", scale=alt.Scale(domain=[0, float(Vmax)])),
        tooltip=[alt.Tooltip("corrente:Q", format=".4f"), alt.Tooltip("tensao:Q", format=".2f")]
    )

    point_color = "#ef4444" if sw else "#64748b"
    point = alt.Chart(df_point).mark_point(size=160, filled=True).encode(
        x="corrente:Q",
        y="tensao:Q",
        color=alt.value(point_color),
        tooltip=[
            alt.Tooltip("corrente:Q", title="I (A)", format=".4f"),
            alt.Tooltip("tensao:Q", title="V_R (V)", format=".2f"),
        ],
    )

    st.altair_chart((line + point).properties(height=340), use_container_width=True)

    st.markdown("### Leituras")
    c1, c2, c3 = st.columns(3)
    c1.metric("Fonte", fmt_voltage(Vsrc))
    c2.metric("Corrente (I)", fmt_current(I))
    c3.metric("Tensão no resistor (V_R)", fmt_voltage(V_R))

    st.write(f"**Resistência (R):** {R:.1f} Ω")
    st.write(f"**Potência no resistor (P):** {Ptxt}")

    st.info("A reta é **V = R·I**. Ao alterar **R**, a inclinação muda. Ao alterar **V**, o ponto se desloca sobre a reta (com o interruptor ON).")
