"""
Hotmart Club · Dashboard de Progreso de Alumnos
================================================
Cómo usar:
  1. Instala dependencias: pip install streamlit requests pandas plotly openpyxl
  2. Ejecuta: streamlit run hotmart_dashboard.py
  3. Abre en el navegador (normalmente http://localhost:8501)

Para el equipo (sin instalar nada):
  - Sube este archivo a https://share.streamlit.io (gratis)
  - Comparte el link — cualquiera lo abre y usa sin código
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io

# ─── CONFIGURACIÓN DE PÁGINA ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Hotmart · Progreso de Alumnos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  .metric-card { background:#f8f9fa; border-radius:12px; padding:16px 20px; border: 1px solid #e9ecef; }
  .risk-high   { color:#e05151; font-weight:600; }
  .risk-mid    { color:#f5a623; font-weight:600; }
  .risk-low    { color:#2ecc8f; font-weight:600; }
  [data-testid="stSidebar"] { background:#0f0f11; }
  [data-testid="stSidebar"] * { color: #f0eff0 !important; }
  [data-testid="stSidebar"] input { background: #1e1e22 !important; border-color:#333 !important; }
  [data-testid="stSidebar"] .stTextInput label { color:#7a7980 !important; }
</style>
""", unsafe_allow_html=True)


# ─── FUNCIONES DE API ─────────────────────────────────────────────────────────

def get_access_token(basic_token, client_id, client_secret):
    """Obtiene el access token de Hotmart."""
    url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": basic_token
    }
    body = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    resp = requests.post(url, headers=headers, data=body, timeout=15)
    if resp.status_code == 200:
        return resp.json().get("access_token"), None
    return None, f"Error {resp.status_code}: {resp.text}"


def get_students(access_token, subdomain):
    """Obtiene la lista de estudiantes del Club."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}"
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list):
            return data, None
        elif "items" in data:
            return data["items"], None
        elif isinstance(data, dict):
            return list(data.values())[0] if data else [], None
    return [], f"Error {resp.status_code}: {resp.text}"


def get_student_progress(access_token, subdomain, user_id):
    """Obtiene el progreso de lecciones de un alumno."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = (
        f"https://developers.hotmart.com/club/api/v1"
        f"/users/{user_id}/lessons?subdomain={subdomain}"
    )
    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code == 200:
        try:
            return resp.json().get("lessons", []), None
        except Exception:
            return [], None
    return [], f"Error {resp.status_code}"

# ─── SIDEBAR · FORMULARIO DE CREDENCIALES ────────────────────────────────────

with st.sidebar:
    st.markdown("## 🔑 Credenciales del cliente")
    st.markdown("---")

    basic_token   = st.text_input("Basic Token", placeholder="Basic NTM5OWZlMD...")
    client_id     = st.text_input("Client ID",   placeholder="5399fe00-f707-...")
    client_secret = st.text_input("Client Secret", type="password", placeholder="ae15213e-5762-...")
    subdomain     = st.text_input("Subdominio del Club", placeholder="agencypro")

    st.markdown("---")
    generar = st.button("🚀 Generar Dashboard", use_container_width=True, type="primary")

    st.markdown("---")
    st.markdown("**¿Dónde encuentro estas credenciales?**")
    st.markdown("developers.hotmart.com → tu aplicación")
    st.markdown("**Subdominio:** lo que aparece en")
    st.markdown("`hotmart.com/es/club/`**subdominio**")


# ─── MAIN · TÍTULO ───────────────────────────────────────────────────────────

col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown(f"# 📊 Hotmart Club · Progreso de Alumnos")
    st.markdown(f"Club: **{subdomain or '—'}** · Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")
with col_badge:
    st.markdown("")

if not generar:
    st.info("👈 Completa las credenciales en el panel izquierdo y haz clic en **Generar Dashboard**.")
    st.stop()


# ─── FLUJO PRINCIPAL ─────────────────────────────────────────────────────────

if not all([basic_token, client_id, client_secret, subdomain]):
    st.error("⚠️ Por favor completa todos los campos antes de continuar.")
    st.stop()

# PASO 1: Token
with st.status("Autenticando con Hotmart...", expanded=True) as status:
    token, err = get_access_token(basic_token, client_id, client_secret)
    if err:
        st.error(f"No se pudo obtener el token: {err}")
        st.stop()
    st.write("✅ Autenticación exitosa")

    # PASO 2: Estudiantes
    st.write("Obteniendo lista de alumnos...")
    students, err2 = get_students(token, subdomain)
    if err2 or not students:
        st.error(f"No se pudo obtener la lista de alumnos: {err2}")
        st.stop()
    st.write(f"✅ {len(students)} alumnos encontrados")

    # PASO 3: Progreso
    st.write("Extrayendo progreso de cada alumno (puede tomar unos segundos)...")
    all_data = []
    progress_bar = st.progress(0)

    for i, student in enumerate(students):
        uid   = student.get("id", "")
        name  = student.get("name", "Sin nombre")
        email = student.get("email", "")

        lecciones, _ = get_student_progress(token, subdomain, uid)

        for l in lecciones:
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(l["completed_date"] / 1000).strftime("%d/%m/%Y")

            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Módulo":           l.get("module_name", ""),
                "Lección":          l.get("page_name", ""),
                "Módulo Extra":     "Sí" if l.get("is_module_extra") else "No",
                "Completada":       "Sí" if l.get("is_completed") else "No",
                "Fecha Completado": fecha
            })

        progress_bar.progress((i + 1) / len(students))
        time.sleep(0.2)  # Respetar rate limits de la API

    status.update(label="✅ Datos extraídos correctamente", state="complete")

