"""
Hotmart Club · Dashboard de Progreso de Alumnos
================================================
Cómo usar:
  1. Instala dependencias: pip install streamlit requests pandas plotly openpyxl
  2. Ejecuta: streamlit run hotmart_dashboard.py
  3. Abre en el navegador (normalmente http://localhost:8501)
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io

st.set_page_config(
    page_title="Hotmart · Progreso de Alumnos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  [data-testid="stSidebar"] { background:#0f0f11; }
  [data-testid="stSidebar"] * { color: #f0eff0 !important; }
  [data-testid="stSidebar"] input { background: #1e1e22 !important; border-color:#333 !important; }
</style>
""", unsafe_allow_html=True)


# ─── FUNCIONES DE API ─────────────────────────────────────────────────────────

def get_access_token(basic_token, client_id, client_secret):
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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = (
        f"https://developers.hotmart.com/club/api/v1"
        f"/users/{user_id}/lessons?subdomain={subdomain}"
    )
    resp = requests.get(url, headers=headers, timeout=15)
    raw_status = resp.status_code
    raw_text = resp.text[:300]

    if raw_status == 200:
        try:
            data = resp.json()
            if isinstance(data, dict):
                lecciones = data.get("lessons", data.get("items", []))
                return lecciones, None
            elif isinstance(data, list):
                return data, None
            else:
                return [], f"Estructura inesperada: {str(data)[:200]}"
        except Exception:
            return [], f"JSON invalido (status 200). Respuesta cruda: {raw_text}"
    elif raw_status == 204:
        return [], None
    else:
        return [], f"HTTP {raw_status}: {raw_text}"


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Credenciales del cliente")
    st.markdown("---")
    basic_token   = st.text_input("Basic Token",      placeholder="Basic NTM5OWZlMD...")
    client_id     = st.text_input("Client ID",        placeholder="5399fe00-f707-...")
    client_secret = st.text_input("Client Secret",    type="password", placeholder="ae15213e-5762-...")
    subdomain     = st.text_input("Subdominio del Club", placeholder="agencypro")
    st.markdown("---")
    generar = st.button("Generar Dashboard", use_container_width=True, type="primary")
    st.markdown("---")
    st.markdown("**Subdominio:** lo que aparece en")
    st.markdown("`hotmart.com/es/club/`**subdominio**")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

st.markdown(f"# Hotmart Club - Progreso de Alumnos")
st.markdown(f"Club: **{subdomain or '---'}** · Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if not generar:
    st.info("Completa las credenciales en el panel izquierdo y haz clic en Generar Dashboard.")
    st.stop()

if not all([basic_token, client_id, client_secret, subdomain]):
    st.error("Por favor completa todos los campos antes de continuar.")
    st.stop()


# ─── EXTRACCION ───────────────────────────────────────────────────────────────

with st.status("Conectando con Hotmart...", expanded=True) as status:

    token, err = get_access_token(basic_token, client_id, client_secret)
    if err:
        st.error(f"Error de autenticacion: {err}")
        st.stop()
    st.write("Autenticacion exitosa")

    st.write("Obteniendo lista de alumnos...")
    students, err2 = get_students(token, subdomain)
    if err2 or not students:
        st.error(f"No se pudo obtener alumnos: {err2}")
        st.stop()
    st.write(f"{len(students)} alumnos encontrados")

    st.write("Extrayendo progreso por alumno...")
    all_data = []
    errores  = []
    progress_bar = st.progress(0)

    for i, student in enumerate(students):
        uid   = student.get("id", "")
        name  = student.get("name", "Sin nombre")
        email = student.get("email", "")

        lecciones, err_l = get_student_progress(token, subdomain, uid)

        if err_l:
            errores.append({"alumno": name, "error": err_l})

        for l in lecciones:
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(
                    l["completed_date"] / 1000
                ).strftime("%d/%m/%Y")

            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           l.get("module_name", ""),
                "Leccion":          l.get("page_name", ""),
                "Modulo Extra":     "Si" if l.get("is_module_extra") else "No",
                "Completada":       "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha
            })

        progress_bar.progress((i + 1) / len(students))
        time.sleep(0.2)

    status.update(label="Extraccion completa", state="complete")


# ─── DIAGNOSTICO VISIBLE ──────────────────────────────────────────────────────

if errores:
    with st.expander(f"{len(errores)} alumnos con error (clic para ver detalle)"):
        st.dataframe(pd.DataFrame(errores), use_container_width=True)

if not all_data:
    st.warning("No se encontraron datos de lecciones. Revisa el detalle de errores arriba.")
    st.stop()


# ─── METRICAS ─────────────────────────────────────────────────────────────────

