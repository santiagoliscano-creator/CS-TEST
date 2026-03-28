"""
Hotmart Club · Club Analytics v6.0
Fix: robust pagination + response parsing + validation order
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import io

st.set_page_config(
    page_title="Hotmart · Club Analytics",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800;900&display=swap');
* { font-family: 'Nunito Sans', sans-serif !important; }
[data-testid="stSidebar"] { display:none !important; }
[data-testid="stToolbar"] { display:none !important; }
footer { display:none !important; }
#MainMenu { display:none !important; }
.stDeployButton { display:none !important; }
.stApp { background:#faf9f7 !important; }
.stTextInput > div > div > input {
    border-radius:10px !important; border:1.5px solid #e0ddd8 !important;
    font-size:14px !important; padding:10px 14px !important;
    background:white !important; color:#1a1815 !important;
}
.stTextInput > div > div > input::placeholder { color:#c0bdb8 !important; }
.stTextInput > div > div > input:focus {
    border-color:#E8420A !important;
    box-shadow:0 0 0 3px rgba(232,66,10,0.12) !important; outline:none !important;
}
.stTextInput label { font-weight:700 !important; color:#3d3a35 !important; font-size:13px !important; }
.stButton > button[kind="primary"] {
    background:#E8420A !important; color:white !important; border:none !important;
    border-radius:10px !important; font-weight:700 !important; font-size:15px !important;
    padding:12px 28px !important; box-shadow:0 4px 15px rgba(232,66,10,0.3) !important;
}
.stButton > button[kind="primary"]:hover { background:#c93608 !important; }
.stButton > button:not([kind="primary"]) {
    background:white !important; color:#E8420A !important;
    border:2px solid #E8420A !important; border-radius:10px !important; font-weight:700 !important;
}
[data-testid="stMetric"] {
    background:white !important; border-radius:14px !important; padding:18px 20px !important;
    border:1px solid #f0ede8 !important; box-shadow:0 2px 8px rgba(0,0,0,0.05) !important;
}
[data-testid="stMetricLabel"] { font-size:12px !important; font-weight:700 !important; color:#8c8880 !important; text-transform:uppercase !important; letter-spacing:0.06em !important; }
[data-testid="stMetricValue"] { font-size:28px !important; font-weight:800 !important; color:#1a1815 !important; }
.stTabs [data-baseweb="tab-list"] { gap:4px !important; background:#f0ede8 !important; border-radius:12px !important; padding:4px !important; }
.stTabs [data-baseweb="tab"] { border-radius:9px !important; font-weight:600 !important; font-size:13px !important; color:#8c8880 !important; padding:8px 16px !important; }
.stTabs [aria-selected="true"] { background:white !important; color:#E8420A !important; box-shadow:0 1px 4px rgba(0,0,0,0.08) !important; }
[data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden !important; }
.stSelectbox > div > div { border-radius:10px !important; border:1.5px solid #e0ddd8 !important; }
.stMultiSelect > div > div { border-radius:10px !important; border:1.5px solid #e0ddd8 !important; }
.stProgress > div > div > div { background:#E8420A !important; }
.caption-box {
    background:#f5f2ee; border-radius:10px; padding:12px 16px; margin-bottom:16px;
    font-size:13px; color:#5c5a56; line-height:1.6; border-left:3px solid #E8420A;
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
            if not resp.text or not resp.text.strip(): return [], "empty_body"
            data = resp.json()
            if isinstance(data, list): return data, None
            elif isinstance(data, dict) and "items" in data: return data["items"], None
            elif isinstance(data, dict): return list(data.values())[0] if data else [], None
        return [], f"HTTP {resp.status_code}"
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


def _extract_items_from_response(data):
    """Extrae la lista de items de cualquier formato de respuesta de la API."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # Buscar en claves conocidas (orden de prioridad)
        for key in ("items", "users", "content", "students", "data", "results", "records"):
            val = data.get(key)
            if isinstance(val, list) and val:
                return val
        # Si ninguna clave conocida tiene lista, buscar la primera lista no vacía
        for key, val in data.items():
            if isinstance(val, list) and val and key not in ("errors", "warnings"):
                return val
    return []


def _extract_page_token(data):
    """Busca el token de paginación en cualquier ubicación del response."""
    if not isinstance(data, dict):
        return None
    # Nivel raíz — claves comunes
    for key in ("next_page_token", "nextPageToken", "page_token", "cursor", "nextCursor"):
        token = data.get(key)
        if token:
            return token
    # Dentro de objetos anidados de paginación
    for wrapper_key in ("pagination", "paging", "page_info", "meta"):
        wrapper = data.get(wrapper_key)
        if isinstance(wrapper, dict):
            for key in ("next_page_token", "nextPageToken", "page_token", "cursor", "next"):
                token = wrapper.get(key)
                if token:
                    return token
    return None


