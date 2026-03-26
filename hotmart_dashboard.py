"""
Hotmart Club · Dashboard de Progreso de Alumnos v2
===================================================
Métricas incluidas:
  - Avance global por alumno
  - Última lección completada (dónde se quedaron)
  - Módulo de abandono (primer módulo con lecciones pendientes)
  - Avance por módulo × alumno (tabla cruzada)
  - Alumnos sin ninguna actividad (riesgo máximo)
  - Lecciones pendientes por alumno desglosadas
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
  .risk-tag { padding: 2px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; }
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
                return data.get("lessons", data.get("items", [])), None
            elif isinstance(data, list):
                return data, None
            else:
                return [], f"Estructura inesperada: {str(data)[:200]}"
        except Exception:
            return [], f"JSON invalido. Respuesta: {raw_text}"
    elif raw_status == 204:
        return [], None
    else:
        return [], f"HTTP {raw_status}: {raw_text}"


# ─── FUNCIONES DE ANÁLISIS ────────────────────────────────────────────────────

def calcular_punto_abandono(df_alumno):
    """Encuentra la última lección completada y el primer módulo pendiente."""
    completadas = df_alumno[df_alumno["Completada"] == "Si"].sort_values("Fecha Completado", ascending=False)
    pendientes  = df_alumno[df_alumno["Completada"] == "No"]

    ultima_leccion = completadas.iloc[0]["Leccion"] if not completadas.empty else "Sin actividad"
    ultimo_modulo  = completadas.iloc[0]["Modulo"]  if not completadas.empty else "Sin actividad"
    ultima_fecha   = completadas.iloc[0]["Fecha Completado"] if not completadas.empty else ""

    # Primer módulo con pendientes (módulo de abandono)
    if not pendientes.empty:
        modulo_abandono = pendientes.iloc[0]["Modulo"]
        leccion_abandono = pendientes.iloc[0]["Leccion"]
    else:
        modulo_abandono  = "Completado"
        leccion_abandono = "Completado"

    return ultima_leccion, ultimo_modulo, ultima_fecha, modulo_abandono, leccion_abandono


def estado_riesgo(pct):
    if pct == 0:    return "Sin actividad"
    if pct < 30:    return "En riesgo"
    if pct < 80:    return "En progreso"
    return "Avanzado"


def color_estado(estado):
    return {
        "Sin actividad": "#e05151",
        "En riesgo":     "#f5a623",
        "En progreso":   "#4f9cf9",
        "Avanzado":      "#2ecc8f"
    }.get(estado, "#888")


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Credenciales del cliente")
    st.markdown("---")
    basic_token   = st.text_input("Basic Token",         placeholder="Basic NTM5OWZlMD...")
    client_id     = st.text_input("Client ID",           placeholder="5399fe00-f707-...")
    client_secret = st.text_input("Client Secret",       type="password", placeholder="ae15213e-5762-...")
    subdomain     = st.text_input("Subdominio del Club", placeholder="don-guz")
    st.markdown("---")
    generar = st.button("Generar Dashboard", use_container_width=True, type="primary")
    st.markdown("---")
    st.markdown("**Subdominio:** lo que aparece en")
    st.markdown("`hotmart.com/es/club/`**subdominio**")


# ─── HEADER ───────────────────────────────────────────────────────────────────

st.markdown(f"# Hotmart Club - Progreso de Alumnos")
st.markdown(f"Club: **{subdomain or '---'}** · Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if not generar:
    st.info("Completa las credenciales en el panel izquierdo y haz clic en Generar Dashboard.")
    st.stop()

if not all([basic_token, client_id, client_secret, subdomain]):
    st.error("Por favor completa todos los campos antes de continuar.")
    st.stop()


# ─── EXTRACCIÓN ───────────────────────────────────────────────────────────────

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

        if not lecciones:
            # Alumno sin ninguna actividad registrada
            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           "Sin actividad",
                "Leccion":          "Sin actividad",
                "Modulo Extra":     "No",
                "Completada":       "No",
                "Fecha Completado": ""
            })
            progress_bar.progress((i + 1) / len(students))
            time.sleep(0.2)
            continue

        for l in lecciones:
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(
                    l["completed_date"] / 1000
                ).strftime("%d/%m/%Y")

            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           l.get("module_name", "Sin modulo"),
                "Leccion":          l.get("page_name", "Sin nombre"),
                "Modulo Extra":     "Si" if l.get("is_module_extra") else "No",
                "Completada":       "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha
            })

        progress_bar.progress((i + 1) / len(students))
        time.sleep(0.2)

    status.update(label="Extraccion completa", state="complete")


# ─── DIAGNÓSTICO ──────────────────────────────────────────────────────────────

if errores:
    with st.expander(f"{len(errores)} alumnos con error de API (clic para ver)"):
        st.dataframe(pd.DataFrame(errores), use_container_width=True)

if not all_data:
    st.warning("No se encontraron datos. Revisa los errores arriba.")
    st.stop()


# ─── PROCESAMIENTO ────────────────────────────────────────────────────────────

df = pd.DataFrame(all_data)
df_activos = df[df["Modulo"] != "Sin actividad"]

# Resumen global por alumno
resumen_rows = []
for nombre, grupo in df.groupby("Nombre"):
    email = grupo["Email"].iloc[0]
    grupo_activo = grupo[grupo["Modulo"] != "Sin actividad"]

    if grupo_activo.empty:
        resumen_rows.append({
            "Nombre":            nombre,
            "Email":             email,
            "Total lecciones":   0,
            "Completadas":       0,
            "Sin completar":     0,
            "Pct Avance":        0.0,
            "Estado":            "Sin actividad",
            "Ultima leccion":    "Nunca accedio",
            "Ultimo modulo":     "---",
            "Ultima actividad":  "---",
            "Modulo abandono":   "---",
            "Leccion abandono":  "---"
        })
        continue

    total      = len(grupo_activo)
    completadas = (grupo_activo["Completada"] == "Si").sum()
    pct        = round(completadas / total * 100, 1)
    estado     = estado_riesgo(pct)

    ul, um, uf, ma, la = calcular_punto_abandono(grupo_activo)

    resumen_rows.append({
        "Nombre":           nombre,
        "Email":            email,
        "Total lecciones":  total,
        "Completadas":      int(completadas),
        "Sin completar":    int(total - completadas),
        "Pct Avance":       pct,
        "Estado":           estado,
        "Ultima leccion":   ul,
        "Ultimo modulo":    um,
        "Ultima actividad": uf,
        "Modulo abandono":  ma,
        "Leccion abandono": la
    })

resumen = pd.DataFrame(resumen_rows)

# Avance por módulo × alumno
if not df_activos.empty:
    pivot_rows = []
    for (nombre, modulo), g in df_activos.groupby(["Nombre", "Modulo"]):
        total_m = len(g)
        comp_m  = (g["Completada"] == "Si").sum()
        pivot_rows.append({
            "Nombre":          nombre,
            "Modulo":          modulo,
            "Lecciones":       total_m,
            "Completadas":     int(comp_m),
            "Pendientes":      int(total_m - comp_m),
            "Pct Modulo":      round(comp_m / total_m * 100, 1)
        })
    df_pivot = pd.DataFrame(pivot_rows)

    # Tabla cruzada alumno × módulo
    tabla_cruzada = df_pivot.pivot_table(
        index="Nombre", columns="Modulo", values="Pct Modulo", fill_value=0
    ).reset_index()
else:
    df_pivot = pd.DataFrame()
    tabla_cruzada = pd.DataFrame()

# Lecciones pendientes detalladas
pendientes_detalle = df_activos[df_activos["Completada"] == "No"][
    ["Nombre", "Email", "Modulo", "Leccion"]
].copy()

# Métricas globales
total_alumnos    = len(resumen)
sin_actividad    = (resumen["Estado"] == "Sin actividad").sum()
en_riesgo        = (resumen["Estado"] == "En riesgo").sum()
en_progreso      = (resumen["Estado"] == "En progreso").sum()
avanzados        = (resumen["Estado"] == "Avanzado").sum()
avance_promedio  = round(resumen[resumen["Pct Avance"] > 0]["Pct Avance"].mean(), 1) if (resumen["Pct Avance"] > 0).any() else 0

# Módulo con mayor abandono
if not df_pivot.empty:
    abandono_modulo = df_pivot.groupby("Modulo")["Pendientes"].sum().sort_values(ascending=False)
    modulo_critico = abandono_modulo.index[0] if not abandono_modulo.empty else "---"
else:
    modulo_critico = "---"


# ─── KPIs ─────────────────────────────────────────────────────────────────────

st.markdown("---")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total alumnos",    total_alumnos)
c2.metric("Avance promedio",  f"{avance_promedio}%", help="Solo alumnos con actividad")
c3.metric("Sin actividad",    sin_actividad,  help="Nunca accedieron al Club")
c4.metric("En riesgo",        en_riesgo,      help="Menos del 30% completado")
c5.metric("En progreso",      en_progreso,    help="Entre 30% y 80%")
c6.metric("Avanzados",        avanzados,      help="Mas del 80% completado")
st.markdown("---")


# ─── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resumen general",
    "Punto de abandono",
    "Avance por modulo",
    "Lecciones pendientes",
    "Tabla cruzada"
])


# ── TAB 1: RESUMEN GENERAL ────────────────────────────────────────────────────

with tab1:
    col_left, col_right = st.columns(2)
    color_map = {
        "Sin actividad": "#e05151",
        "En riesgo":     "#f5a623",
        "En progreso":   "#4f9cf9",
        "Avanzado":      "#2ecc8f"
    }

    with col_left:
        st.subheader("Segmentacion de alumnos")
        seg = resumen["Estado"].value_counts().reset_index()
        seg.columns = ["Estado", "Cantidad"]
        fig_d = px.pie(seg, names="Estado", values="Cantidad",
                       hole=0.55, color="Estado", color_discrete_map=color_map)
        fig_d.update_traces(textposition="outside", textinfo="label+value")
        fig_d.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300,
                            paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_d, use_container_width=True)

    with col_right:
        st.subheader("Progreso por alumno")
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
            height=max(300, total_alumnos * 30),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_a, use_container_width=True)

    st.subheader("Detalle por alumno")
    st.dataframe(
        resumen[["Nombre", "Email", "Completadas", "Total lecciones", "Pct Avance", "Estado"]].sort_values("Pct Avance"),
        use_container_width=True, hide_index=True
    )


# ── TAB 2: PUNTO DE ABANDONO ──────────────────────────────────────────────────

with tab2:
    st.subheader("Donde se quedo cada alumno")
    st.caption("Muestra la ultima leccion completada y el modulo donde se atasco cada alumno.")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.markdown("**Alumnos sin ninguna actividad**")
        sin_act = resumen[resumen["Estado"] == "Sin actividad"][["Nombre", "Email"]]
        if sin_act.empty:
            st.success("Todos los alumnos han accedido al menos una vez.")
        else:
            st.error(f"{len(sin_act)} alumnos nunca accedieron al Club:")
            st.dataframe(sin_act, use_container_width=True, hide_index=True)

    with col_b:
        st.markdown("**Modulo critico (mayor cantidad de lecciones pendientes)**")
        if not df_pivot.empty:
            fig_crit = go.Figure(go.Bar(
                x=abandono_modulo.values,
                y=abandono_modulo.index,
                orientation="h",
                marker_color="#f5a623",
                text=abandono_modulo.values,
                textposition="outside"
            ))
            fig_crit.update_layout(
                xaxis_title="Lecciones pendientes acumuladas",
                yaxis=dict(autorange="reversed"),
                margin=dict(t=10, b=10, l=10, r=40),
                height=280,
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_crit, use_container_width=True)

    st.markdown("---")
    st.subheader("Ultima actividad por alumno")
    df_abandono = resumen[resumen["Estado"] != "Sin actividad"][[
        "Nombre", "Email", "Estado", "Pct Avance",
        "Ultimo modulo", "Ultima leccion", "Ultima actividad",
        "Modulo abandono", "Leccion abandono"
    ]].sort_values("Pct Avance")
    st.dataframe(df_abandono, use_container_width=True, hide_index=True)


# ── TAB 3: AVANCE POR MÓDULO ──────────────────────────────────────────────────

with tab3:
    st.subheader("Completitud por modulo (todos los alumnos)")
    st.caption("Porcentaje de lecciones completadas dentro de cada modulo, sumando todos los alumnos.")

    if not df_pivot.empty:
        mod_global = df_pivot.groupby("Modulo").agg(
            Lecciones=("Lecciones", "sum"),
            Completadas=("Completadas", "sum"),
            Pendientes=("Pendientes", "sum")
        ).reset_index()
        mod_global["Pct Global"] = round(mod_global["Completadas"] / mod_global["Lecciones"] * 100, 1)

        colors_mod = [
            "#2ecc8f" if p >= 60 else "#f5a623" if p >= 35 else "#e05151"
            for p in mod_global["Pct Global"]
        ]
        fig_mod = go.Figure(go.Bar(
            x=mod_global["Pct Global"],
            y=mod_global["Modulo"],
            orientation="h",
            marker_color=colors_mod,
            text=[f"{p}%" for p in mod_global["Pct Global"]],
            textposition="outside",
            customdata=mod_global[["Completadas", "Pendientes"]],
            hovertemplate="<b>%{y}</b><br>Completadas: %{customdata[0]}<br>Pendientes: %{customdata[1]}<extra></extra>"
        ))
        fig_mod.update_layout(
            xaxis=dict(range=[0, 115], ticksuffix="%"),
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10, b=10, l=10, r=50),
            height=max(280, len(mod_global) * 38),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_mod, use_container_width=True)

        st.markdown("---")
        st.subheader("Avance por alumno dentro de cada modulo")
        filtro_mod = st.selectbox("Selecciona un modulo", sorted(df_pivot["Modulo"].unique()))
        df_mod_fil = df_pivot[df_pivot["Modulo"] == filtro_mod].sort_values("Pct Modulo")
        fig_mod2 = go.Figure(go.Bar(
            x=df_mod_fil["Pct Modulo"],
            y=df_mod_fil["Nombre"],
            orientation="h",
            marker_color=[
                "#2ecc8f" if p >= 60 else "#f5a623" if p >= 35 else "#e05151"
                for p in df_mod_fil["Pct Modulo"]
            ],
            text=[f"{p}% ({int(c)}/{int(l)})" for p, c, l in zip(
                df_mod_fil["Pct Modulo"], df_mod_fil["Completadas"], df_mod_fil["Lecciones"]
            )],
            textposition="outside"
        ))
        fig_mod2.update_layout(
            xaxis=dict(range=[0, 125], ticksuffix="%"),
            margin=dict(t=10, b=10, l=10, r=80),
            height=max(300, len(df_mod_fil) * 32),
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=False
        )
        st.plotly_chart(fig_mod2, use_container_width=True)
    else:
        st.warning("No hay datos de modulos disponibles.")


# ── TAB 4: LECCIONES PENDIENTES ───────────────────────────────────────────────

with tab4:
    st.subheader("Lecciones pendientes por alumno")
    st.caption("Lista exacta de las clases que cada alumno NO ha completado todavia.")

    if not pendientes_detalle.empty:
        filtro_alumno = st.selectbox(
            "Selecciona un alumno",
            ["Todos"] + sorted(pendientes_detalle["Nombre"].unique().tolist())
        )
        df_pend_fil = (
            pendientes_detalle if filtro_alumno == "Todos"
            else pendientes_detalle[pendientes_detalle["Nombre"] == filtro_alumno]
        )
        st.dataframe(df_pend_fil, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_pend_fil)} lecciones pendientes en total")
    else:
        st.success("Todos los alumnos completaron todas las lecciones.")


# ── TAB 5: TABLA CRUZADA ──────────────────────────────────────────────────────

with tab5:
    st.subheader("Avance por alumno x modulo (%)")
    st.caption("Cada celda muestra el % de lecciones completadas de ese alumno en ese modulo. Util para ver de un vistazo quien se quedo en que parte.")

    if not tabla_cruzada.empty:
        st.dataframe(
            tabla_cruzada.set_index("Nombre").style.background_gradient(
                cmap="RdYlGn", vmin=0, vmax=100, axis=None
            ).format("{:.0f}%"),
            use_container_width=True
        )
    else:
        st.warning("No hay suficientes datos para generar la tabla cruzada.")


# ─── EXPORTAR ─────────────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("Exportar informe completo")

buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    resumen.to_excel(writer, sheet_name="Resumen por alumno", index=False)
    if not df_pivot.empty:
        df_pivot.to_excel(writer, sheet_name="Avance por modulo", index=False)
    if not tabla_cruzada.empty:
        tabla_cruzada.to_excel(writer, sheet_name="Tabla cruzada", index=False)
    if not pendientes_detalle.empty:
        pendientes_detalle.to_excel(writer, sheet_name="Lecciones pendientes", index=False)
    df.to_excel(writer, sheet_name="Detalle completo", index=False)
buffer.seek(0)

st.download_button(
    label="Descargar Excel completo (5 pestanas)",
    data=buffer,
    file_name=f"informe_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