df = pd.DataFrame(all_data)

resumen = df.groupby(["Nombre", "Email"]).apply(
    lambda x: pd.Series({
        "Total lecciones": len(x),
        "Completadas":     (x["Completada"] == "Si").sum(),
        "Sin completar":   (x["Completada"] == "No").sum(),
        "Pct Avance":      round((x["Completada"] == "Si").mean() * 100, 1)
    })
).reset_index()

por_modulo = df.groupby("Modulo").apply(
    lambda x: pd.Series({
        "Interacciones": len(x),
        "Completadas":   (x["Completada"] == "Si").sum(),
        "Pct Completado": round((x["Completada"] == "Si").mean() * 100, 1)
    })
).reset_index()

def segmento(pct):
    if pct >= 80:
        return "Avanzado"
    if pct >= 30:
        return "En progreso"
    return "En riesgo"

resumen["Estado"] = resumen["Pct Avance"].apply(segmento)

total_alumnos   = len(resumen)
avance_promedio = round(resumen["Pct Avance"].mean(), 1)
en_riesgo       = (resumen["Pct Avance"] < 30).sum()
completaron     = (resumen["Pct Avance"] >= 80).sum()


# ─── KPIs ─────────────────────────────────────────────────────────────────────

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total alumnos",   total_alumnos)
c2.metric("Avance promedio", f"{avance_promedio}%")
c3.metric("En riesgo",       en_riesgo)
c4.metric("Completaron",     completaron)
st.markdown("---")


# ─── GRAFICAS ─────────────────────────────────────────────────────────────────

col_left, col_right = st.columns(2)
color_map = {"Avanzado": "#2ecc8f", "En progreso": "#f5a623", "En riesgo": "#e05151"}

with col_left:
    st.subheader("Segmentacion de alumnos")
    seg = resumen["Estado"].value_counts().reset_index()
    seg.columns = ["Estado", "Cantidad"]
    fig_d = px.pie(seg, names="Estado", values="Cantidad",
                   hole=0.55, color="Estado", color_discrete_map=color_map)
    fig_d.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280,
                        paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_d, use_container_width=True)

with col_right:
    st.subheader("Completitud por modulo")
    colors_mod = [
        "#2ecc8f" if p >= 60 else "#f5a623" if p >= 35 else "#e05151"
        for p in por_modulo["Pct Completado"]
    ]
    fig_m = go.Figure(go.Bar(
        x=por_modulo["Pct Completado"],
        y=por_modulo["Modulo"],
        orientation="h",
        marker_color=colors_mod,
        text=[f"{p}%" for p in por_modulo["Pct Completado"]],
        textposition="outside"
    ))
    fig_m.update_layout(
        xaxis=dict(range=[0, 115]),
        yaxis=dict(autorange="reversed"),
        margin=dict(t=10, b=10, l=10, r=40),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    st.plotly_chart(fig_m, use_container_width=True)

st.subheader("Progreso individual")
sorted_r = resumen.sort_values("Pct Avance", ascending=True)
fig_a = go.Figure(go.Bar(
    x=sorted_r["Pct Avance"],
    y=sorted_r["Nombre"],
    orientation="h",
    marker_color=[color_map[e] for e in sorted_r["Estado"]],
    text=[f"{p}%" for p in sorted_r["Pct Avance"]],
    textposition="outside"
))
fig_a.update_layout(
    xaxis=dict(range=[0, 115], ticksuffix="%"),
    margin=dict(t=10, b=10, l=10, r=50),
    height=max(300, len(students) * 28),
    paper_bgcolor="rgba(0,0,0,0)",
    showlegend=False
)
st.plotly_chart(fig_a, use_container_width=True)


# ─── TABLA ────────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Tabla de alumnos")
filtro = st.selectbox("Filtrar por estado", ["Todos", "En riesgo", "En progreso", "Avanzado"])
df_tabla = resumen if filtro == "Todos" else resumen[resumen["Estado"] == filtro]
st.dataframe(
    df_tabla[["Nombre", "Email", "Completadas", "Total lecciones", "Pct Avance", "Estado"]],
    use_container_width=True,
    hide_index=True
)


# ─── EXPORTAR ─────────────────────────────────────────────────────────────────

st.markdown("---")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    resumen.to_excel(writer, sheet_name="Resumen por alumno", index=False)
    por_modulo.to_excel(writer, sheet_name="Por modulo", index=False)
    df.to_excel(writer, sheet_name="Detalle completo", index=False)
buffer.seek(0)

st.download_button(
    label="Descargar Excel completo",
    data=buffer,
    file_name=f"informe_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