def get_students(access_token, subdomain):
    """Obtiene TODOS los alumnos con paginación automática."""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    todos = []
    page_token = None
    max_pages = 100  # suficiente para ~5000 alumnos

    for page_num in range(max_pages):
        url = f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}&max_results=50"
        if page_token:
            url += f"&page_token={page_token}"
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            if resp.status_code != 200:
                err_msg = f"HTTP {resp.status_code}: {resp.text[:300]}"
                return todos if todos else [], err_msg
            if not resp.text or not resp.text.strip():
                break
            data = resp.json()

            items = _extract_items_from_response(data)
            if not items:
                # Si es la primera página y no hay items, devolver vacío
                if page_num == 0:
                    return [], f"Respuesta vacía de la API. Cuerpo: {resp.text[:300]}"
                break

            todos.extend(items)

            # Buscar token de siguiente página
            if isinstance(data, dict):
                page_token = _extract_page_token(data)
                if not page_token:
                    break
            else:
                break  # lista plana = sin paginación

        except Exception as e:
            return todos if todos else [], str(e)

    return todos, None


def get_student_progress(access_token, subdomain, user_id):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    url = f"https://developers.hotmart.com/club/api/v1/users/{user_id}/lessons?subdomain={subdomain}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            if not resp.text or not resp.text.strip(): return [], None
            data = resp.json()
            if isinstance(data, list): return data, None
            if isinstance(data, dict):
                # Buscar en claves conocidas
                for key in ("lessons", "items", "content", "data", "results"):
                    val = data.get(key)
                    if isinstance(val, list):
                        return val, None
                # Fallback: primera lista encontrada
                for key, val in data.items():
                    if isinstance(val, list) and key not in ("errors", "warnings"):
                        return val, None
            return [], None
        elif resp.status_code == 204: return [], None
        return [], f"HTTP {resp.status_code}"
    except Exception as e:
        return [], str(e)


def extraer_modulos_desde_alumnos(token, subdomain, students, max_alumnos=30):
    nombres = set()
    for s in (students or [])[:max_alumnos]:
        uid = s.get("user_id", s.get("id", ""))
        if not uid: continue
        lecs, _ = get_student_progress(token, subdomain, uid)
        for l in (lecs or []):
            m = l.get("module_name", "")
            if m: nombres.add(m)
        if nombres: time.sleep(0.1)
    return sorted(nombres)


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

TFONT = dict(family="Nunito Sans", color="#3d3a35", size=12)

def make_layout(**kwargs):
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Nunito Sans", color="#3d3a35", size=12),
        showlegend=False,
    )
    base.update(kwargs)
    return base

def bar_colors(values):
    return ["#b83208" if v >= 60 else "#E8420A" if v >= 35 else "#ffb3a0" for v in values]

def caption(text):
    st.markdown(f'<div class="caption-box">{text}</div>', unsafe_allow_html=True)

def calcular_abandono(df_alumno):
    completadas = df_alumno[df_alumno["Completada"] == "Si"].sort_values("Fecha Completado", ascending=False)
    pendientes  = df_alumno[df_alumno["Completada"] == "No"]
    ul = completadas.iloc[0]["Leccion"]          if not completadas.empty else "—"
    um = completadas.iloc[0]["Modulo"]           if not completadas.empty else "—"
    uf = completadas.iloc[0]["Fecha Completado"] if not completadas.empty else "—"
    ma = pendientes.iloc[0]["Modulo"]            if not pendientes.empty else "Completado ✓"
    la = pendientes.iloc[0]["Leccion"]           if not pendientes.empty else "Completado ✓"
    return ul, um, uf, ma, la


# ─── SESSION STATE ────────────────────────────────────────────────────────────

