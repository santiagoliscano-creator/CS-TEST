"""
Hotmart Club - Dashboard de Progreso de Alumnos v4
Fix: user_id correcto + progreso base desde /users
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
    page_title="Hotmart - Progreso de Alumnos",
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
    try:
        resp = requests.post(url, headers=headers, data=body, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("access_token"), None
        return None, f"Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)


def get_modules(access_token, subdomain, is_extra=False):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://developers.hotmart.com/club/api/v1/modules?subdomain={subdomain}&is_extra={str(is_extra).lower()}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code in (200, 204):
            if not resp.text or not resp.text.strip():
                return [], "empty_body"
            try:
                data = resp.json()
                if isinstance(data, list):
                    return data, None
                elif isinstance(data, dict) and "items" in data:
                    return data["items"], None
                elif isinstance(data, dict):
                    return list(data.values())[0] if data else [], None
            except Exception:
                return [], f"JSON invalido: {resp.text[:300]}"
        return [], f"HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as e:
        return [], str(e)


def get_pages_for_module(access_token, subdomain, module_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://developers.hotmart.com/club/api/v2/modules/{module_id}/pages?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip():
                return [], None
            data = resp.json()
            if isinstance(data, list):
                return data, None
            elif isinstance(data, dict) and "items" in data:
                return data["items"], None
            elif isinstance(data, dict):
                return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}"
    except Exception as e:
        return [], str(e)


def get_students(access_token, subdomain):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip():
                return [], "Respuesta vacia"
            data = resp.json()
            if isinstance(data, list):
                return data, None
            elif isinstance(data, dict) and "items" in data:
                return data["items"], None
            elif isinstance(data, dict):
                return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as e:
        return [], str(e)


def get_student_progress(access_token, subdomain, user_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    url = (
        f"https://developers.hotmart.com/club/api/v1"
        f"/users/{user_id}/lessons?subdomain={subdomain}"
    )
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip():
                return [], None
            data = resp.json()
            if isinstance(data, dict):
                return data.get("lessons", data.get("items", [])), None
            elif isinstance(data, list):
                return data, None
            return [], f"Estructura inesperada: {str(data)[:200]}"
        elif resp.status_code == 204:
            return [], None
        return [], f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return [], str(e)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def estado_riesgo(pct):
    if pct == 0:  return "Sin actividad"
    if pct < 30:  return "En riesgo"
    if pct < 80:  return "En progreso"
    return "Avanzado"

color_map = {
    "Sin actividad": "#e05151",
    "En riesgo":     "#f5a623",
    "En progreso":   "#4f9cf9",
    "Avanzado":      "#2ecc8f"
}

def calcular_abandono(df_alumno):
    completadas = df_alumno[df_alumno["Completada"] == "Si"].sort_values("Fecha Completado", ascending=False)
    pendientes  = df_alumno[df_alumno["Completada"] == "No"]
    ul = completadas.iloc[0]["Leccion"]          if not completadas.empty else "Sin actividad"
    um = completadas.iloc[0]["Modulo"]           if not completadas.empty else "Sin actividad"
    uf = completadas.iloc[0]["Fecha Completado"] if not completadas.empty else ""
    ma = pendientes.iloc[0]["Modulo"]            if not pendientes.empty else "Completado"
    la = pendientes.iloc[0]["Leccion"]           if not pendientes.empty else "Completado"
    return ul, um, uf, ma, la


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Credenciales del cliente")
    st.markdown("---")
    basic_token   = st.text_input("Basic Token",         placeholder="Basic NTM5OWZlMD...")
    client_id     = st.text_input("Client ID",           placeholder="5399fe00-f707-...")
    client_secret = st.text_input("Client Secret",       type="password", placeholder="ae15213e...")
    subdomain     = st.text_input("Subdominio del Club", placeholder="agencypro")
    st.markdown("---")
    cargar_modulos = st.button("1. Cargar modulos del Club", use_container_width=True)
    st.markdown("---")
    st.markdown("**Subdominio:** lo que aparece en")
    st.markdown("`hotmart.com/es/club/`**subdominio**")


# ─── HEADER ───────────────────────────────────────────────────────────────────

st.markdown("# Hotmart Club - Progreso de Alumnos")
st.markdown(f"Club: **{subdomain or '---'}** · {datetime.now().strftime('%d/%m/%Y %H:%M')}")

if not all([basic_token, client_id, client_secret, subdomain]):
    st.info("Completa las credenciales en el panel izquierdo y haz clic en **1. Cargar modulos del Club**.")
    st.stop()


# ─── PASO 1: CARGAR MÓDULOS ───────────────────────────────────────────────────

if cargar_modulos:
    with st.spinner("Autenticando y cargando modulos..."):

        token, err = get_access_token(basic_token, client_id, client_secret)
        if err:
            st.error(f"Error de autenticacion: {err}")
            st.stop()
        st.success("Token obtenido correctamente.")

        modulos_main,  err_m  = get_modules(token, subdomain, is_extra=False)
        modulos_extra, err_me = get_modules(token, subdomain, is_extra=True)
        todos_modulos = modulos_main + modulos_extra

        modulo_info = {}

        if not todos_modulos:
            st.warning(f"Endpoint /modules vacio. Extrayendo modulos desde progreso de alumnos...")
            students_tmp, err_st = get_students(token, subdomain)
            st.write(f"- /users → {len(students_tmp)} alumnos | Error: `{err_st}`")

            if not students_tmp:
                st.error("Lista de alumnos vacia. Verifica las credenciales y el subdominio.")
                st.stop()

            nombres_modulos_tmp = set()
            for s in students_tmp[:20]:
                # ✅ FIX: usar user_id, no id
                uid = s.get("user_id", s.get("id", ""))
                if not uid:
                    continue
                lecs, _ = get_student_progress(token, subdomain, uid)
                for l in lecs:
                    m = l.get("module_name", "")
                    if m:
                        nombres_modulos_tmp.add(m)
                time.sleep(0.15)

            for nombre in sorted(nombres_modulos_tmp):
                modulo_info[nombre] = {
                    "module_id":   "",
                    "total_pages": 0,
                    "is_extra":    False,
                    "is_public":   True
                }

            if modulo_info:
                st.info(f"Modulos extraidos via fallback: {list(modulo_info.keys())}")
            else:
                st.error("No se encontraron modulos.")
                st.stop()

        else:
            for m in todos_modulos:
                mid  = m.get("module_id", m.get("id", ""))
                name = m.get("name", f"Modulo {mid}")
                pages, _ = get_pages_for_module(token, subdomain, mid)
                total_pages = len([
                    p for p in pages
                    if p.get("type", "CONTENT") != "ADVERTISEMENT"
                ]) if pages else 0
                modulo_info[name] = {
                    "module_id":   mid,
                    "total_pages": total_pages,
                    "is_extra":    m.get("is_extra", False),
                    "is_public":   m.get("is_public", False)
                }

        if not modulo_info:
            st.error("No se pudieron cargar los modulos.")
            st.stop()

        st.session_state["token"]       = token
        st.session_state["modulo_info"] = modulo_info
        st.session_state["subdomain"]   = subdomain

    st.success(f"{len(modulo_info)} modulos cargados correctamente.")

if "modulo_info" not in st.session_state:
    st.info("Haz clic en **1. Cargar modulos del Club** para continuar.")
    st.stop()

modulo_info = st.session_state["modulo_info"]
token       = st.session_state["token"]


# ─── PASO 2: SELECTOR DE MÓDULOS ──────────────────────────────────────────────

st.markdown("---")
st.subheader("Selecciona los modulos a analizar")
st.caption("Agrupa los modulos que pertenecen al mismo producto para filtrar el reporte.")

col_sel, col_info = st.columns([2, 1])

with col_sel:
    nombres_modulos = list(modulo_info.keys())
    modulos_seleccionados = st.multiselect(
        "Modulos incluidos en el analisis",
        options=nombres_modulos,
        default=nombres_modulos,
        help="Selecciona solo los modulos del producto que quieres analizar"
    )

with col_info:
    st.markdown("**Estructura del Club:**")
    for nombre, info in modulo_info.items():
        tipo      = "Extra" if info["is_extra"] else "Principal"
        pages     = info["total_pages"]
        check     = "✅" if nombre in modulos_seleccionados else "⬜"
        pages_txt = f"· {pages} lecciones" if pages > 0 else ""
        st.markdown(f"{check} `{tipo}` **{nombre}** {pages_txt}")

if not modulos_seleccionados:
    st.warning("Selecciona al menos un modulo para continuar.")
    st.stop()

total_lecciones_reales = sum(modulo_info[m]["total_pages"] for m in modulos_seleccionados)
usar_total_real = total_lecciones_reales > 0

if usar_total_real:
    st.info(f"**{len(modulos_seleccionados)} modulos** · **{total_lecciones_reales} lecciones** en total")
else:
    st.info(f"**{len(modulos_seleccionados)} modulos** seleccionados · El % se calculara sobre lecciones registradas por alumno.")

generar = st.button("2. Generar Dashboard", type="primary")

if not generar:
    st.stop()


# ─── PASO 3: EXTRACCIÓN ───────────────────────────────────────────────────────

with st.status("Extrayendo progreso de alumnos...", expanded=True) as status:

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
        # ✅ FIX: usar user_id, no id
        uid   = student.get("user_id", student.get("id", ""))
        name  = student.get("name", "Sin nombre")
        email = student.get("email", "")

        # Progreso global ya viene en /users — lo usamos como fallback
        prog_obj      = student.get("progress", {})
        pct_hotmart   = prog_obj.get("completed_percentage", 0)
        total_hotmart = prog_obj.get("total", 0)
        comp_hotmart  = prog_obj.get("completed", 0)

        if not uid:
            errores.append({"alumno": name, "error": "user_id vacio"})
            continue

        lecciones, err_l = get_student_progress(token, subdomain, uid)
        if err_l:
            errores.append({"alumno": name, "error": err_l})

        if not lecciones:
            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           "Sin actividad",
                "Leccion":          "Sin actividad",
                "Completada":       "No",
                "Fecha Completado": "",
                "Pct Hotmart":      pct_hotmart
            })
            progress_bar.progress((i + 1) / len(students))
            time.sleep(0.2)
            continue

        for l in lecciones:
            modulo_nombre = l.get("module_name", "Sin modulo")
            if modulo_nombre not in modulos_seleccionados:
                continue
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(
                    l["completed_date"] / 1000
                ).strftime("%d/%m/%Y")
            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           modulo_nombre,
                "Leccion":          l.get("page_name", "Sin nombre"),
                "Completada":       "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha,
                "Pct Hotmart":      pct_hotmart
            })

        progress_bar.progress((i + 1) / len(students))
        time.sleep(0.2)

    status.update(label="Extraccion completa", state="complete")

if errores:
    with st.expander(f"{len(errores)} alumnos con error de API"):
        st.dataframe(pd.DataFrame(errores), use_container_width=True)

if not all_data:
    st.warning("No se encontraron datos para los modulos seleccionados.")
    st.stop()


# ─── PROCESAMIENTO ────────────────────────────────────────────────────────────

df = pd.DataFrame(all_data)
df_activos = df[df["Modulo"] != "Sin actividad"]

resumen_rows = []
for nombre, grupo in df.groupby("Nombre"):
    email        = grupo["Email"].iloc[0]
    pct_hotmart  = grupo["Pct Hotmart"].iloc[0]
    grupo_activo = grupo[grupo["Modulo"] != "Sin actividad"]

    if grupo_activo.empty:
        # Usamos el % de Hotmart si no hay detalle de lecciones
        pct    = float(pct_hotmart) if pct_hotmart else 0.0
        estado = estado_riesgo(pct)
        resumen_rows.append({
            "Nombre": nombre, "Email": email,
            "Completadas": 0, "Total": total_lecciones_reales if usar_total_real else 0,
            "Sin completar": total_lecciones_reales if usar_total_real else 0,
            "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
            "Estado": estado,
            "Ultima leccion": "Sin detalle disponible",
            "Ultimo modulo": "---", "Ultima actividad": "---",
            "Modulo abandono": "---", "Leccion abandono": "---"
        })
        continue

    completadas_n = int((grupo_activo["Completada"] == "Si").sum())
    total_n       = total_lecciones_reales if usar_total_real else len(grupo_activo)
    pct           = round(completadas_n / total_n * 100, 1) if total_n > 0 else 0.0
    pct           = min(pct, 100.0)
    estado        = estado_riesgo(pct)
    ul, um, uf, ma, la = calcular_abandono(grupo_activo)

    resumen_rows.append({
        "Nombre": nombre, "Email": email,
        "Completadas": completadas_n, "Total": total_n,
        "Sin completar": max(0, total_n - completadas_n),
        "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
        "Estado": estado,
        "Ultima leccion": ul, "Ultimo modulo": um,
        "Ultima actividad": uf, "Modulo abandono": ma, "Leccion abandono": la
    })

resumen = pd.DataFrame(resumen_rows)

pivot_rows = []
for m in modulos_seleccionados:
    total_m_real = modulo_info[m]["total_pages"]
    df_m = df_activos[df_activos["Modulo"] == m]
    for nombre, g in df_m.groupby("Nombre"):
        comp_m  = int((g["Completada"] == "Si").sum())
        total_m = total_m_real if total_m_real > 0 else len(g)
        pct_m   = round(comp_m / total_m * 100, 1) if total_m > 0 else 0.0
        pct_m   = min(pct_m, 100.0)
        pivot_rows.append({
            "Nombre": nombre, "Modulo": m,
            "Completadas": comp_m, "Total modulo": total_m,
            "Pendientes": max(0, total_m - comp_m), "Pct Modulo": pct_m
        })

df_pivot = pd.DataFrame(pivot_rows) if pivot_rows else pd.DataFrame()
tabla_cruzada = (
    df_pivot.pivot_table(index="Nombre", columns="Modulo", values="Pct Modulo", fill_value=0).reset_index()
    if not df_pivot.empty else pd.DataFrame()
)
pendientes_detalle = df_activos[df_activos["Completada"] == "No"][
    ["Nombre", "Email", "Modulo", "Leccion"]
].copy()

total_alumnos = len(resumen)
sin_actividad = (resumen["Estado"] == "Sin actividad").sum()
en_riesgo     = (resumen["Estado"] == "En riesgo").sum()
en_progreso   = (resumen["Estado"] == "En progreso").sum()
avanzados     = (resumen["Estado"] == "Avanzado").sum()
avance_prom   = round(resumen[resumen["Pct Avance"] > 0]["Pct Avance"].mean(), 1) if (resumen["Pct Avance"] > 0).any() else 0
abandono_modulo = (
    df_pivot.groupby("Modulo")["Pendientes"].sum().sort_values(ascending=False)
    if not df_pivot.empty else pd.Series(dtype=float)
)


# ─── KPIs ─────────────────────────────────────────────────────────────────────

st.markdown("---")
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total alumnos",   total_alumnos)
c2.metric("Avance promedio", f"{avance_prom}%")
c3.metric("Sin actividad",   sin_actividad)
c4.metric("En riesgo",       en_riesgo)
c5.metric("En progreso",     en_progreso)
c6.metric("Avanzados",       avanzados)
st.markdown("---")


# ─── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Resumen general",
    "Punto de abandono",
    "Avance por modulo",
    "Lecciones pendientes",
    "Tabla cruzada"
])

with tab1:
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("Segmentacion")
        seg = resumen["Estado"].value_counts().reset_index()
        seg.columns = ["Estado", "Cantidad"]
        fig_d = px.pie(seg, names="Estado", values="Cantidad",
                       hole=0.55, color="Estado", color_discrete_map=color_map)
        fig_d.update_traces(textposition="outside", textinfo="label+value")
        fig_d.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=300,
                            paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_d, use_container_width=True)
    with col_r:
        st.subheader("Progreso por alumno")
        sorted_r = resumen.sort_values("Pct Avance", ascending=True)
        fig_a = go.Figure(go.Bar(
            x=sorted_r["Pct Avance"], y=sorted_r["Nombre"],
            orientation="h",
            marker_color=[color_map[e] for e in sorted_r["Estado"]],
            text=[f"{p}%" for p in sorted_r["Pct Avance"]],
            textposition="outside",
            customdata=sorted_r[["Completadas","Total","Pct Hotmart"]],
            hovertemplate="<b>%{y}</b><br>Nuestro: %{x}%<br>Hotmart: %{customdata[2]}%<br>%{customdata[0]}/%{customdata[1]} lecciones<extra></extra>"
        ))
        fig_a.update_layout(
            xaxis=dict(range=[0,115], ticksuffix="%"),
            margin=dict(t=10,b=10,l=10,r=60),
            height=max(300, total_alumnos*30),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False
        )
        st.plotly_chart(fig_a, use_container_width=True)

    st.subheader("Detalle por alumno")
    st.dataframe(
        resumen[["Nombre","Email","Completadas","Total","Pct Avance","Pct Hotmart","Estado"]].sort_values("Pct Avance"),
        use_container_width=True, hide_index=True
    )

with tab2:
    st.subheader("Donde se quedo cada alumno")
    col_a, col_b = st.columns([1,1])
    with col_a:
        st.markdown("**Alumnos sin ninguna actividad**")
        sin_act = resumen[resumen["Estado"] == "Sin actividad"][["Nombre","Email","Pct Hotmart"]]
        if sin_act.empty:
            st.success("Todos los alumnos han accedido al menos una vez.")
        else:
            st.error(f"{len(sin_act)} alumnos sin detalle de lecciones:")
            st.dataframe(sin_act, use_container_width=True, hide_index=True)
    with col_b:
        st.markdown("**Modulos con mas lecciones pendientes**")
        if not abandono_modulo.empty:
            fig_crit = go.Figure(go.Bar(
                x=abandono_modulo.values, y=abandono_modulo.index,
                orientation="h", marker_color="#f5a623",
                text=abandono_modulo.values, textposition="outside"
            ))
            fig_crit.update_layout(
                xaxis_title="Lecciones pendientes acumuladas",
                yaxis=dict(autorange="reversed"),
                margin=dict(t=10,b=10,l=10,r=40), height=280,
                paper_bgcolor="rgba(0,0,0,0)", showlegend=False
            )
            st.plotly_chart(fig_crit, use_container_width=True)
    st.markdown("---")
    st.subheader("Ultima actividad y punto de abandono")
    df_ab = resumen[resumen["Ultimo modulo"] != "---"][[
        "Nombre","Email","Estado","Pct Avance","Pct Hotmart",
        "Ultimo modulo","Ultima leccion","Ultima actividad",
        "Modulo abandono","Leccion abandono"
    ]].sort_values("Pct Avance")
    st.dataframe(df_ab, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Completitud por modulo")
    if not df_pivot.empty:
        mod_global = df_pivot.groupby("Modulo").agg(
            Completadas=("Completadas","sum"),
            Pendientes=("Pendientes","sum"),
            Total=("Total modulo","first")
        ).reset_index()
        mod_global["Pct Global"] = (
            mod_global["Completadas"] / (mod_global["Total"] * total_alumnos) * 100
        ).clip(0, 100).round(1)
        fig_mod = go.Figure(go.Bar(
            x=mod_global["Pct Global"], y=mod_global["Modulo"],
            orientation="h",
            marker_color=["#2ecc8f" if p>=60 else "#f5a623" if p>=35 else "#e05151" for p in mod_global["Pct Global"]],
            text=[f"{p}%" for p in mod_global["Pct Global"]],
            textposition="outside"
        ))
        fig_mod.update_layout(
            xaxis=dict(range=[0,115], ticksuffix="%"),
            yaxis=dict(autorange="reversed"),
            margin=dict(t=10,b=10,l=10,r=50),
            height=max(280, len(mod_global)*40),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False
        )
        st.plotly_chart(fig_mod, use_container_width=True)
        st.markdown("---")
        st.subheader("Avance por alumno en un modulo especifico")
        filtro_mod = st.selectbox("Selecciona el modulo", sorted(df_pivot["Modulo"].unique()))
        df_mf = df_pivot[df_pivot["Modulo"]==filtro_mod].sort_values("Pct Modulo")
        fig_m2 = go.Figure(go.Bar(
            x=df_mf["Pct Modulo"], y=df_mf["Nombre"],
            orientation="h",
            marker_color=["#2ecc8f" if p>=60 else "#f5a623" if p>=35 else "#e05151" for p in df_mf["Pct Modulo"]],
            text=[f"{p}% ({int(c)}/{int(t)})" for p,c,t in zip(df_mf["Pct Modulo"],df_mf["Completadas"],df_mf["Total modulo"])],
            textposition="outside"
        ))
        fig_m2.update_layout(
            xaxis=dict(range=[0,125], ticksuffix="%"),
            margin=dict(t=10,b=10,l=10,r=100),
            height=max(300, len(df_mf)*34),
            paper_bgcolor="rgba(0,0,0,0)", showlegend=False
        )
        st.plotly_chart(fig_m2, use_container_width=True)
    else:
        st.warning("No hay datos de modulos disponibles.")

with tab4:
    st.subheader("Lecciones pendientes por alumno")
    if not pendientes_detalle.empty:
        filtro_alumno = st.selectbox(
            "Selecciona un alumno",
            ["Todos"] + sorted(pendientes_detalle["Nombre"].unique().tolist())
        )
        df_pf = pendientes_detalle if filtro_alumno == "Todos" else pendientes_detalle[pendientes_detalle["Nombre"]==filtro_alumno]
        st.dataframe(df_pf, use_container_width=True, hide_index=True)
        st.caption(f"{len(df_pf)} lecciones pendientes")
    else:
        st.success("Todos los alumnos completaron todas las lecciones.")

with tab5:
    st.subheader("Avance alumno x modulo (%)")
    st.caption("Verde = avanzado · Amarillo = en progreso · Rojo = en riesgo o sin iniciar")
    if not tabla_cruzada.empty:
        st.dataframe(
            tabla_cruzada.set_index("Nombre").style.background_gradient(
                cmap="RdYlGn", vmin=0, vmax=100, axis=None
            ).format("{:.0f}%"),
            use_container_width=True
        )
    else:
        st.warning("No hay suficientes datos para la tabla cruzada.")


# ─── EXPORTAR ─────────────────────────────────────────────────────────────────

st.markdown("---")
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