df = pd.DataFrame(all_data)

if df.empty:
    st.warning("No se encontraron datos de lecciones para este subdominio.")
    st.stop()


# ─── CÁLCULO DE MÉTRICAS ─────────────────────────────────────────────────────

resumen = df.groupby(["Nombre", "Email"]).apply(
    lambda x: pd.Series({
        "Total lecciones": len(x),
        "Completadas":     (x["Completada"] == "Sí").sum(),
        "Sin completar":   (x["Completada"] == "No").sum(),
        "% Avance":        round((x["Completada"] == "Sí").mean() * 100, 1)
    })
).reset_index()

por_modulo = df.groupby("Módulo").apply(
    lambda x: pd.Series({
        "Interacciones": len(x),
        "Completadas":   (x["Completada"] == "Sí").sum(),
        "% Completado":  round((x["Completada"] == "Sí").mean() * 100, 1)
    })
).reset_index()

total_alumnos  = len(resumen)
avance_promedio = round(resumen["% Avance"].mean(), 1)
en_riesgo      = (resumen["% Avance"] < 30).sum()
completaron    = (resumen["% Avance"] >= 80).sum()

def segmento(pct):
    if pct >= 80: return "Avanzado"
    if pct >= 30: return "En progreso"
    return "En riesgo"

resumen["Estado"] = resumen["% Avance"].apply(segmento)


# ─── KPIs ────────────────────────────────────────────────────────────────────

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("👥 Total alumnos",   total_alumnos)
c2.metric("📈 Avance promedio", f"{avance_promedio}%")
c3.metric("⚠️ En riesgo",       en_riesgo, help="Menos del 30% del contenido completado")
c4.metric("🏆 Completaron",     completaron, help="Más del 80% del contenido completado")

st.markdown("---")


# ─── GRÁFICAS ────────────────────────────────────────────────────────────────

col_left, col_right = st.columns(2)

# Donut: Segmentación
with col_left:
    st.subheader("Segmentación de alumnos")
    seg_counts = resumen["Estado"].value_counts().reset_index()
    seg_counts.columns = ["Estado", "Cantidad"]
    color_map = {"Avanzado": "#2ecc8f", "En progreso": "#f5a623", "En riesgo": "#e05151"}
    fig_donut = px.pie(
        seg_counts, names="Estado", values="Cantidad",
        hole=0.55, color="Estado", color_discrete_map=color_map
    )
    fig_donut.update_traces(textposition="outside", textinfo="label+value")
    fig_donut.update_layout(
        showlegend=True, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=280, legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# Módulos: barras horizontales
with col_right:
    st.subheader("Completitud por módulo")
    colors = ["#2ecc8f" if p >= 60 else "#f5a623" if p >= 35 else "#e05151"
              for p in por_modulo["% Completado"]]
    fig_mod = go.Figure(go.Bar(
        x=por_modulo["% Completado"],
        y=por_modulo["Módulo"],
        orientation="h",
        marker_color=colors,
        text=[f"{p}%" for p in por_modulo["% Completado"]],
        textposition="outside"
    ))
    fig_mod.update_layout(
        xaxis=dict(range=[0, 110], showgrid=False, zeroline=False),
        yaxis=dict(autorange="reversed"),
        margin=dict(t=10, b=10, l=10, r=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=280, showlegend=False
    )
    st.plotly_chart(fig_mod, use_container_width=True)

# Barras de progreso por alumno
st.subheader("Progreso individual")
sorted_resumen = resumen.sort_values("% Avance", ascending=True)
bar_colors = [color_map[e] for e in sorted_resumen["Estado"]]
fig_alumnos = go.Figure(go.Bar(
    x=sorted_resumen["% Avance"],
    y=sorted_resumen["Nombre"],
    orientation="h",
    marker_color=bar_colors,
    text=[f"{p}%" for p in sorted_resumen["% Avance"]],
    textposition="outside"
))
fig_alumnos.update_layout(
    xaxis=dict(range=[0, 115], showgrid=False, zeroline=False, ticksuffix="%"),
    margin=dict(t=10, b=10, l=10, r=50),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    height=max(300, len(students) * 28),
    showlegend=False
)
st.plotly_chart(fig_alumnos, use_container_width=True)


# ─── TABLA DETALLADA ─────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Tabla de alumnos")

col_filter, _ = st.columns([1, 2])
with col_filter:
    filtro = st.selectbox("Filtrar por estado", ["Todos", "En riesgo", "En progreso", "Avanzado"])

df_tabla = resumen if filtro == "Todos" else resumen[resumen["Estado"] == filtro]
st.dataframe(
    df_tabla[["Nombre","Email","Completadas","Total lecciones","% Avance","Estado"]],
    use_container_width=True, hide_index=True
)


# ─── EXPORTAR ────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Exportar informe")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    resumen.to_excel(writer, sheet_name="Resumen por alumno", index=False)
    por_modulo.to_excel(writer, sheet_name="Por módulo", index=False)
    df.to_excel(writer, sheet_name="Detalle completo", index=False)
buffer.seek(0)

nombre_archivo = f"informe_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx"
st.download_button(
    label="📥 Descargar Excel completo",
    data=buffer,
    file_name=nombre_archivo,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