for k, v in {"page":"login","token":None,"modulo_info":{},
             "subdomain":"","club_name":"","modulos_seleccionados":[],"dashboard_data":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — LOGIN
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state["page"] == "login":

    _, col_c, _ = st.columns([1, 1.1, 1])
    with col_c:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:28px;">
            <div style="display:inline-flex; align-items:center; justify-content:center;
                        width:60px; height:60px; background:#E8420A; border-radius:18px;
                        margin-bottom:16px; box-shadow:0 8px 24px rgba(232,66,10,0.35);">
                <span style="font-size:30px; line-height:1;">🔥</span>
            </div>
            <h1 style="font-weight:800; font-size:28px; color:#1a1815; margin:0;">Club Analytics</h1>
            <p style="color:#8c8880; font-size:14px; margin-top:6px;">
                Analiza el progreso de tus alumnos en Hotmart Club
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("### Conecta tu Club")
            st.markdown("<p style='color:#8c8880;font-size:13px;margin-top:-12px;margin-bottom:16px;'>Ingresa tus credenciales de Hotmart Developers</p>", unsafe_allow_html=True)
            basic_token   = st.text_input("Basic Token",         placeholder="Basic NTM5OWZlMD...",                  key="l_basic")
            client_id     = st.text_input("Client ID",           placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", key="l_cid")
            client_secret = st.text_input("Client Secret",       placeholder="••••••••••••••••", type="password",    key="l_secret")
            subdomain_in  = st.text_input("Subdominio del Club", placeholder="mi-curso",                             key="l_sub",
                                          help="Lo que aparece en hotmart.com/es/club/SUBDOMINIO")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            conectar = st.button("Conectar y ver Analytics →", type="primary", use_container_width=True)

        st.markdown("""
        <div style="text-align:center; margin-top:16px;">
            <p style="color:#b8b4ae; font-size:12px; line-height:1.7;">
                ¿Cómo obtener mis credenciales?<br>
                Entra a <strong style="color:#E8420A;">developers.hotmart.com</strong>
                → crea una aplicación → copia tus credenciales.<br>
                Las mismas credenciales sirven para todos tus Clubs.
            </p>
        </div>
        """, unsafe_allow_html=True)

        if conectar:
            if not all([basic_token, client_id, client_secret, subdomain_in]):
                st.error("Por favor completa todos los campos.")
            else:
                with st.spinner("Verificando credenciales y cargando módulos..."):
                    token, err = get_access_token(basic_token, client_id, client_secret)
                    if err:
                        st.error(f"Credenciales incorrectas: {err}")
                    else:
                        # PASO 1: Validar que el Club tenga alumnos PRIMERO
                        students_check, err_st = get_students(token, subdomain_in)
                        if not students_check:
                            detail = f" Detalle: {err_st}" if err_st else ""
                            st.error(
                                f"No se encontraron alumnos en el subdominio '{subdomain_in}'.{detail}\n\n"
                                f"Verifica que:\n"
                                f"- El subdominio sea exacto (sin espacios, en minúsculas)\n"
                                f"- Tu cuenta tenga acceso a este Club\n"
                                f"- El Club tenga al menos un alumno matriculado"
                            )
                            st.stop()

                        # PASO 2: Intentar obtener módulos vía endpoint directo
                        mods_main, _  = get_modules(token, subdomain_in, is_extra=False)
                        mods_extra, _ = get_modules(token, subdomain_in, is_extra=True)
                        todos_mods = mods_main + mods_extra
                        modulo_info = {}

                        if todos_mods:
                            for m in todos_mods:
                                mid  = m.get("module_id", m.get("id", ""))
                                name = m.get("name", f"Modulo {mid}")
                                pages, _ = get_pages_for_module(token, subdomain_in, mid)
                                total_pages = len([p for p in pages if p.get("type","CONTENT") != "ADVERTISEMENT"]) if pages else 0
                                modulo_info[name] = {"module_id": mid, "total_pages": total_pages, "is_extra": m.get("is_extra", False)}
                        else:
                            # PASO 3: Fallback — extraer módulos desde las lecciones de alumnos
                            nombres_tmp = extraer_modulos_desde_alumnos(token, subdomain_in, students_check, max_alumnos=30)
                            if not nombres_tmp:
                                st.warning("No se detectaron módulos. Se cargará el Club completo.")
                                modulo_info["Contenido del Club"] = {"module_id": "", "total_pages": 0, "is_extra": False}
                            else:
                                for nombre in nombres_tmp:
                                    modulo_info[nombre] = {"module_id": "", "total_pages": 0, "is_extra": False}

                        st.session_state.update({
                            "token": token, "modulo_info": modulo_info,
                            "subdomain": subdomain_in,
                            "club_name": subdomain_in.replace("-"," ").title(),
                            "page": "selector"
                        })
                        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — SELECTOR DE MÓDULOS
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "selector":

    token       = st.session_state["token"]
    modulo_info = st.session_state["modulo_info"]
    subdomain   = st.session_state["subdomain"]
    club_name   = st.session_state["club_name"]

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:14px;padding:20px 0 28px;border-bottom:2px solid #f0ede8;margin-bottom:32px;">
        <div style="width:42px;height:42px;background:#E8420A;border-radius:12px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(232,66,10,0.3);font-size:20px;">🔥</div>
        <div>
            <div style="font-weight:800;font-size:20px;color:#1a1815;">Club Analytics</div>
            <div style="font-size:13px;color:#8c8880;">{club_name} · {len(modulo_info)} módulos encontrados</div>
        </div>
    </div>
    <h2 style="font-weight:800;font-size:22px;color:#1a1815;margin-bottom:8px;">¿Qué producto quieres analizar?</h2>
    <p style="color:#8c8880;font-size:14px;margin-bottom:28px;">Selecciona los módulos del producto que quieres revisar. Si hay un solo producto, selecciónalos todos.</p>
    """, unsafe_allow_html=True)

    col_sel, col_prev = st.columns([1.3, 1])
    with col_sel:
        nombres = list(modulo_info.keys())
        seleccionados = st.multiselect("Módulos a incluir", options=nombres, default=nombres)
        total_lec = sum(modulo_info[m]["total_pages"] for m in seleccionados)
        if seleccionados:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fff5f2,#fff);border:1.5px solid #ffd4c4;border-radius:14px;padding:18px 20px;margin-top:16px;">
                <div style="font-size:11px;color:#E8420A;font-weight:800;letter-spacing:0.08em;margin-bottom:4px;">SELECCIÓN ACTUAL</div>
                <div style="font-size:24px;font-weight:800;color:#1a1815;">{len(seleccionados)} módulos</div>
                {'<div style="font-size:14px;color:#8c8880;margin-top:2px;">' + str(total_lec) + ' lecciones en total</div>' if total_lec > 0 else ''}
            </div>""", unsafe_allow_html=True)

    with col_prev:
        st.markdown("<div style='font-weight:800;font-size:11px;color:#8c8880;letter-spacing:0.08em;margin-bottom:12px;'>MÓDULOS DISPONIBLES</div>", unsafe_allow_html=True)
        for nombre, info in modulo_info.items():
            activo = nombre in seleccionados
            pages  = info["total_pages"]
            bg     = "#fff5f2" if activo else "#faf9f7"
            border = "#ffd4c4" if activo else "#f0ede8"
            dot    = "#E8420A" if activo else "#d0cdc8"
            st.markdown(f"""
            <div style="background:{bg};border:1.5px solid {border};border-radius:10px;padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px;">
                <div style="width:8px;height:8px;border-radius:50%;background:{dot};flex-shrink:0;"></div>
                <div>
                    <div style="font-weight:700;font-size:13px;color:#1a1815;">{nombre}</div>
                    <div style="font-size:11px;color:#b8b4ae;">{'Extra' if info['is_extra'] else 'Principal'}{' · ' + str(pages) + ' clases' if pages > 0 else ''}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    col_b, _, col_g = st.columns([1, 2, 1])
    with col_b:
        if st.button("← Volver", use_container_width=True):
            st.session_state["page"] = "login"; st.rerun()
    with col_g:
        if st.button("Generar Dashboard →", type="primary", use_container_width=True, disabled=not seleccionados):
            st.session_state["modulos_seleccionados"] = seleccionados
            st.session_state["page"] = "loading"; st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — CARGA
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "loading":

    token       = st.session_state["token"]
    modulo_info = st.session_state["modulo_info"]
    subdomain   = st.session_state["subdomain"]
    modulos_sel = st.session_state["modulos_seleccionados"]
    usar_filtro = modulos_sel != ["Contenido del Club"]

    _, col_c, _ = st.columns([1, 1.5, 1])
    with col_c:
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:40px;margin-bottom:16px;">🔥</div>
            <h2 style="font-weight:800;font-size:22px;color:#1a1815;margin-bottom:8px;">Analizando tu Club...</h2>
            <p style="color:#8c8880;font-size:14px;">Extrayendo el progreso de cada alumno.</p>
        </div>""", unsafe_allow_html=True)
        status_txt = st.empty()
        prog_bar   = st.progress(0)

    students, err2 = get_students(token, subdomain)
    if not students:
        with col_c:
            st.error(f"No se pudo obtener la lista de alumnos: {err2}")
            if st.button("← Volver"): st.session_state["page"] = "selector"; st.rerun()
        st.stop()

    all_data, errores = [], []

    for i, student in enumerate(students):
        uid           = student.get("user_id", student.get("id", ""))
        name          = student.get("name", "Sin nombre")
        email         = student.get("email", "")
        prog_obj      = student.get("progress", {}) or {}
        pct_hotmart   = float(prog_obj.get("completed_percentage", 0) or 0)
        comp_hotmart  = int(prog_obj.get("completed", 0) or 0)
        total_hotmart = int(prog_obj.get("total", 0) or 0)

        prog_bar.progress((i + 1) / len(students))
        status_txt.markdown(f"<p style='text-align:center;color:#8c8880;font-size:13px;'>Analizando {i+1} de {len(students)} alumnos...</p>", unsafe_allow_html=True)

        if not uid:
            errores.append({"Alumno": name, "Error": "user_id vacio"}); continue

        lecciones, err_l = get_student_progress(token, subdomain, uid)
        if err_l: errores.append({"Alumno": name, "Error": err_l})

        if not lecciones:
            all_data.append({
                "Nombre": name, "Email": email,
                "Modulo": "Sin actividad", "Leccion": "Sin actividad",
                "Completada": "No", "Fecha Completado": "",
                "Pct Hotmart": pct_hotmart, "Completadas Hotmart": comp_hotmart,
                "Total Hotmart": total_hotmart
            })
            time.sleep(0.1); continue

        for l in lecciones:
            mn = l.get("module_name", "Sin modulo")
            if usar_filtro and mn not in modulos_sel: continue
            fecha = ""
            if l.get("completed_date"):
                try: fecha = datetime.fromtimestamp(l["completed_date"] / 1000).strftime("%d/%m/%Y")
                except: fecha = ""
            all_data.append({
                "Nombre": name, "Email": email, "Modulo": mn,
                "Leccion": l.get("page_name", "Sin nombre"),
                "Completada": "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha,
                "Pct Hotmart": pct_hotmart,
                "Completadas Hotmart": comp_hotmart,
                "Total Hotmart": total_hotmart
            })
        time.sleep(0.1)

    prog_bar.progress(1.0)
    status_txt.markdown("<p style='text-align:center;color:#1aab6d;font-size:14px;font-weight:800;'>✓ ¡Análisis completado!</p>", unsafe_allow_html=True)

    df         = pd.DataFrame(all_data)
    df_activos = df[df["Modulo"] != "Sin actividad"]

    resumen_rows = []
    for nombre, grupo in df.groupby("Nombre"):
        email         = grupo["Email"].iloc[0]
        pct_hotmart   = float(grupo["Pct Hotmart"].iloc[0] or 0)
        comp_hotmart  = int(grupo["Completadas Hotmart"].iloc[0] or 0)
        total_hotmart = int(grupo["Total Hotmart"].iloc[0] or 0)
        estado        = estado_riesgo(pct_hotmart)
        grupo_activo  = grupo[grupo["Modulo"] != "Sin actividad"]

        if grupo_activo.empty:
            resumen_rows.append({
                "Nombre": nombre, "Email": email,
                "Completadas": comp_hotmart, "Total lecciones": total_hotmart,
                "% Avance": pct_hotmart, "Estado": estado,
                "Ultima leccion": "—", "Ultimo modulo": "—",
                "Ultima actividad": "—", "Modulo abandono": "—", "Leccion abandono": "—"
            }); continue

        ul, um, uf, ma, la = calcular_abandono(grupo_activo)
        resumen_rows.append({
            "Nombre": nombre, "Email": email,
            "Completadas": comp_hotmart, "Total lecciones": total_hotmart,
            "% Avance": pct_hotmart, "Estado": estado,
            "Ultima leccion": ul, "Ultimo modulo": um, "Ultima actividad": uf,
            "Modulo abandono": ma, "Leccion abandono": la
        })

    resumen = pd.DataFrame(resumen_rows)

    pivot_rows = []
    modulos_para_pivot = df_activos["Modulo"].unique() if not usar_filtro else modulos_sel
    for m in modulos_para_pivot:
        total_m_real = modulo_info.get(m, {}).get("total_pages", 0)
        df_m = df_activos[df_activos["Modulo"] == m]
        for nombre, g in df_m.groupby("Nombre"):
            comp_m  = int((g["Completada"] == "Si").sum())
            total_m = total_m_real if total_m_real > 0 else len(g)
            pct_m   = min(round(comp_m / total_m * 100, 1) if total_m > 0 else 0.0, 100.0)
            pivot_rows.append({
                "Nombre": nombre, "Modulo": m,
                "Completadas": comp_m, "Total modulo": total_m,
                "Pendientes": max(0, total_m - comp_m), "% Avance": pct_m
            })

    df_pivot = pd.DataFrame(pivot_rows) if pivot_rows else pd.DataFrame()
    tabla_cruzada = (
        df_pivot.pivot_table(index="Nombre", columns="Modulo", values="% Avance", fill_value=0).reset_index()
        if not df_pivot.empty else pd.DataFrame()
    )
    df_detalle         = df_activos[["Nombre","Email","Modulo","Leccion","Completada","Fecha Completado"]].copy()
    pendientes_detalle = df_activos[df_activos["Completada"] == "No"][["Nombre","Email","Modulo","Leccion"]].copy()

    st.session_state["dashboard_data"] = {
        "df": df, "df_detalle": df_detalle, "resumen": resumen,
        "df_pivot": df_pivot, "tabla_cruzada": tabla_cruzada,
        "pendientes_detalle": pendientes_detalle, "errores": errores,
        "modulos_sel": modulos_sel, "total_alumnos_raw": len(students)
    }
    time.sleep(0.4)
    st.session_state["page"] = "dashboard"
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "dashboard":

    data               = st.session_state["dashboard_data"]
    df                 = data["df"]
    df_detalle         = data["df_detalle"]
    resumen            = data["resumen"]
    df_pivot           = data["df_pivot"]
    tabla_cruzada      = data["tabla_cruzada"]
    pendientes_detalle = data["pendientes_detalle"]
    errores            = data["errores"]
    modulos_sel        = data["modulos_sel"]
    total_alumnos_raw  = data["total_alumnos_raw"]
    subdomain          = st.session_state["subdomain"]
    club_name          = st.session_state["club_name"]

    total_alumnos = len(resumen)
    sin_actividad = (resumen["Estado"] == "Sin actividad").sum()
    en_riesgo     = (resumen["Estado"] == "En riesgo").sum()
    en_progreso   = (resumen["Estado"] == "En progreso").sum()
    avanzados     = (resumen["Estado"] == "Avanzado").sum()
    avance_prom   = round(resumen[resumen["% Avance"] > 0]["% Avance"].mean(), 1) if (resumen["% Avance"] > 0).any() else 0

    # HEADER
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"""
        <div style="padding:20px 0 24px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
                <div style="width:38px;height:38px;background:#E8420A;border-radius:10px;display:flex;align-items:center;justify-content:center;box-shadow:0 3px 10px rgba(232,66,10,0.3);font-size:18px;">🔥</div>
                <span style="font-weight:800;font-size:22px;color:#1a1815;">Club Analytics</span>
                <span style="background:#fff5f2;color:#E8420A;border:1px solid #ffd4c4;border-radius:20px;padding:3px 12px;font-size:12px;font-weight:700;">{club_name}</span>
            </div>
            <p style="color:#8c8880;font-size:13px;margin:0;">
                {total_alumnos_raw} alumnos extraídos · Generado el {datetime.now().strftime('%d/%m/%Y · %H:%M')}
            </p>
        </div>""", unsafe_allow_html=True)
    with col_h2:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        if st.button("← Nuevo análisis", use_container_width=True):
            st.session_state["page"] = "selector"
            st.session_state["dashboard_data"] = None
            st.rerun()

    st.markdown("<div style='height:2px;background:linear-gradient(90deg,#E8420A,#ff9a7a,transparent);border-radius:2px;margin-bottom:28px;'></div>", unsafe_allow_html=True)

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Alumnos",         total_alumnos)
    c2.metric("📈 Avance promedio", f"{avance_prom}%")
    c3.metric("⚠️ En riesgo",       en_riesgo)
    c4.metric("🔄 En progreso",     en_progreso)
    c5.metric("🏆 Avanzados",       avanzados)

    if sin_actividad > 0:
        st.markdown(f"""
        <div style="background:#fff5f2;border:1.5px solid #ffd4c4;border-radius:12px;padding:12px 18px;margin-top:12px;display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">🚨</span>
            <span style="font-size:14px;color:#c93608;font-weight:700;">
                {sin_actividad} alumno{'s' if sin_actividad > 1 else ''} con 0% de avance — riesgo de churn
            </span>
        </div>""", unsafe_allow_html=True)

    if errores:
        with st.expander(f"⚠️ {len(errores)} alumnos con error al extraer datos"):
            st.dataframe(pd.DataFrame(errores), use_container_width=True, hide_index=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen general",
        "🎯 Punto de abandono",
        "📚 Por módulo",
        "📋 Pendientes",
        "🗺️ Mapa"
    ])

    with tab1:
        caption("Vista global del Club. El <strong>% de avance</strong> es el dato oficial de Hotmart por alumno.")
        col_l, col_r = st.columns(2)

        with col_l:
            st.markdown("**Segmentación de alumnos**")
            seg = resumen["Estado"].value_counts().reset_index()
            seg.columns = ["Estado","Cantidad"]
            fig_d = px.pie(seg, names="Estado", values="Cantidad", hole=0.58,
                           color="Estado", color_discrete_map=COLOR_MAP)
            fig_d.update_traces(
                textposition="outside", textinfo="label+value",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=12),
                marker=dict(line=dict(color="#faf9f7", width=3))
            )
            fig_d.update_layout(make_layout(margin=dict(t=20,b=20,l=20,r=20), height=300))
            st.plotly_chart(fig_d, use_container_width=True)

        with col_r:
            st.markdown("**Progreso por alumno**")
            sorted_r = resumen.sort_values("% Avance", ascending=True)
            fig_a = go.Figure(go.Bar(
                x=sorted_r["% Avance"], y=sorted_r["Nombre"], orientation="h",
                marker_color=[COLOR_MAP[e] for e in sorted_r["Estado"]],
                text=[f"{p}%" for p in sorted_r["% Avance"]],
                textposition="outside",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=11),
                customdata=sorted_r[["Completadas","Total lecciones"]],
                hovertemplate="<b>%{y}</b><br>%{x}% · %{customdata[0]}/%{customdata[1]} lecciones<extra></extra>"
            ))
            fig_a.update_layout(make_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           zeroline=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                yaxis=dict(showgrid=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(300, total_alumnos * 28)
            ))
            st.plotly_chart(fig_a, use_container_width=True)

        st.markdown("**Tabla detallada**")
        st.dataframe(
            resumen[["Nombre","Email","Completadas","Total lecciones","% Avance","Estado"]].sort_values("% Avance"),
            use_container_width=True, hide_index=True
        )

    with tab2:
        caption("Muestra <strong>dónde exactamente paró cada alumno</strong>: última lección completada y el módulo donde dejó de avanzar.")

        col_a, col_b = st.columns([1,1])
        with col_a:
            st.markdown("**Alumnos con 0% de avance**")
            sin_act = resumen[resumen["Estado"] == "Sin actividad"][["Nombre","Email"]]
            if sin_act.empty:
                st.success("¡Todos los alumnos tienen avance registrado!")
            else:
                st.error(f"{len(sin_act)} alumnos con 0% — contactar de inmediato:")
                st.dataframe(sin_act, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("**Módulos con más lecciones pendientes**")
            if not df_pivot.empty:
                aband = df_pivot.groupby("Modulo")["Pendientes"].sum().sort_values(ascending=False)
                if not aband.empty:
                    fig_ab = go.Figure(go.Bar(
                        x=aband.values, y=aband.index, orientation="h",
                        marker_color="#E8420A",
                        text=aband.values, textposition="outside",
                        textfont=dict(family="Nunito Sans", color="#3d3a35", size=12)
                    ))
                    fig_ab.update_layout(make_layout(
                        xaxis=dict(
                            title=dict(text="Lecciones pendientes",
                                       font=dict(family="Nunito Sans", color="#8c8880", size=11)),
                            tickfont=dict(family="Nunito Sans", color="#3d3a35"), zeroline=False
                        ),
                        yaxis=dict(autorange="reversed",
                                   tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                        margin=dict(t=10,b=10,l=10,r=60), height=280
                    ))
                    st.plotly_chart(fig_ab, use_container_width=True)
            else:
                st.info("No hay datos de módulos disponibles.")

        st.markdown("---")
        st.markdown("**Última actividad y punto de abandono**")
        df_ab = resumen[resumen["Ultimo modulo"] != "—"][[
            "Nombre","Email","Estado","% Avance",
            "Ultimo modulo","Ultima leccion","Ultima actividad",
            "Modulo abandono","Leccion abandono"
        ]].sort_values("% Avance")
        if not df_ab.empty:
            st.dataframe(df_ab, use_container_width=True, hide_index=True)
        else:
            st.info("No hay datos de detalle disponibles.")

    with tab3:
        caption("Avance <strong>dentro de cada módulo</strong>. El zoom permite ver alumno por alumno en un módulo específico.")

        if not df_pivot.empty:
            mod_prom = df_pivot.groupby("Modulo")["% Avance"].mean().round(1).reset_index()
            mod_prom.columns = ["Modulo","% Promedio"]

            st.markdown("**% promedio de avance por módulo**")
            fig_mod = go.Figure(go.Bar(
                x=mod_prom["% Promedio"], y=mod_prom["Modulo"], orientation="h",
                marker_color=bar_colors(mod_prom["% Promedio"]),
                text=[f"{p}%" for p in mod_prom["% Promedio"]],
                textposition="outside",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=12)
            ))
            fig_mod.update_layout(make_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           zeroline=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                yaxis=dict(autorange="reversed", showgrid=False,
                           tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(280, len(mod_prom) * 46)
            ))
            st.plotly_chart(fig_mod, use_container_width=True)

            st.markdown("---")
            st.markdown("**Zoom: alumno por alumno dentro de un módulo**")
            filtro_mod = st.selectbox("Módulo", sorted(df_pivot["Modulo"].unique()), key="mod1")
            df_mf = df_pivot[df_pivot["Modulo"] == filtro_mod].sort_values("% Avance")
            fig_m2 = go.Figure(go.Bar(
                x=df_mf["% Avance"], y=df_mf["Nombre"], orientation="h",
                marker_color=bar_colors(df_mf["% Avance"]),
                text=[f"{p}% ({int(c)}/{int(t)})" for p,c,t in zip(df_mf["% Avance"], df_mf["Completadas"], df_mf["Total modulo"])],
                textposition="outside",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=12)
            ))
            fig_m2.update_layout(make_layout(
                xaxis=dict(range=[0,125], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           zeroline=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                yaxis=dict(showgrid=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                margin=dict(t=10,b=10,l=10,r=110),
                height=max(300, len(df_mf) * 36)
            ))
            st.plotly_chart(fig_m2, use_container_width=True)

            st.markdown("---")
            st.markdown("**Detalle de lecciones por módulo y alumno**")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_mod2 = st.selectbox("Módulo", sorted(df_detalle["Modulo"].unique()), key="mod2")
            with col_f2:
                alumnos_mod = sorted(df_detalle[df_detalle["Modulo"]==filtro_mod2]["Nombre"].unique().tolist())
                filtro_al   = st.selectbox("Alumno", ["Todos"] + alumnos_mod, key="al2")
            df_det_fil = df_detalle[df_detalle["Modulo"]==filtro_mod2]
            if filtro_al != "Todos":
                df_det_fil = df_det_fil[df_det_fil["Nombre"]==filtro_al]
            st.dataframe(df_det_fil[["Nombre","Leccion","Completada","Fecha Completado"]],
                         use_container_width=True, hide_index=True)
        else:
            st.warning("No hay datos de módulos disponibles.")

    with tab4:
        caption("Lista exacta de cada <strong>lección que cada alumno NO ha completado</strong>. Filtra por alumno para seguimiento personalizado.")
        if not pendientes_detalle.empty:
            filtro_alumno = st.selectbox("Filtrar por alumno",
                ["Todos"] + sorted(pendientes_detalle["Nombre"].unique().tolist()), key="pend_al")
            df_pf = pendientes_detalle if filtro_alumno == "Todos" else pendientes_detalle[pendientes_detalle["Nombre"]==filtro_alumno]
            st.markdown(f"**{len(df_pf)} lecciones pendientes**")
            st.dataframe(df_pf, use_container_width=True, hide_index=True)
        else:
            st.success("¡Todos los alumnos completaron todas las lecciones!")

    with tab5:
        caption("Tabla cruzada alumno × módulo. Cada celda = <strong>% de avance en ese módulo específico</strong>.")
        if not tabla_cruzada.empty:
            st.dataframe(tabla_cruzada.set_index("Nombre"), use_container_width=True)
            st.caption("Valores en % completado por módulo.")
        else:
            st.warning("No hay suficientes datos para el mapa de progreso.")

    # EXPORTAR
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:2px;background:linear-gradient(90deg,#E8420A,#ff9a7a,transparent);border-radius:2px;margin-bottom:20px;'></div>", unsafe_allow_html=True)

    col_txt, col_btn = st.columns([3, 1])
    with col_txt:
        st.markdown("""
        <p style="font-weight:800;font-size:15px;color:#1a1815;margin-bottom:4px;">Exportar informe completo</p>
        <p style="color:#8c8880;font-size:13px;margin:0;">Excel con 5 pestañas: resumen, por módulo, tabla cruzada, pendientes y detalle completo.</p>
        """, unsafe_allow_html=True)
    with col_btn:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            resumen.to_excel(writer,                sheet_name="Resumen",          index=False)
            if not df_pivot.empty:
                df_pivot.to_excel(writer,           sheet_name="Por modulo",       index=False)
            if not tabla_cruzada.empty:
                tabla_cruzada.to_excel(writer,      sheet_name="Tabla cruzada",    index=False)
            if not pendientes_detalle.empty:
                pendientes_detalle.to_excel(writer, sheet_name="Pendientes",       index=False)
            df_detalle.to_excel(writer,             sheet_name="Detalle completo", index=False)
        buffer.seek(0)
        st.download_button(
            label="📥 Descargar Excel",
            data=buffer,
            file_name=f"club_analytics_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
