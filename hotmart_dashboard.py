"""
Hotmart Club · Club Analytics v5
Branded · Login screen · Multi-page flow
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import io
import matplotlib

st.set_page_config(
    page_title="Hotmart · Club Analytics",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ESTILOS GLOBALES ─────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800;900&display=swap');

* {
    font-family: 'Nunito Sans', sans-serif !important;
}

/* Ocultar sidebar y elementos de Streamlit */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
.stDeployButton { display: none !important; }

/* Fondo general */
.stApp {
    background: #faf9f7 !important;
}

/* Botones primarios */
.stButton > button[kind="primary"] {
    background: #E8420A !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 12px 28px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(232, 66, 10, 0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #c93608 !important;
    box-shadow: 0 6px 20px rgba(232, 66, 10, 0.4) !important;
    transform: translateY(-1px) !important;
}

/* Botones secundarios */
.stButton > button:not([kind="primary"]) {
    background: white !important;
    color: #E8420A !important;
    border: 2px solid #E8420A !important;
    border-radius: 10px !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: #fff5f2 !important;
}

/* Inputs */
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #e0ddd8 !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    background: white !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: #E8420A !important;
    box-shadow: 0 0 0 3px rgba(232,66,10,0.1) !important;
}

/* Labels de inputs */
.stTextInput label {
    font-weight: 600 !important;
    color: #3d3a35 !important;
    font-size: 13px !important;
}

/* Métricas */
[data-testid="stMetric"] {
    background: white !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
    border: 1px solid #f0ede8 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 12px !important;
    font-weight: 700 !important;
    color: #8c8880 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricValue"] {
    font-size: 28px !important;
    font-weight: 800 !important;
    color: #1a1815 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: #f0ede8 !important;
    border-radius: 12px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: #8c8880 !important;
    padding: 8px 16px !important;
}
.stTabs [aria-selected="true"] {
    background: white !important;
    color: #E8420A !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* Selectbox */
.stSelectbox > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #e0ddd8 !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    border-radius: 10px !important;
    border: 1.5px solid #e0ddd8 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* Expander */
.streamlit-expanderHeader {
    font-weight: 700 !important;
    color: #3d3a35 !important;
}

/* Status box */
[data-testid="stStatusWidget"] {
    border-radius: 12px !important;
}

/* Progress bar */
.stProgress > div > div > div {
    background: #E8420A !important;
}

/* Alerts */
.stSuccess {
    background: #f0faf5 !important;
    border-left-color: #1aab6d !important;
    border-radius: 10px !important;
}
.stError {
    background: #fff5f2 !important;
    border-left-color: #E8420A !important;
    border-radius: 10px !important;
}
.stWarning {
    background: #fffbf0 !important;
    border-radius: 10px !important;
}
.stInfo {
    background: #f5f0ff !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)


# ─── FUNCIONES DE API ─────────────────────────────────────────────────────────

def get_access_token(basic_token, client_id, client_secret):
    url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": basic_token}
    body = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}
    try:
        resp = requests.post(url, headers=headers, data=body, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("access_token"), None
        return None, f"Error {resp.status_code}: {resp.text}"
    except Exception as e:
        return None, str(e)


def get_modules(access_token, subdomain, is_extra=False):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://developers.hotmart.com/club/api/v1/modules?subdomain={subdomain}&is_extra={str(is_extra).lower()}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code in (200, 204):
            if not resp.text or not resp.text.strip():
                return [], "empty_body"
            data = resp.json()
            if isinstance(data, list): return data, None
            elif isinstance(data, dict) and "items" in data: return data["items"], None
            elif isinstance(data, dict): return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return [], str(e)


def get_pages_for_module(access_token, subdomain, module_id):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://developers.hotmart.com/club/api/v2/modules/{module_id}/pages?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip(): return [], None
            data = resp.json()
            if isinstance(data, list): return data, None
            elif isinstance(data, dict) and "items" in data: return data["items"], None
            elif isinstance(data, dict): return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}"
    except Exception as e:
        return [], str(e)


def get_students(access_token, subdomain):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip(): return [], "Respuesta vacia"
            data = resp.json()
            if isinstance(data, list): return data, None
            elif isinstance(data, dict) and "items" in data: return data["items"], None
            elif isinstance(data, dict): return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return [], str(e)


def get_student_progress(access_token, subdomain, user_id):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://developers.hotmart.com/club/api/v1/users/{user_id}/lessons?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip(): return [], None
            data = resp.json()
            if isinstance(data, dict): return data.get("lessons", data.get("items", [])), None
            elif isinstance(data, list): return data, None
            return [], f"Estructura inesperada: {str(data)[:200]}"
        elif resp.status_code == 204: return [], None
        return [], f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return [], str(e)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def estado_riesgo(pct):
    if pct == 0:  return "Sin actividad"
    if pct < 30:  return "En riesgo"
    if pct < 80:  return "En progreso"
    return "Avanzado"

COLOR_MAP = {
    "Sin actividad": "#ffb3a0",
    "En riesgo":     "#ff7c4d",
    "En progreso":   "#E8420A",
    "Avanzado":      "#b83208"
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


# ─── SESSION STATE INIT ───────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state["page"] = "login"
if "token" not in st.session_state:
    st.session_state["token"] = None
if "modulo_info" not in st.session_state:
    st.session_state["modulo_info"] = {}
if "subdomain" not in st.session_state:
    st.session_state["subdomain"] = ""
if "club_name" not in st.session_state:
    st.session_state["club_name"] = ""
if "modulos_seleccionados" not in st.session_state:
    st.session_state["modulos_seleccionados"] = []
if "dashboard_data" not in st.session_state:
    st.session_state["dashboard_data"] = None


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — LOGIN
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state["page"] == "login":

    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:

        st.markdown("<div style='height: 48px'></div>", unsafe_allow_html=True)

        # Logo + título
        st.markdown("""
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="display:inline-flex; align-items:center; justify-content:center;
                        width:56px; height:56px; background:#E8420A; border-radius:16px;
                        margin-bottom:16px; box-shadow: 0 8px 24px rgba(232,66,10,0.35);">
                <span style="font-size:28px;">🔥</span>
            </div>
            <h1 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:26px;
                       color:#1a1815; margin:0; line-height:1.2;">Club Analytics</h1>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px;
                      margin-top:6px;">Analiza el progreso de tus alumnos en Hotmart Club</p>
        </div>
        """, unsafe_allow_html=True)

        # Card de login
        st.markdown("""
        <div style="background:white; border-radius:20px; padding:36px;
                    box-shadow: 0 8px 40px rgba(0,0,0,0.08); border: 1px solid #f0ede8;">
        """, unsafe_allow_html=True)

        st.markdown("""
        <p style="font-family:'Nunito Sans',sans-serif; font-weight:700; font-size:16px;
                   color:#1a1815; margin-bottom:4px;">Conecta tu Club</p>
        <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:13px;
                   margin-bottom:24px;">Ingresa tus credenciales de Hotmart Developers</p>
        """, unsafe_allow_html=True)

        basic_token   = st.text_input("Basic Token", placeholder="Basic NTM5OWZlMD...", key="l_basic")
        client_id     = st.text_input("Client ID",   placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", key="l_cid")
        client_secret = st.text_input("Client Secret", placeholder="••••••••••••••••", type="password", key="l_secret")
        subdomain     = st.text_input("Subdominio del Club", placeholder="mi-curso", key="l_sub",
                                      help="Lo que aparece en hotmart.com/es/club/SUBDOMINIO")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        conectar = st.button("Conectar y ver Analytics →", type="primary", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Ayuda
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <p style="font-family:'Nunito Sans',sans-serif; color:#b8b4ae; font-size:12px;">
                ¿Cómo obtener mis credenciales?
                Entra a <strong style="color:#E8420A;">developers.hotmart.com</strong> →
                crea una aplicación → copia tus credenciales
            </p>
        </div>
        """, unsafe_allow_html=True)

        if conectar:
            if not all([basic_token, client_id, client_secret, subdomain]):
                st.error("Por favor completa todos los campos.")
            else:
                with st.spinner("Verificando credenciales..."):
                    token, err = get_access_token(basic_token, client_id, client_secret)
                    if err:
                        st.error(f"Credenciales incorrectas: {err}")
                    else:
                        # Cargar módulos
                        mods_main,  _ = get_modules(token, subdomain, is_extra=False)
                        mods_extra, _ = get_modules(token, subdomain, is_extra=True)
                        todos = mods_main + mods_extra
                        modulo_info = {}

                        if todos:
                            for m in todos:
                                mid  = m.get("module_id", m.get("id", ""))
                                name = m.get("name", f"Modulo {mid}")
                                pages, _ = get_pages_for_module(token, subdomain, mid)
                                total_pages = len([
                                    p for p in pages
                                    if p.get("type", "CONTENT") != "ADVERTISEMENT"
                                ]) if pages else 0
                                modulo_info[name] = {
                                    "module_id": mid,
                                    "total_pages": total_pages,
                                    "is_extra": m.get("is_extra", False)
                                }
                        else:
                            # Fallback: extraer módulos desde progreso
                            students_tmp, _ = get_students(token, subdomain)
                            nombres_tmp = set()
                            for s in students_tmp[:15]:
                                uid = s.get("user_id", s.get("id", ""))
                                if not uid: continue
                                lecs, _ = get_student_progress(token, subdomain, uid)
                                for l in lecs:
                                    m = l.get("module_name", "")
                                    if m: nombres_tmp.add(m)
                                time.sleep(0.15)
                            for nombre in sorted(nombres_tmp):
                                modulo_info[nombre] = {"module_id": "", "total_pages": 0, "is_extra": False}

                        if not modulo_info:
                            st.error("No se encontraron módulos. Verifica el subdominio.")
                        else:
                            st.session_state["token"]     = token
                            st.session_state["modulo_info"] = modulo_info
                            st.session_state["subdomain"] = subdomain
                            st.session_state["club_name"] = subdomain.replace("-", " ").title()
                            st.session_state["page"]      = "selector"
                            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — SELECTOR DE MÓDULOS
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "selector":

    token       = st.session_state["token"]
    modulo_info = st.session_state["modulo_info"]
    subdomain   = st.session_state["subdomain"]
    club_name   = st.session_state["club_name"]

    # Header
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between;
                padding: 20px 0 28px; border-bottom: 2px solid #f0ede8; margin-bottom:32px;">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="width:42px; height:42px; background:#E8420A; border-radius:12px;
                        display:flex; align-items:center; justify-content:center;
                        box-shadow:0 4px 12px rgba(232,66,10,0.3);">
                <span style="font-size:20px;">🔥</span>
            </div>
            <div>
                <div style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:20px;
                            color:#1a1815;">Club Analytics</div>
                <div style="font-family:'Nunito Sans',sans-serif; font-size:13px; color:#8c8880;">
                    {club_name} · {len(modulo_info)} módulos encontrados
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <h2 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px;
               color:#1a1815; margin-bottom:8px;">¿Qué producto quieres analizar?</h2>
    <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px; margin-bottom:28px;">
        Selecciona los módulos que pertenecen al producto que quieres revisar.
        Si tu Club tiene un solo producto, selecciónalos todos.
    </p>
    """, unsafe_allow_html=True)

    col_sel, col_preview = st.columns([1.3, 1])

    with col_sel:
        nombres = list(modulo_info.keys())
        seleccionados = st.multiselect(
            "Módulos a incluir",
            options=nombres,
            default=nombres,
            help="Puedes seleccionar solo los módulos de un producto específico"
        )

        total_lecciones = sum(modulo_info[m]["total_pages"] for m in seleccionados)

        if seleccionados:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #fff5f2, #fff); border: 1.5px solid #ffd4c4;
                        border-radius: 14px; padding: 18px 20px; margin-top: 16px;">
                <div style="font-family:'Nunito Sans',sans-serif; font-size:13px; color:#E8420A;
                            font-weight:700; margin-bottom:4px;">RESUMEN DE SELECCIÓN</div>
                <div style="font-family:'Nunito Sans',sans-serif; font-size:24px; font-weight:800;
                            color:#1a1815;">{len(seleccionados)} módulos</div>
                {'<div style="font-family:Nunito Sans,sans-serif; font-size:14px; color:#8c8880;">' +
                 str(total_lecciones) + ' lecciones en total</div>' if total_lecciones > 0 else ''}
            </div>
            """, unsafe_allow_html=True)

    with col_preview:
        st.markdown("""
        <div style="font-family:'Nunito Sans',sans-serif; font-weight:700; font-size:13px;
                    color:#8c8880; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:12px;">
            MÓDULOS DISPONIBLES
        </div>
        """, unsafe_allow_html=True)

        for nombre, info in modulo_info.items():
            activo = nombre in seleccionados
            pages  = info["total_pages"]
            extra  = "· Extra" if info["is_extra"] else ""
            color_bg = "#fff5f2" if activo else "#faf9f7"
            color_border = "#ffd4c4" if activo else "#f0ede8"
            color_dot = "#E8420A" if activo else "#d0cdc8"
            pages_txt = f" · {pages} clases" if pages > 0 else ""

            st.markdown(f"""
            <div style="background:{color_bg}; border:1.5px solid {color_border};
                        border-radius:10px; padding:10px 14px; margin-bottom:8px;
                        display:flex; align-items:center; gap:10px;">
                <div style="width:8px; height:8px; border-radius:50%; background:{color_dot}; flex-shrink:0;"></div>
                <div>
                    <div style="font-family:'Nunito Sans',sans-serif; font-weight:700; font-size:13px;
                                color:#1a1815;">{nombre}</div>
                    <div style="font-family:'Nunito Sans',sans-serif; font-size:11px;
                                color:#b8b4ae;">Principal{extra}{pages_txt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    col_back, col_spacer, col_go = st.columns([1, 2, 1])

    with col_back:
        if st.button("← Volver", use_container_width=True):
            st.session_state["page"] = "login"
            st.rerun()

    with col_go:
        if st.button("Generar Dashboard →", type="primary", use_container_width=True, disabled=not seleccionados):
            st.session_state["modulos_seleccionados"] = seleccionados
            st.session_state["page"] = "loading"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CARGA DE DATOS
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "loading":

    token               = st.session_state["token"]
    modulo_info         = st.session_state["modulo_info"]
    subdomain           = st.session_state["subdomain"]
    modulos_sel         = st.session_state["modulos_seleccionados"]
    total_lec_reales    = sum(modulo_info[m]["total_pages"] for m in modulos_sel)
    usar_total_real     = total_lec_reales > 0

    col_c1, col_c2, col_c3 = st.columns([1, 1.5, 1])
    with col_c2:
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
            <div style="font-size:40px; margin-bottom:16px;">🔥</div>
            <h2 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px;
                       color:#1a1815; margin-bottom:8px;">Analizando tu Club...</h2>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px;">
                Estamos extrayendo el progreso de cada alumno.<br>Esto puede tomar unos segundos.
            </p>
        </div>
        """, unsafe_allow_html=True)

        status_text = st.empty()
        prog_bar    = st.progress(0)

    status_text.markdown("""
    <p style="font-family:'Nunito Sans',sans-serif; text-align:center; color:#8c8880; font-size:13px;">
        Obteniendo lista de alumnos...
    </p>""", unsafe_allow_html=True)

    students, err2 = get_students(token, subdomain)
    if not students:
        with col_c2:
            st.error(f"No se pudo obtener la lista de alumnos: {err2}")
            if st.button("← Volver"):
                st.session_state["page"] = "selector"
                st.rerun()
        st.stop()

    all_data = []
    errores  = []

    for i, student in enumerate(students):
        uid          = student.get("user_id", student.get("id", ""))
        name         = student.get("name", "Sin nombre")
        email        = student.get("email", "")
        prog_obj     = student.get("progress", {})
        pct_hotmart  = prog_obj.get("completed_percentage", 0)

        pct_done = (i + 1) / len(students)
        prog_bar.progress(pct_done)
        status_text.markdown(f"""
        <p style="font-family:'Nunito Sans',sans-serif; text-align:center; color:#8c8880; font-size:13px;">
            Analizando {i+1} de {len(students)} alumnos...
        </p>""", unsafe_allow_html=True)

        if not uid:
            errores.append({"alumno": name, "error": "user_id vacio"})
            continue

        lecciones, err_l = get_student_progress(token, subdomain, uid)
        if err_l:
            errores.append({"alumno": name, "error": err_l})

        if not lecciones:
            all_data.append({
                "Nombre": name, "Email": email,
                "Modulo": "Sin actividad", "Leccion": "Sin actividad",
                "Completada": "No", "Fecha Completado": "",
                "Pct Hotmart": pct_hotmart
            })
            time.sleep(0.15)
            continue

        for l in lecciones:
            modulo_nombre = l.get("module_name", "Sin modulo")
            if modulo_nombre not in modulos_sel:
                continue
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(l["completed_date"] / 1000).strftime("%d/%m/%Y")
            all_data.append({
                "Nombre":           name,
                "Email":            email,
                "Modulo":           modulo_nombre,
                "Leccion":          l.get("page_name", "Sin nombre"),
                "Completada":       "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha,
                "Pct Hotmart":      pct_hotmart
            })
        time.sleep(0.15)

    prog_bar.progress(1.0)
    status_text.markdown("""
    <p style="font-family:'Nunito Sans',sans-serif; text-align:center; color:#1aab6d;
              font-size:13px; font-weight:700;">✓ ¡Listo!</p>""", unsafe_allow_html=True)

    # Procesar datos
    df = pd.DataFrame(all_data)
    df_activos = df[df["Modulo"] != "Sin actividad"]

    resumen_rows = []
    for nombre, grupo in df.groupby("Nombre"):
        email        = grupo["Email"].iloc[0]
        pct_hotmart  = grupo["Pct Hotmart"].iloc[0]
        grupo_activo = grupo[grupo["Modulo"] != "Sin actividad"]

        if grupo_activo.empty:
            pct = float(pct_hotmart) if pct_hotmart else 0.0
            resumen_rows.append({
                "Nombre": nombre, "Email": email,
                "Completadas": 0, "Total": total_lec_reales if usar_total_real else 0,
                "Sin completar": total_lec_reales if usar_total_real else 0,
                "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
                "Estado": estado_riesgo(pct),
                "Ultima leccion": "Sin detalle", "Ultimo modulo": "---",
                "Ultima actividad": "---", "Modulo abandono": "---", "Leccion abandono": "---"
            })
            continue

        completadas_n = int((grupo_activo["Completada"] == "Si").sum())
        total_n       = total_lec_reales if usar_total_real else len(grupo_activo)
        pct           = min(round(completadas_n / total_n * 100, 1) if total_n > 0 else 0.0, 100.0)
        ul, um, uf, ma, la = calcular_abandono(grupo_activo)

        resumen_rows.append({
            "Nombre": nombre, "Email": email,
            "Completadas": completadas_n, "Total": total_n,
            "Sin completar": max(0, total_n - completadas_n),
            "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
            "Estado": estado_riesgo(pct),
            "Ultima leccion": ul, "Ultimo modulo": um,
            "Ultima actividad": uf, "Modulo abandono": ma, "Leccion abandono": la
        })

    resumen = pd.DataFrame(resumen_rows)

    pivot_rows = []
    for m in modulos_sel:
        total_m_real = modulo_info[m]["total_pages"]
        df_m = df_activos[df_activos["Modulo"] == m]
        for nombre, g in df_m.groupby("Nombre"):
            comp_m  = int((g["Completada"] == "Si").sum())
            total_m = total_m_real if total_m_real > 0 else len(g)
            pct_m   = min(round(comp_m / total_m * 100, 1) if total_m > 0 else 0.0, 100.0)
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

    st.session_state["dashboard_data"] = {
        "df": df, "resumen": resumen, "df_pivot": df_pivot,
        "tabla_cruzada": tabla_cruzada, "pendientes_detalle": pendientes_detalle,
        "errores": errores, "total_lec_reales": total_lec_reales,
        "usar_total_real": usar_total_real, "modulos_sel": modulos_sel,
        "total_alumnos": len(students)
    }

    time.sleep(0.5)
    st.session_state["page"] = "dashboard"
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "dashboard":

    data                = st.session_state["dashboard_data"]
    df                  = data["df"]
    resumen             = data["resumen"]
    df_pivot            = data["df_pivot"]
    tabla_cruzada       = data["tabla_cruzada"]
    pendientes_detalle  = data["pendientes_detalle"]
    errores             = data["errores"]
    total_lec_reales    = data["total_lec_reales"]
    usar_total_real     = data["usar_total_real"]
    modulos_sel         = data["modulos_sel"]
    subdomain           = st.session_state["subdomain"]
    club_name           = st.session_state["club_name"]

    total_alumnos = len(resumen)
    sin_actividad = (resumen["Estado"] == "Sin actividad").sum()
    en_riesgo     = (resumen["Estado"] == "En riesgo").sum()
    en_progreso   = (resumen["Estado"] == "En progreso").sum()
    avanzados     = (resumen["Estado"] == "Avanzado").sum()
    avance_prom   = round(resumen[resumen["Pct Avance"] > 0]["Pct Avance"].mean(), 1) if (resumen["Pct Avance"] > 0).any() else 0
    abandono_mod  = (
        df_pivot.groupby("Modulo")["Pendientes"].sum().sort_values(ascending=False)
        if not df_pivot.empty else pd.Series(dtype=float)
    )

    # ── HEADER ────────────────────────────────────────────────────────────────

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"""
        <div style="padding: 20px 0 24px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
                <div style="width:38px; height:38px; background:#E8420A; border-radius:10px;
                            display:flex; align-items:center; justify-content:center;
                            box-shadow:0 3px 10px rgba(232,66,10,0.3); font-size:18px;">🔥</div>
                <span style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px;
                             color:#1a1815;">Club Analytics</span>
                <span style="background:#fff5f2; color:#E8420A; border:1px solid #ffd4c4;
                             border-radius:20px; padding:3px 12px; font-size:12px; font-weight:700;
                             font-family:'Nunito Sans',sans-serif;">{club_name}</span>
            </div>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:13px; margin:0;">
                {len(modulos_sel)} módulos analizados · Generado el {datetime.now().strftime('%d de %B de %Y · %H:%M')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_h2:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("← Nuevo análisis", use_container_width=True):
            st.session_state["page"] = "selector"
            st.session_state["dashboard_data"] = None
            st.rerun()

    st.markdown("<div style='height:2px; background: linear-gradient(90deg, #E8420A, #ff9a7a, transparent); border-radius:2px; margin-bottom:28px;'></div>", unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────

    c1, c2, c3, c4, c5 = st.columns(5)

    def kpi_card(col, label, value, color="#1a1815", sublabel=""):
        with col:
            st.metric(label, value)

    c1.metric("👥 Alumnos", total_alumnos)
    c2.metric("📈 Avance promedio", f"{avance_prom}%")
    c3.metric("⚠️ En riesgo", en_riesgo)
    c4.metric("🔄 En progreso", en_progreso)
    c5.metric("🏆 Avanzados", avanzados)

    if sin_actividad > 0:
        st.markdown(f"""
        <div style="background:#fff5f2; border:1.5px solid #ffd4c4; border-radius:12px;
                    padding:12px 18px; margin-top:12px; display:flex; align-items:center; gap:10px;">
            <span style="font-size:18px;">🚨</span>
            <span style="font-family:'Nunito Sans',sans-serif; font-size:14px; color:#c93608; font-weight:600;">
                {sin_actividad} alumno{'s' if sin_actividad > 1 else ''} nunca {'accedieron' if sin_actividad > 1 else 'accedió'} al Club —
                riesgo máximo de churn
            </span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    if errores:
        with st.expander(f"⚠️ {len(errores)} alumnos con error al extraer datos"):
            st.dataframe(pd.DataFrame(errores), use_container_width=True, hide_index=True)

    # ── TABS ──────────────────────────────────────────────────────────────────

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen general",
        "🎯 Punto de abandono",
        "📚 Avance por módulo",
        "📋 Lecciones pendientes",
        "🗺️ Mapa de progreso"
    ])

    # ── TAB 1 ─────────────────────────────────────────────────────────────────
    with tab1:
        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Segmentación de alumnos**")
            seg = resumen["Estado"].value_counts().reset_index()
            seg.columns = ["Estado", "Cantidad"]
            fig_d = px.pie(seg, names="Estado", values="Cantidad",
                           hole=0.58, color="Estado", color_discrete_map=COLOR_MAP)
            fig_d.update_traces(textposition="outside", textinfo="label+value",
                                marker=dict(line=dict(color="#faf9f7", width=3)))
            fig_d.update_layout(
                margin=dict(t=20,b=20,l=20,r=20), height=300,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                font=dict(family="Nunito Sans")
            )
            st.plotly_chart(fig_d, use_container_width=True)

        with col_r:
            st.markdown("**Progreso individual**")
            sorted_r = resumen.sort_values("Pct Avance", ascending=True)
            fig_a = go.Figure(go.Bar(
                x=sorted_r["Pct Avance"], y=sorted_r["Nombre"],
                orientation="h",
                marker=dict(
                    color=[COLOR_MAP[e] for e in sorted_r["Estado"]],
                    line=dict(width=0)
                ),
                text=[f"{p}%" for p in sorted_r["Pct Avance"]],
                textposition="outside",
                textfont=dict(family="Nunito Sans", size=12),
                customdata=sorted_r[["Completadas","Total","Pct Hotmart"]],
                hovertemplate="<b>%{y}</b><br>Nuestro cálculo: %{x}%<br>Hotmart oficial: %{customdata[2]}%<br>%{customdata[0]}/%{customdata[1]} lecciones<extra></extra>"
            ))
            fig_a.update_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True,
                           gridcolor="#f0ede8", zeroline=False),
                yaxis=dict(showgrid=False),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(300, total_alumnos*32),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(family="Nunito Sans")
            )
            st.plotly_chart(fig_a, use_container_width=True)

        st.markdown("**Detalle completo**")
        st.dataframe(
            resumen[["Nombre","Email","Completadas","Total","Pct Avance","Pct Hotmart","Estado"]].sort_values("Pct Avance"),
            use_container_width=True, hide_index=True
        )

    # ── TAB 2 ─────────────────────────────────────────────────────────────────
    with tab2:
        col_a, col_b = st.columns([1,1])
        with col_a:
            st.markdown("**Alumnos sin actividad registrada**")
            sin_act = resumen[resumen["Estado"] == "Sin actividad"][["Nombre","Email","Pct Hotmart"]]
            if sin_act.empty:
                st.success("¡Todos los alumnos han accedido al menos una vez!")
            else:
                st.error(f"{len(sin_act)} alumnos nunca marcaron una lección como completada:")
                st.dataframe(sin_act, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("**Módulos con más lecciones pendientes**")
            if not abandono_mod.empty:
                fig_crit = go.Figure(go.Bar(
                    x=abandono_mod.values, y=abandono_mod.index,
                    orientation="h",
                    marker=dict(color="#E8420A", opacity=0.85, line=dict(width=0)),
                    text=abandono_mod.values, textposition="outside",
                    textfont=dict(family="Nunito Sans")
                ))
                fig_crit.update_layout(
                    xaxis_title="Lecciones pendientes acumuladas",
                    yaxis=dict(autorange="reversed"),
                    margin=dict(t=10,b=10,l=10,r=50), height=280,
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False, font=dict(family="Nunito Sans")
                )
                st.plotly_chart(fig_crit, use_container_width=True)

        st.markdown("---")
        st.markdown("**Última actividad y punto de abandono por alumno**")
        df_ab = resumen[resumen["Ultimo modulo"] != "---"][[
            "Nombre","Email","Estado","Pct Avance",
            "Ultimo modulo","Ultima leccion","Ultima actividad",
            "Modulo abandono","Leccion abandono"
        ]].sort_values("Pct Avance")
        st.dataframe(df_ab, use_container_width=True, hide_index=True)

    # ── TAB 3 ─────────────────────────────────────────────────────────────────
    with tab3:
        if not df_pivot.empty:
            mod_global = df_pivot.groupby("Modulo").agg(
                Completadas=("Completadas","sum"),
                Pendientes=("Pendientes","sum"),
                Total=("Total modulo","first")
            ).reset_index()
            mod_global["Pct Global"] = (
                mod_global["Completadas"] / (mod_global["Total"] * total_alumnos) * 100
            ).clip(0, 100).round(1)

            st.markdown("**Completitud por módulo — todos los alumnos**")
            fig_mod = go.Figure(go.Bar(
                x=mod_global["Pct Global"], y=mod_global["Modulo"],
                orientation="h",
                marker=dict(
                    color=["#b83208" if p>=60 else "#E8420A" if p>=35 else "#ffb3a0" for p in mod_global["Pct Global"]],
                    line=dict(width=0)
                ),
                text=[f"{p}%" for p in mod_global["Pct Global"]],
                textposition="outside",
                textfont=dict(family="Nunito Sans"),
                customdata=mod_global[["Completadas","Pendientes"]],
                hovertemplate="<b>%{y}</b><br>Completadas: %{customdata[0]}<br>Pendientes: %{customdata[1]}<extra></extra>"
            ))
            fig_mod.update_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8"),
                yaxis=dict(autorange="reversed", showgrid=False),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(280, len(mod_global)*44),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(family="Nunito Sans")
            )
            st.plotly_chart(fig_mod, use_container_width=True)

            st.markdown("---")
            st.markdown("**Zoom: avance por alumno dentro de un módulo**")
            filtro_mod = st.selectbox("Selecciona el módulo", sorted(df_pivot["Modulo"].unique()))
            df_mf = df_pivot[df_pivot["Modulo"]==filtro_mod].sort_values("Pct Modulo")
            fig_m2 = go.Figure(go.Bar(
                x=df_mf["Pct Modulo"], y=df_mf["Nombre"],
                orientation="h",
                marker=dict(
                    color=["#b83208" if p>=60 else "#E8420A" if p>=35 else "#ffb3a0" for p in df_mf["Pct Modulo"]],
                    line=dict(width=0)
                ),
                text=[f"{p}% ({int(c)}/{int(t)})" for p,c,t in zip(df_mf["Pct Modulo"],df_mf["Completadas"],df_mf["Total modulo"])],
                textposition="outside",
                textfont=dict(family="Nunito Sans")
            ))
            fig_m2.update_layout(
                xaxis=dict(range=[0,125], ticksuffix="%", showgrid=True, gridcolor="#f0ede8"),
                yaxis=dict(showgrid=False),
                margin=dict(t=10,b=10,l=10,r=110),
                height=max(300, len(df_mf)*36),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False, font=dict(family="Nunito Sans")
            )
            st.plotly_chart(fig_m2, use_container_width=True)
        else:
            st.warning("No hay datos de módulos disponibles.")

    # ── TAB 4 ─────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("**Lecciones pendientes por alumno**")
        st.caption("Lista exacta de las clases que cada alumno NO ha completado todavía.")
        if not pendientes_detalle.empty:
            filtro_alumno = st.selectbox(
                "Filtrar por alumno",
                ["Todos"] + sorted(pendientes_detalle["Nombre"].unique().tolist())
            )
            df_pf = pendientes_detalle if filtro_alumno == "Todos" else pendientes_detalle[pendientes_detalle["Nombre"]==filtro_alumno]
            st.dataframe(df_pf, use_container_width=True, hide_index=True)
            st.caption(f"{len(df_pf)} lecciones pendientes")
        else:
            st.success("¡Todos los alumnos completaron todas las lecciones!")

    # ── TAB 5 ─────────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("**Mapa de progreso — alumno × módulo**")
        st.caption("Cada celda muestra el % completado. Oscuro = más avance, claro = menos avance.")
        if not tabla_cruzada.empty:
            st.dataframe(
                tabla_cruzada.set_index("Nombre"),
                use_container_width=True
            )
        else:
            st.warning("No hay suficientes datos para el mapa de progreso.")

    # ── EXPORTAR ──────────────────────────────────────────────────────────────

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:2px; background: linear-gradient(90deg, #E8420A, #ff9a7a, transparent); border-radius:2px; margin-bottom:20px;'></div>", unsafe_allow_html=True)

    col_exp1, col_exp2 = st.columns([3,1])
    with col_exp1:
        st.markdown("""
        <p style="font-family:'Nunito Sans',sans-serif; font-weight:700; font-size:15px;
                   color:#1a1815; margin-bottom:4px;">Exportar informe</p>
        <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:13px; margin:0;">
            Excel con 5 pestañas: resumen, avance por módulo, tabla cruzada, lecciones pendientes y detalle completo.
        </p>
        """, unsafe_allow_html=True)
    with col_exp2:
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
            label="📥 Descargar Excel",
            data=buffer,
            file_name=f"club_analytics_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
