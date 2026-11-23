# -*- coding: utf-8 -*-
"""
PROTOTIPO SIMULADO - Sistema de detección temprana de filtraciones
I+E III - INACAP La Serena | Diego González, Johan Espinoza, Fernando Cortés
Simula sensores IoT de humedad en tres entretechos y una alerta al celular/comité.
No utiliza sensores ni envía mensajes reales: es una demostración por software.
"""

import random
import time
from datetime import datetime
from html import escape

import plotly.graph_objects as go
import streamlit as st

# ---------------- CONFIGURACIÓN ----------------
st.set_page_config(
    page_title="Detección temprana de filtraciones",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROJO = "#EF4444"
VERDE = "#22C55E"
AMBAR = "#F59E0B"
AZUL = "#38BDF8"
MORADO = "#A78BFA"
TURQUESA = "#2DD4BF"
UMBRAL_ALERTA = 70
UMBRAL_PRECAUCION = 50
MAX_HISTORIAL = 40

CASAS_INICIALES = {
    "Casa 1 · Rosa Muñoz": 35.0,
    "Casa 2 · Margarita López": 42.0,
    "Casa 3 · Patricia Rojas": 28.0,
}
COLORES_CASAS = [AZUL, MORADO, TURQUESA]


def estado_de(humedad):
    """Umbrales ilustrativos: no constituyen detección física validada."""
    if humedad >= UMBRAL_ALERTA:
        return "ALERTA", ROJO
    if humedad >= UMBRAL_PRECAUCION:
        return "Precaución", AMBAR
    return "Normal", VERDE


def iniciar_simulacion():
    """Inicializa una única vez los datos de la sesión."""
    if st.session_state.get("version_demo") == "1.1":
        return
    st.session_state.version_demo = "1.1"
    st.session_state.casas = CASAS_INICIALES.copy()
    st.session_state.hist = {
        casa: [humedad] for casa, humedad in CASAS_INICIALES.items()
    }
    st.session_state.eventos = []
    st.session_state.n_alertas = 0
    st.session_state.ultimo_estado = {
        casa: estado_de(humedad)[0]
        for casa, humedad in CASAS_INICIALES.items()
    }
    st.session_state.modo_auto = False
    st.session_state.ultimo_tick = time.monotonic()
    st.session_state.aviso_pendiente = None


def registrar_cambios():
    """Registra únicamente cambios de estado; evita filas duplicadas."""
    for casa, humedad in st.session_state.casas.items():
        estado, _ = estado_de(humedad)
        anterior = st.session_state.ultimo_estado[casa]
        if estado != anterior:
            st.session_state.eventos.insert(0, {
                "Hora": datetime.now().strftime("%H:%M:%S"),
                "Casa": casa,
                "Humedad": f"{humedad:.0f}%",
                "Cambio": f"{anterior} → {estado}",
            })
            st.session_state.eventos = st.session_state.eventos[:12]
            if estado == "ALERTA":
                st.session_state.n_alertas += 1
                st.session_state.aviso_pendiente = casa
        st.session_state.ultimo_estado[casa] = estado


def guardar_lectura():
    """Una muestra por acción (o ciclo automático), para las tres casas."""
    for casa, humedad in st.session_state.casas.items():
        st.session_state.hist[casa].append(humedad)
        st.session_state.hist[casa] = st.session_state.hist[casa][-MAX_HISTORIAL:]
    registrar_cambios()


def modificar_humedad(casa, incremento=0.0, objetivo=None):
    anterior = st.session_state.casas[casa]
    nuevo = objetivo if objetivo is not None else anterior + incremento
    nuevo = max(0.0, min(100.0, nuevo))
    if nuevo != anterior:
        st.session_state.casas[casa] = nuevo
        guardar_lectura()


def reiniciar_simulacion():
    st.session_state.casas = {casa: 30.0 for casa in CASAS_INICIALES}
    st.session_state.hist = {casa: [30.0] for casa in CASAS_INICIALES}
    st.session_state.eventos = []
    st.session_state.n_alertas = 0
    st.session_state.ultimo_estado = {casa: "Normal" for casa in CASAS_INICIALES}
    st.session_state.modo_auto = False
    st.session_state.ultimo_tick = time.monotonic()
    st.session_state.aviso_pendiente = None


def avanzar_lluvia_automatica():
    for casa in st.session_state.casas:
        st.session_state.casas[casa] = min(
            100.0, st.session_state.casas[casa] + random.uniform(1.5, 5.0)
        )
    guardar_lectura()


def medidor(humedad, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=humedad,
        number={"suffix": "%", "font": {"size": 36, "color": "#F8FAFC"}},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 25, 50, 70, 100],
                "tickcolor": "#94A3B8",
                "tickfont": {"color": "#94A3B8", "size": 11},
            },
            "bar": {"color": color, "thickness": 0.33},
            "bgcolor": "#19263B",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#173B35"},
                {"range": [50, 70], "color": "#57401E"},
                {"range": [70, 100], "color": "#542735"},
            ],
            "threshold": {
                "line": {"color": "#F8FAFC", "width": 3},
                "thickness": 0.75,
                "value": UMBRAL_ALERTA,
            },
        },
    ))
    fig.update_layout(
        height=195,
        margin=dict(l=12, r=12, t=28, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#E2E8F0"},
    )
    return fig


def grafico_historial():
    fig = go.Figure()
    for (casa, serie), color in zip(st.session_state.hist.items(), COLORES_CASAS):
        fig.add_trace(go.Scatter(
            x=list(range(len(serie))),
            y=serie,
            mode="lines+markers",
            name=casa.split(" · ")[0],
            line={"color": color, "width": 3, "shape": "spline"},
            marker={"size": 5},
            hovertemplate="Lectura %{x}<br>Humedad %{y:.1f}%<extra>%{fullData.name}</extra>",
        ))
    fig.add_hline(
        y=UMBRAL_ALERTA, line_dash="dash", line_color=ROJO,
        annotation_text="Alerta 70%", annotation_position="top left",
        annotation_font_color=ROJO,
    )
    fig.add_hline(
        y=UMBRAL_PRECAUCION, line_dash="dot", line_color=AMBAR,
    )
    fig.update_layout(
        height=305,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#CBD5E1"},
        margin=dict(l=8, r=15, t=28, b=15),
        yaxis={
            "range": [0, 105], "title": "Humedad (%)",
            "gridcolor": "#27364B", "zeroline": False,
        },
        xaxis={
            "title": "Lecturas de la simulación",
            "gridcolor": "#27364B", "zeroline": False,
            "dtick": 5,
        },
        legend={"orientation": "h", "y": -0.28, "x": 0},
        hovermode="x unified",
    )
    return fig


# ---------------- ESTILO VISUAL ----------------
st.markdown("""
<style>
    .stApp {background: #0B1220;}
    .block-container {padding-top: 1.8rem; padding-bottom: 2rem; max-width: 1400px;}
    [data-testid="stSidebar"] {background: #111C2E;}
    [data-testid="stSidebar"] hr {border-color: #304057;}
    h1, h2, h3 {letter-spacing: -0.025em;}
    .hero {
        padding: 25px 28px; border-radius: 18px;
        background: linear-gradient(110deg, #152A45, #17233C 70%, #39233C);
        border: 1px solid #314865; margin-bottom: 14px;
    }
    .hero-title {font-size: clamp(24px, 2.6vw, 36px); font-weight: 800;
                 color: #F8FAFC; line-height: 1.2; margin: 0 0 8px;}
    .hero-subtitle {color: #CBD5E1; font-size: 14px;}
    .hero-pill {display: inline-block; padding: 5px 11px; margin-bottom: 12px;
                border-radius: 100px; color: #93C5FD; background: #1E3A5F;
                font-size: 11px; font-weight: 700; letter-spacing: 0.8px;}
    .metric-card {background: #152238; border: 1px solid #2A3B53;
                  padding: 18px 19px; border-radius: 14px; min-height: 105px;}
    .metric-label {color: #9CAEC6; font-size: 13px; margin-bottom: 9px;}
    .metric-value {color: #F8FAFC; font-size: 31px; font-weight: 750; line-height: 1.1;}
    .sensor-label {font-weight: 750; color: #F8FAFC; font-size: 17px;}
    .sensor-owner {font-size: 13px; color: #94A3B8;}
    .status-tag {text-align: center; padding: 8px 10px; border-radius: 9px;
                 font-weight: 750; font-size: 13px; margin-top: -4px;}
    .phone {max-width: 330px; border: 8px solid #273244; border-radius: 30px;
            padding: 20px 12px 12px; background: #080E19; margin: 4px auto 8px;
            box-shadow: 0 15px 30px #0005;}
    .phone-top {color: #94A3B8; text-align: center; font-size: 12px;
                padding-bottom: 12px;}
    .phone-content {background: #17283E; border: 1px solid #36516A;
                    color: #F8FAFC; padding: 16px; border-radius: 16px;
                    min-height: 150px; line-height: 1.5;}
    .phone-title {font-size: 15px; font-weight: 800; padding-bottom: 8px;}
    .phone-home {width: 75px; height: 4px; border-radius: 10px;
                 background: #64748B; margin: 15px auto 1px;}
    .small-note {color: #94A3B8; font-size: 12px;}
</style>
""", unsafe_allow_html=True)

iniciar_simulacion()

# ---------------- BARRA LATERAL ----------------
with st.sidebar:
    st.title("Controles de la demo")
    st.caption("Los datos son simulados. No necesitas sensores físicos.")
    casa_sel = st.selectbox(
        "Vivienda a intervenir", list(st.session_state.casas.keys())
    )

    izquierda, derecha = st.columns(2)
    izquierda.button(
        "🌧️ Simular lluvia", on_click=modificar_humedad,
        args=(casa_sel, 18.0), use_container_width=True,
    )
    derecha.button(
        "☀️ Ventilar / secar", on_click=modificar_humedad,
        args=(casa_sel, -15.0), use_container_width=True,
    )
    st.button(
        "🚨 Simular filtración crítica", on_click=modificar_humedad,
        args=(casa_sel, 0.0, 85.0), use_container_width=True,
    )
    st.divider()
    st.toggle("Modo automático · lluvia gradual", key="modo_auto")
    st.caption("En automático aumenta gradualmente la humedad de las tres casas.")
    st.button(
        "🔄 Reiniciar simulación", on_click=reiniciar_simulacion,
        use_container_width=True,
    )
    st.divider()
    st.markdown("**Umbrales de la demo**")
    st.markdown("🟢 Normal: menos de 50%")
    st.markdown("🟠 Precaución: 50% a menos de 70%")
    st.markdown("🔴 Alerta: 70% o más")
    st.caption("Los porcentajes y límites son ilustrativos, no mediciones reales.")

# ---------------- ENCABEZADO ----------------
st.markdown("""
<div class="hero">
  <div class="hero-pill">I+E III · INACAP LA SERENA · DEMO IoT</div>
  <div class="hero-title">🏠 Detección temprana de filtraciones</div>
  <div class="hero-subtitle">Monitoreo simulado de humedad en entretechos · Diego González, Johan Espinoza y Fernando Cortés</div>
</div>
""", unsafe_allow_html=True)

st.caption(
    "Un sistema de alerta temprana para viviendas: identifica niveles elevados de "
    "humedad y permite actuar antes de que el daño avance. Prototipo 100% simulado."
)

with st.expander("ℹ️ ¿Cómo funciona? (explicación para la presentación)"):
    st.markdown(
        "1. **Sensor:** mide la humedad en el entretecho (representado en esta simulación).\n"
        "2. **Conectividad:** enviaría las lecturas por Wi-Fi o una red tipo LoRa.\n"
        "3. **Evaluación:** el sistema compara las lecturas con los umbrales de la demo.\n"
        "4. **Alerta:** al llegar al 70%, muestra una notificación *simulada* al celular/comité.\n"
        "5. **Acción:** la familia revisaría el techo y aplicaría las medidas de reparación.\n\n"
        "**Importante:** la humedad ambiental alta puede tener otras causas. El valor "
        "70% es demostrativo y no prueba por sí solo una filtración real."
    )


# ---------------- PANEL EN VIVO ----------------
# Un fragmento actualiza los gráficos sin bloquear toda la aplicación con sleep().
@st.fragment(run_every="1.5s" if st.session_state.modo_auto else None)
def panel_en_vivo():
    if st.session_state.modo_auto:
        ahora = time.monotonic()
        if ahora - st.session_state.ultimo_tick >= 1.4:
            avanzar_lluvia_automatica()
            st.session_state.ultimo_tick = ahora

    if st.session_state.aviso_pendiente:
        st.toast(
            f"Humedad alta en {st.session_state.aviso_pendiente}", icon="🚨"
        )
        st.session_state.aviso_pendiente = None

    valores = list(st.session_state.casas.values())
    promedio = sum(valores) / len(valores)
    alertas_activas = sum(h >= UMBRAL_ALERTA for h in valores)
    precauciones = sum(UMBRAL_PRECAUCION <= h < UMBRAL_ALERTA for h in valores)

    # Indicadores superiores.
    indicadores = [
        ("Viviendas monitoreadas", "03", "#F8FAFC"),
        ("Humedad promedio", f"{promedio:.0f}%", AZUL),
        ("Casas en alerta", f"{alertas_activas:02d}", ROJO if alertas_activas else VERDE),
        ("Alertas de esta sesión", f"{st.session_state.n_alertas:02d}", AMBAR),
    ]
    for columna, (etiqueta, valor, color) in zip(st.columns(4), indicadores):
        with columna:
            st.markdown(
                f'<div class="metric-card"><div class="metric-label">{etiqueta}</div>'
                f'<div class="metric-value" style="color:{color}">{valor}</div></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    st.subheader("📡 Lectura de sensores en los entretechos")
    for columna, (casa, humedad) in zip(
        st.columns(3), st.session_state.casas.items()
    ):
        estado, color = estado_de(humedad)
        numero, propietario = casa.split(" · ", maxsplit=1)
        with columna:
            with st.container(border=True):
                st.markdown(
                    f'<div class="sensor-label">{escape(numero)}</div>'
                    f'<div class="sensor-owner">{escape(propietario)}</div>',
                    unsafe_allow_html=True,
                )
                st.plotly_chart(
                    medidor(humedad, color),
                    width="stretch", key=f"medidor_{numero}",
                    config={"displayModeBar": False},
                )
                st.markdown(
                    f'<div class="status-tag" style="color:{color};'
                    f'background:{color}20;border:1px solid {color}55">'
                    f'{escape(estado.upper())}</div>',
                    unsafe_allow_html=True,
                )

    st.subheader("📈 Humedad en el tiempo")
    st.plotly_chart(
        grafico_historial(), width="stretch",
        config={"displayModeBar": False},
    )
    st.caption("Cada punto corresponde a una actualización de la simulación (máximo 40 lecturas).")

    # Teléfono y estado general.
    izquierda, derecha = st.columns([1, 1.15], gap="large")
    with izquierda:
        st.subheader("📱 Alerta al teléfono")
        casas_alerta = [
            casa for casa, h in st.session_state.casas.items()
            if h >= UMBRAL_ALERTA
        ]
        if casas_alerta:
            titulo = "🚨 Posible filtración"
            mensaje = "Humedad elevada en:<br>" + "<br>".join(
                "• " + escape(casa) for casa in casas_alerta
            )
            mensaje += (
                "<br><br><span class='small-note'>Revisar el entretecho y evaluar "
                "medidas de reparación.</span>"
            )
            borde = ROJO
        else:
            titulo = "✅ Viviendas sin alerta"
            mensaje = (
                "Ninguna casa supera el umbral de alerta."
                "<br><br><span class='small-note'>El monitoreo simulado continúa.</span>"
            )
            borde = VERDE
        st.markdown(
            '<div class="phone"><div class="phone-top">'
            '12:00 ▰▰▰ Wi-Fi · VISTA PREVIA</div>'
            f'<div class="phone-content" style="border-left:4px solid {borde}">'
            f'<div class="phone-title">{titulo}</div>{mensaje}</div>'
            '<div class="phone-home"></div></div>',
            unsafe_allow_html=True,
        )
        st.caption("Aviso visual: la aplicación no envía SMS ni notificaciones reales.")

    with derecha:
        st.subheader("🏘️ Estado general")
        if alertas_activas:
            st.error(
                f"{alertas_activas} vivienda(s) con humedad en nivel de ALERTA. "
                "Requieren revisión en esta demostración."
            )
        elif precauciones:
            st.warning(
                f"{precauciones} vivienda(s) en PRECAUCIÓN. "
                "Conviene revisar la evolución de la humedad."
            )
        else:
            st.success("Las tres viviendas están en estado NORMAL.")
        st.markdown(
            "**Secuencia para mostrar en vivo:**\n"
            "1. Selecciona una vivienda.\n"
            "2. Presiona **Simular lluvia** o **Simular filtración crítica**.\n"
            "3. Observa el medidor, el gráfico y la alerta del teléfono.\n"
            "4. Presiona **Ventilar / secar** para mostrar la recuperación."
        )

    st.subheader("📋 Registro del comité")
    if st.session_state.eventos:
        st.dataframe(
            st.session_state.eventos,
            width="stretch", hide_index=True,
        )
    else:
        st.info("Aún no hay cambios de estado. Simula lluvia para generar eventos.")
    st.caption(
        "Registro de cambios de estado (últimos 12 eventos). "
        "Las alertas se cuentan por cada entrada al estado ALERTA."
    )


panel_en_vivo()
