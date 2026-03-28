"""
Hotmart Club · Club Analytics v5.2
Fixes: ghost card, chart text, table dark bg, explanatory text, data discrepancy
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
    page_title="Hotmart · Club Analytics",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@300;400;600;700;800;900&display=swap');

* { font-family: 'Nunito Sans', sans-serif !important; }

[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }
.stDeployButton { display: none !important; }

.stApp { background: #faf9f7 !important; }

/* ── Inputs ── */
.stTextInput > div > div > input {
    border-radius: 10px !important;
    border: 1.5px solid #e0ddd8 !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    background: white !important;
    color: #1a1815 !important;
    transition: border-color 0.2s !important;
}
.stTextInput > div > div > input::placeholder { color: #c0bdb8 !important; }
.stTextInput > div > div > input:focus {
    border-color: #E8420A !important;
    box-shadow: 0 0 0 3px rgba(232,66,10,0.1) !important;
    outline: none !important;
}
.stTextInput label {
    font-weight: 700 !important;
    color: #3d3a35 !important;
    font-size: 13px !important;
}

/* ── Botones ── */
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
    box-shadow: 0 4px 15px rgba(232,66,10,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    background: #c93608 !important;
    transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: white !important;
    color: #E8420A !important;
    border: 2px solid #E8420A !important;
    border-radius: 10px !important;
    font-family: 'Nunito Sans', sans-serif !important;
    font-weight: 700 !important;
}

/* ── Métricas ── */
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

/* ── Tabs ── */
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

/* ── Tablas — fondo claro, texto oscuro ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    background: white !important;
}
[data-testid="stDataFrame"] * {
    color: #1a1815 !important;
    font-family: 'Nunito Sans', sans-serif !important;
}
[data-testid="stDataFrame"] th {
    background: #f5f2ee !important;
    color: #3d3a35 !important;
    font-weight: 700 !important;
}
[data-testid="stDataFrame"] td { background: white !important; }
[data-testid="stDataFrame"] tr:hover td { background: #faf9f7 !important; }

/* ── Selects ── */
.stSelectbox > div > div { border-radius: 10px !important; border: 1.5px solid #e0ddd8 !important; }
.stMultiSelect > div > div { border-radius: 10px !important; border: 1.5px solid #e0ddd8 !important; }

/* ── Progress bar ── */
.stProgress > div > div > div { background: #E8420A !important; }

/* ── Caption / texto explicativo ── */
.caption-box {
    background: #f5f2ee;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #5c5a56;
    line-height: 1.6;
    border-left: 3px solid #E8420A;
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
            return [], f"Estructura inesperada"
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

FONT = dict(family="Nunito Sans", color="#3d3a35", size=12)

def chart_layout(**kw):
    return dict(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=FONT, showlegend=False, **kw)

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

for k, v in {"page":"login","token":None,"modulo_info":{},"subdomain":"",
             "club_name":"","modulos_seleccionados":[],"dashboard_data":None}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — LOGIN
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state["page"] == "login":

    _, col_c, _ = st.columns([1, 1.1, 1])
    with col_c:
        st.markdown("<div style='height:48px'></div>", unsafe_allow_html=True)

        # Logo + título
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
            <div style="display:inline-flex; align-items:center; justify-content:center;
                        width:60px; height:60px; background:#E8420A; border-radius:18px;
                        margin-bottom:16px; box-shadow:0 8px 24px rgba(232,66,10,0.35);">
                <span style="font-size:30px; line-height:1;">🔥</span>
            </div>
            <h1 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:28px;
                       color:#1a1815; margin:0;">Club Analytics</h1>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px; margin-top:6px;">
                Analiza el progreso de tus alumnos en Hotmart Club
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Título del formulario (sin div wrapper que causa el ghost card)
        st.markdown("""
        <div style="background:white; border-radius:20px 20px 0 0; padding:24px 24px 0;
                    border:1px solid #f0ede8; border-bottom:none;
                    box-shadow:0 4px 20px rgba(0,0,0,0.06);">
            <p style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:17px;
                      color:#1a1815; margin:0 0 4px;">Conecta tu Club</p>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:13px; margin:0 0 20px;">
                Ingresa tus credenciales de Hotmart Developers
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Wrapper de inputs con CSS de continuación del card
        st.markdown("""<div style="background:white; border:1px solid #f0ede8; border-top:none;
                    border-radius:0 0 20px 20px; padding:0 24px 24px;
                    box-shadow:0 8px 30px rgba(0,0,0,0.06);">
        </div>""", unsafe_allow_html=True)

        # Inputs directamente en Streamlit (sin envolver en HTML)
        basic_token   = st.text_input("Basic Token",         placeholder="Basic NTM5OWZlMD...", key="l_basic")
        client_id     = st.text_input("Client ID",           placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", key="l_cid")
        client_secret = st.text_input("Client Secret",       placeholder="••••••••••••••••", type="password", key="l_secret")
        subdomain_in  = st.text_input("Subdominio del Club", placeholder="mi-curso", key="l_sub",
                                      help="Lo que aparece en hotmart.com/es/club/SUBDOMINIO")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        conectar = st.button("Conectar y ver Analytics →", type="primary", use_container_width=True)

        # Ayuda
        st.markdown("""
        <div style="text-align:center; margin-top:20px;">
            <p style="font-family:'Nunito Sans',sans-serif; color:#b8b4ae; font-size:12px; line-height:1.7;">
                ¿Cómo obtener mis credenciales?<br>
                Entra a <strong style="color:#E8420A;">developers.hotmart.com</strong>
                → crea una aplicación → copia tus credenciales
            </p>
        </div>
        """, unsafe_allow_html=True)

        if conectar:
            if not all([basic_token, client_id, client_secret, subdomain_in]):
                st.error("Por favor completa todos los campos.")
            else:
                with st.spinner("Verificando credenciales..."):
                    token, err = get_access_token(basic_token, client_id, client_secret)
                    if err:
                        st.error(f"Credenciales incorrectas: {err}")
                    else:
                        mods_main, _  = get_modules(token, subdomain_in, is_extra=False)
                        mods_extra, _ = get_modules(token, subdomain_in, is_extra=True)
                        todos = mods_main + mods_extra
                        modulo_info = {}

                        if todos:
                            for m in todos:
                                mid  = m.get("module_id", m.get("id", ""))
                                name = m.get("name", f"Modulo {mid}")
                                pages, _ = get_pages_for_module(token, subdomain_in, mid)
                                total_pages = len([p for p in pages if p.get("type","CONTENT") != "ADVERTISEMENT"]) if pages else 0
                                modulo_info[name] = {"module_id": mid, "total_pages": total_pages, "is_extra": m.get("is_extra", False)}
                        else:
                            students_tmp, _ = get_students(token, subdomain_in)
                            nombres_tmp = set()
                            for s in students_tmp[:15]:
                                uid = s.get("user_id", s.get("id", ""))
                                if not uid: continue
                                lecs, _ = get_student_progress(token, subdomain_in, uid)
                                for l in lecs:
                                    m = l.get("module_name", "")
                                    if m: nombres_tmp.add(m)
                                time.sleep(0.15)
                            for nombre in sorted(nombres_tmp):
                                modulo_info[nombre] = {"module_id": "", "total_pages": 0, "is_extra": False}

                        if not modulo_info:
                            st.error("No se encontraron módulos. Verifica el subdominio.")
                        else:
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
    <div style="display:flex; align-items:center; gap:14px; padding:20px 0 28px;
                border-bottom:2px solid #f0ede8; margin-bottom:32px;">
        <div style="width:42px; height:42px; background:#E8420A; border-radius:12px;
                    display:flex; align-items:center; justify-content:center;
                    box-shadow:0 4px 12px rgba(232,66,10,0.3); font-size:20px;">🔥</div>
        <div>
            <div style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:20px; color:#1a1815;">Club Analytics</div>
            <div style="font-family:'Nunito Sans',sans-serif; font-size:13px; color:#8c8880;">{club_name} · {len(modulo_info)} módulos encontrados</div>
        </div>
    </div>
    <h2 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px; color:#1a1815; margin-bottom:8px;">¿Qué producto quieres analizar?</h2>
    <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px; margin-bottom:28px;">
        Si tu Club tiene varios productos, selecciona solo los módulos del producto que quieres revisar. Si tienes un solo producto, selecciónalos todos.
    </p>
    """, unsafe_allow_html=True)

    col_sel, col_prev = st.columns([1.3, 1])

    with col_sel:
        nombres = list(modulo_info.keys())
        seleccionados = st.multiselect("Módulos a incluir", options=nombres, default=nombres)
        total_lec = sum(modulo_info[m]["total_pages"] for m in seleccionados)
        if seleccionados:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#fff5f2,#fff); border:1.5px solid #ffd4c4;
                        border-radius:14px; padding:18px 20px; margin-top:16px;">
                <div style="font-family:'Nunito Sans',sans-serif; font-size:11px; color:#E8420A;
                            font-weight:800; letter-spacing:0.08em; margin-bottom:4px;">SELECCIÓN ACTUAL</div>
                <div style="font-family:'Nunito Sans',sans-serif; font-size:24px; font-weight:800; color:#1a1815;">{len(seleccionados)} módulos</div>
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

    token            = st.session_state["token"]
    modulo_info      = st.session_state["modulo_info"]
    subdomain        = st.session_state["subdomain"]
    modulos_sel      = st.session_state["modulos_seleccionados"]
    total_lec_reales = sum(modulo_info[m]["total_pages"] for m in modulos_sel)
    usar_total_real  = total_lec_reales > 0

    _, col_c, _ = st.columns([1, 1.5, 1])
    with col_c:
        st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align:center; margin-bottom:32px;">
            <div style="font-size:40px; margin-bottom:16px;">🔥</div>
            <h2 style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px; color:#1a1815; margin-bottom:8px;">Analizando tu Club...</h2>
            <p style="font-family:'Nunito Sans',sans-serif; color:#8c8880; font-size:14px;">Extrayendo el progreso de cada alumno. Esto puede tomar unos segundos.</p>
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
        uid         = student.get("user_id", student.get("id", ""))
        name        = student.get("name", "Sin nombre")
        email       = student.get("email", "")
        prog_obj    = student.get("progress", {})
        pct_hotmart = prog_obj.get("completed_percentage", 0)
        comp_hotmart = prog_obj.get("completed", 0)
        total_hotmart = prog_obj.get("total", 0)

        prog_bar.progress((i + 1) / len(students))
        status_txt.markdown(f"<p style='font-family:Nunito Sans,sans-serif;text-align:center;color:#8c8880;font-size:13px;'>Analizando {i+1} de {len(students)} alumnos...</p>", unsafe_allow_html=True)

        if not uid:
            errores.append({"alumno": name, "error": "user_id vacio"}); continue

        lecciones, err_l = get_student_progress(token, subdomain, uid)
        if err_l: errores.append({"alumno": name, "error": err_l})

        if not lecciones:
            all_data.append({
                "Nombre": name, "Email": email, "Modulo": "Sin actividad",
                "Leccion": "Sin actividad", "Completada": "No", "Fecha Completado": "",
                "Pct Hotmart": pct_hotmart, "Comp Hotmart": comp_hotmart, "Total Hotmart": total_hotmart
            })
            time.sleep(0.15); continue

        for l in lecciones:
            mn = l.get("module_name", "Sin modulo")
            if mn not in modulos_sel: continue
            fecha = ""
            if l.get("completed_date"):
                fecha = datetime.fromtimestamp(l["completed_date"] / 1000).strftime("%d/%m/%Y")
            all_data.append({
                "Nombre": name, "Email": email, "Modulo": mn,
                "Leccion": l.get("page_name", "Sin nombre"),
                "Completada": "Si" if l.get("is_completed") else "No",
                "Fecha Completado": fecha,
                "Pct Hotmart": pct_hotmart,
                "Comp Hotmart": comp_hotmart,
                "Total Hotmart": total_hotmart
            })
        time.sleep(0.15)

    prog_bar.progress(1.0)
    status_txt.markdown("<p style='font-family:Nunito Sans,sans-serif;text-align:center;color:#1aab6d;font-size:14px;font-weight:800;'>✓ ¡Análisis completado!</p>", unsafe_allow_html=True)

    df = pd.DataFrame(all_data)
    df_activos = df[df["Modulo"] != "Sin actividad"]

    resumen_rows = []
    for nombre, grupo in df.groupby("Nombre"):
        email         = grupo["Email"].iloc[0]
        pct_hotmart   = grupo["Pct Hotmart"].iloc[0]
        comp_hotmart  = grupo["Comp Hotmart"].iloc[0]
        total_hotmart = grupo["Total Hotmart"].iloc[0]
        grupo_activo  = grupo[grupo["Modulo"] != "Sin actividad"]

        if grupo_activo.empty:
            # Sin lecciones registradas — usamos dato de Hotmart como referencia
            pct = float(pct_hotmart) if pct_hotmart else 0.0
            resumen_rows.append({
                "Nombre": nombre, "Email": email,
                "Completadas (API)": int(comp_hotmart), "Total (Hotmart)": int(total_hotmart),
                "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
                "Estado": estado_riesgo(pct),
                "Ultima leccion": "Sin detalle de lección",
                "Ultimo modulo": "—", "Ultima actividad": "—",
                "Modulo abandono": "—", "Leccion abandono": "—"
            }); continue

        completadas_n = int((grupo_activo["Completada"] == "Si").sum())
        # Usamos el total de Hotmart como denominador si está disponible, sino el total real de módulos
        if total_hotmart > 0:
            total_n = int(total_hotmart)
        elif usar_total_real:
            total_n = total_lec_reales
        else:
            total_n = len(grupo_activo)

        pct = min(round(completadas_n / total_n * 100, 1) if total_n > 0 else 0.0, 100.0)
        ul, um, uf, ma, la = calcular_abandono(grupo_activo)
        resumen_rows.append({
            "Nombre": nombre, "Email": email,
            "Completadas (API)": completadas_n, "Total (Hotmart)": total_n,
            "Pct Avance": pct, "Pct Hotmart": pct_hotmart,
            "Estado": estado_riesgo(pct),
            "Ultima leccion": ul, "Ultimo modulo": um, "Ultima actividad": uf,
            "Modulo abandono": ma, "Leccion abandono": la
        })

    resumen = pd.DataFrame(resumen_rows)

    pivot_rows = []
    for m in modulos_sel:
        total_m_real = modulo_info[m]["total_pages"]
        for nombre, g in df_activos[df_activos["Modulo"] == m].groupby("Nombre"):
            comp_m  = int((g["Completada"] == "Si").sum())
            total_m = total_m_real if total_m_real > 0 else len(g)
            pct_m   = min(round(comp_m / total_m * 100, 1) if total_m > 0 else 0.0, 100.0)
            pivot_rows.append({
                "Nombre": nombre, "Modulo": m,
                "Completadas": comp_m, "Total modulo": total_m,
                "Pendientes": max(0, total_m - comp_m), "% Avance": pct_m
            })

    df_pivot      = pd.DataFrame(pivot_rows) if pivot_rows else pd.DataFrame()
    tabla_cruzada = (df_pivot.pivot_table(index="Nombre", columns="Modulo", values="% Avance", fill_value=0).reset_index()
                     if not df_pivot.empty else pd.DataFrame())

    # Detalle completo de lecciones por alumno con estado
    df_detalle = df_activos[["Nombre","Email","Modulo","Leccion","Completada","Fecha Completado"]].copy()
    pendientes_detalle = df_activos[df_activos["Completada"] == "No"][["Nombre","Email","Modulo","Leccion"]].copy()

    st.session_state["dashboard_data"] = {
        "df": df, "df_detalle": df_detalle, "resumen": resumen,
        "df_pivot": df_pivot, "tabla_cruzada": tabla_cruzada,
        "pendientes_detalle": pendientes_detalle, "errores": errores,
        "total_lec_reales": total_lec_reales, "usar_total_real": usar_total_real,
        "modulos_sel": modulos_sel
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
    total_lec_reales   = data["total_lec_reales"]
    modulos_sel        = data["modulos_sel"]
    subdomain          = st.session_state["subdomain"]
    club_name          = st.session_state["club_name"]

    total_alumnos = len(resumen)
    sin_actividad = (resumen["Estado"] == "Sin actividad").sum()
    en_riesgo     = (resumen["Estado"] == "En riesgo").sum()
    en_progreso   = (resumen["Estado"] == "En progreso").sum()
    avanzados     = (resumen["Estado"] == "Avanzado").sum()
    avance_prom   = round(resumen[resumen["Pct Avance"] > 0]["Pct Avance"].mean(), 1) if (resumen["Pct Avance"] > 0).any() else 0
    abandono_mod  = (df_pivot.groupby("Modulo")["Pendientes"].sum().sort_values(ascending=False)
                    if not df_pivot.empty else pd.Series(dtype=float))

    # ── HEADER ────────────────────────────────────────────────────────────────
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"""
        <div style="padding:20px 0 24px;">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
                <div style="width:38px; height:38px; background:#E8420A; border-radius:10px;
                            display:flex; align-items:center; justify-content:center;
                            box-shadow:0 3px 10px rgba(232,66,10,0.3); font-size:18px;">🔥</div>
                <span style="font-family:'Nunito Sans',sans-serif; font-weight:800; font-size:22px; color:#1a1815;">Club Analytics</span>
                <span style="background:#fff5f2; color:#E8420A; border:1px solid #ffd4c4;
                             border-radius:20px; padding:3px 12px; font-size:12px; font-weight:700;">{club_name}</span>
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

    st.markdown("<div style='height:2px; background:linear-gradient(90deg,#E8420A,#ff9a7a,transparent); border-radius:2px; margin-bottom:28px;'></div>", unsafe_allow_html=True)

    # ── KPIs ──────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Alumnos",         total_alumnos)
    c2.metric("📈 Avance promedio", f"{avance_prom}%")
    c3.metric("⚠️ En riesgo",       en_riesgo)
    c4.metric("🔄 En progreso",     en_progreso)
    c5.metric("🏆 Avanzados",       avanzados)

    if sin_actividad > 0:
        st.markdown(f"""
        <div style="background:#fff5f2; border:1.5px solid #ffd4c4; border-radius:12px;
                    padding:12px 18px; margin-top:12px; display:flex; align-items:center; gap:10px;">
            <span style="font-size:18px;">🚨</span>
            <span style="font-family:'Nunito Sans',sans-serif; font-size:14px; color:#c93608; font-weight:700;">
                {sin_actividad} alumno{'s' if sin_actividad > 1 else ''} no {'tienen' if sin_actividad > 1 else 'tiene'} lecciones completadas registradas — riesgo de churn
            </span>
        </div>
        """, unsafe_allow_html=True)

    if errores:
        with st.expander(f"⚠️ {len(errores)} alumnos con error al extraer datos"):
            st.dataframe(pd.DataFrame(errores), use_container_width=True, hide_index=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Resumen general",
        "🎯 Punto de abandono",
        "📚 Por módulo",
        "📋 Lecciones pendientes",
        "🗺️ Mapa de progreso"
    ])

    # ── TAB 1: RESUMEN ────────────────────────────────────────────────────────
    with tab1:
        caption("Vista global de todos los alumnos. El <strong>% de avance</strong> se calcula dividiendo las lecciones completadas entre el total de lecciones del curso según Hotmart. <em>Pct Hotmart</em> es el número oficial de Hotmart para comparación.")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("**Segmentación de alumnos**")
            seg = resumen["Estado"].value_counts().reset_index()
            seg.columns = ["Estado","Cantidad"]
            fig_d = px.pie(seg, names="Estado", values="Cantidad", hole=0.58,
                           color="Estado", color_discrete_map=COLOR_MAP)
            fig_d.update_traces(
                textposition="outside", textinfo="label+value",
                textfont=dict(color="#3d3a35", size=13, family="Nunito Sans"),
                marker=dict(line=dict(color="#faf9f7", width=3))
            )
            fig_d.update_layout(**chart_layout(margin=dict(t=20,b=20,l=20,r=20), height=300))
            st.plotly_chart(fig_d, use_container_width=True)

        with col_r:
            st.markdown("**Progreso por alumno**")
            sorted_r = resumen.sort_values("Pct Avance", ascending=True)
            fig_a = go.Figure(go.Bar(
                x=sorted_r["Pct Avance"], y=sorted_r["Nombre"], orientation="h",
                marker=dict(color=[COLOR_MAP[e] for e in sorted_r["Estado"]], line=dict(width=0)),
                text=[f"{p}%" for p in sorted_r["Pct Avance"]],
                textposition="outside",
                textfont=dict(color="#3d3a35", size=12, family="Nunito Sans"),
                customdata=sorted_r[["Completadas (API)","Total (Hotmart)","Pct Hotmart"]],
                hovertemplate="<b>%{y}</b><br>Avance: %{x}%<br>Hotmart oficial: %{customdata[2]}%<br>%{customdata[0]}/%{customdata[1]} lecciones<extra></extra>"
            ))
            fig_a.update_layout(**chart_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           tickfont=dict(color="#3d3a35", family="Nunito Sans"),
                           zeroline=False),
                yaxis=dict(showgrid=False, tickfont=dict(color="#3d3a35", family="Nunito Sans")),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(300, total_alumnos*34)
            ))
            st.plotly_chart(fig_a, use_container_width=True)

        st.markdown("**Tabla detallada de alumnos**")
        st.dataframe(
            resumen[["Nombre","Email","Completadas (API)","Total (Hotmart)","Pct Avance","Pct Hotmart","Estado"]].sort_values("Pct Avance"),
            use_container_width=True, hide_index=True
        )

    # ── TAB 2: ABANDONO ───────────────────────────────────────────────────────
    with tab2:
        caption("Muestra <strong>dónde exactamente se detuvo cada alumno</strong>: la última lección que completó y en qué módulo dejó de avanzar. También identifica alumnos que nunca marcaron una lección como completada.")

        col_a, col_b = st.columns([1,1])
        with col_a:
            st.markdown("**Alumnos sin lecciones completadas**")
            sin_act = resumen[resumen["Estado"] == "Sin actividad"][["Nombre","Email","Pct Hotmart"]]
            if sin_act.empty:
                st.success("¡Todos los alumnos tienen al menos una lección completada!")
            else:
                st.error(f"{len(sin_act)} alumnos sin lecciones completadas registradas:")
                st.dataframe(sin_act, use_container_width=True, hide_index=True)

        with col_b:
            st.markdown("**Módulos con más lecciones pendientes**")
            st.caption("Aquí se ve dónde se atasca la mayoría de alumnos.")
            if not abandono_mod.empty:
                fig_crit = go.Figure(go.Bar(
                    x=abandono_mod.values, y=abandono_mod.index, orientation="h",
                    marker=dict(color="#E8420A", opacity=0.85, line=dict(width=0)),
                    text=abandono_mod.values, textposition="outside",
                    textfont=dict(color="#3d3a35", size=12, family="Nunito Sans")
                ))
                fig_crit.update_layout(**chart_layout(
                    xaxis=dict(title="Lecciones pendientes acumuladas",
                               tickfont=dict(color="#3d3a35", family="Nunito Sans"),
                               titlefont=dict(color="#3d3a35", family="Nunito Sans")),
                    yaxis=dict(autorange="reversed", tickfont=dict(color="#3d3a35", family="Nunito Sans")),
                    margin=dict(t=10,b=10,l=10,r=60), height=280
                ))
                st.plotly_chart(fig_crit, use_container_width=True)

        st.markdown("---")
        st.markdown("**Última actividad y punto de abandono por alumno**")
        df_ab = resumen[resumen["Ultimo modulo"] != "—"][[
            "Nombre","Email","Estado","Pct Avance","Ultimo modulo",
            "Ultima leccion","Ultima actividad","Modulo abandono","Leccion abandono"
        ]].sort_values("Pct Avance")
        st.dataframe(df_ab, use_container_width=True, hide_index=True)

    # ── TAB 3: POR MÓDULO ─────────────────────────────────────────────────────
    with tab3:
        caption("Analiza el avance dentro de cada módulo del curso. La barra global muestra qué % de alumnos completaron ese módulo en promedio. El zoom permite ver alumno por alumno dentro de un módulo específico.")

        if not df_pivot.empty:
            mod_global = df_pivot.groupby("Modulo").agg(
                Completadas=("Completadas","sum"),
                Pendientes=("Pendientes","sum"),
                Total=("Total modulo","first")
            ).reset_index()
            mod_global["% Global"] = (mod_global["Completadas"] / (mod_global["Total"] * total_alumnos) * 100).clip(0,100).round(1)

            st.markdown("**Completitud por módulo — todos los alumnos**")
            fig_mod = go.Figure(go.Bar(
                x=mod_global["% Global"], y=mod_global["Modulo"], orientation="h",
                marker=dict(
                    color=["#b83208" if p>=60 else "#E8420A" if p>=35 else "#ffb3a0" for p in mod_global["% Global"]],
                    line=dict(width=0)
                ),
                text=[f"{p}%" for p in mod_global["% Global"]],
                textposition="outside",
                textfont=dict(color="#3d3a35", size=12, family="Nunito Sans"),
                customdata=mod_global[["Completadas","Pendientes"]],
                hovertemplate="<b>%{y}</b><br>Completadas: %{customdata[0]}<br>Pendientes: %{customdata[1]}<extra></extra>"
            ))
            fig_mod.update_layout(**chart_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           tickfont=dict(color="#3d3a35", family="Nunito Sans"), zeroline=False),
                yaxis=dict(autorange="reversed", tickfont=dict(color="#3d3a35", family="Nunito Sans"), showgrid=False),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(280, len(mod_global)*46)
            ))
            st.plotly_chart(fig_mod, use_container_width=True)

            st.markdown("---")
            st.markdown("**Zoom: avance alumno por alumno dentro de un módulo**")
            filtro_mod = st.selectbox("Selecciona el módulo", sorted(df_pivot["Modulo"].unique()))
            df_mf = df_pivot[df_pivot["Modulo"]==filtro_mod].sort_values("% Avance")
            fig_m2 = go.Figure(go.Bar(
                x=df_mf["% Avance"], y=df_mf["Nombre"], orientation="h",
                marker=dict(
                    color=["#b83208" if p>=60 else "#E8420A" if p>=35 else "#ffb3a0" for p in df_mf["% Avance"]],
                    line=dict(width=0)
                ),
                text=[f"{p}% ({int(c)}/{int(t)})" for p,c,t in zip(df_mf["% Avance"],df_mf["Completadas"],df_mf["Total modulo"])],
                textposition="outside",
                textfont=dict(color="#3d3a35", size=12, family="Nunito Sans")
            ))
            fig_m2.update_layout(**chart_layout(
                xaxis=dict(range=[0,125], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           tickfont=dict(color="#3d3a35", family="Nunito Sans"), zeroline=False),
                yaxis=dict(tickfont=dict(color="#3d3a35", family="Nunito Sans"), showgrid=False),
                margin=dict(t=10,b=10,l=10,r=110),
                height=max(300, len(df_mf)*36)
            ))
            st.plotly_chart(fig_m2, use_container_width=True)

            st.markdown("**Detalle de lecciones por módulo y alumno**")
            filtro_mod2 = st.selectbox("Módulo a detallar", sorted(df_detalle["Modulo"].unique()), key="mod2")
            filtro_al   = st.selectbox("Alumno", ["Todos"] + sorted(df_detalle[df_detalle["Modulo"]==filtro_mod2]["Nombre"].unique().tolist()), key="al2")
            df_det_fil  = df_detalle[df_detalle["Modulo"]==filtro_mod2]
            if filtro_al != "Todos":
                df_det_fil = df_det_fil[df_det_fil["Nombre"]==filtro_al]
            st.dataframe(df_det_fil[["Nombre","Leccion","Completada","Fecha Completado"]], use_container_width=True, hide_index=True)
        else:
            st.warning("No hay datos de módulos disponibles.")

    # ── TAB 4: LECCIONES PENDIENTES ───────────────────────────────────────────
    with tab4:
        caption("Lista exacta de <strong>cada lección que cada alumno NO ha completado todavía</strong>. Útil para hacer seguimiento puntual o enviar recordatorios personalizados. Filtra por alumno para ver su lista específica.")

        if not pendientes_detalle.empty:
            filtro_alumno = st.selectbox("Filtrar por alumno",
                ["Todos"] + sorted(pendientes_detalle["Nombre"].unique().tolist()))
            df_pf = pendientes_detalle if filtro_alumno == "Todos" else pendientes_detalle[pendientes_detalle["Nombre"]==filtro_alumno]
            st.markdown(f"**{len(df_pf)} lecciones pendientes**")
            st.dataframe(df_pf, use_container_width=True, hide_index=True)
        else:
            st.success("¡Todos los alumnos completaron todas las lecciones!")

    # ── TAB 5: MAPA ───────────────────────────────────────────────────────────
    with tab5:
        caption("Tabla cruzada que muestra el <strong>% de avance de cada alumno en cada módulo</strong>. Permite identificar de un vistazo en qué módulo específico cada alumno está atrasado.")

        if not tabla_cruzada.empty:
            st.dataframe(tabla_cruzada.set_index("Nombre"), use_container_width=True)
            st.caption("Valores en % de avance por módulo. 100 = módulo completado.")
        else:
            st.warning("No hay suficientes datos para el mapa de progreso.")

    # ── EXPORTAR ──────────────────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:2px; background:linear-gradient(90deg,#E8420A,#ff9a7a,transparent); border-radius:2px; margin-bottom:20px;'></div>", unsafe_allow_html=True)

    col_txt, col_btn = st.columns([3,1])
    with col_txt:
        st.markdown("""
        <p style="font-weight:800; font-size:15px; color:#1a1815; margin-bottom:4px;">Exportar informe completo</p>
        <p style="color:#8c8880; font-size:13px; margin:0;">Excel con 5 pestañas: resumen, avance por módulo, tabla cruzada, pendientes y detalle completo.</p>
        """, unsafe_allow_html=True)
    with col_btn:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            resumen.to_excel(writer, sheet_name="Resumen", index=False)
            if not df_pivot.empty:
                df_pivot.to_excel(writer, sheet_name="Por modulo", index=False)
            if not tabla_cruzada.empty:
                tabla_cruzada.to_excel(writer, sheet_name="Tabla cruzada", index=False)
            if not pendientes_detalle.empty:
                pendientes_detalle.to_excel(writer, sheet_name="Pendientes", index=False)
            df_detalle.to_excel(writer, sheet_name="Detalle completo", index=False)
        buffer.seek(0)
        st.download_button(
            label="📥 Descargar Excel",
            data=buffer,
            file_name=f"club_analytics_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
