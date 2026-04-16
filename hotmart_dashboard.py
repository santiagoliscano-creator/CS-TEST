"""
Hotmart Club · Club Analytics v8.1
Feature: state criteria legend for AMs, product filter, paginated UI
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
/* ── Forzar fondo claro y contraste en todos los contenedores ── */
[data-testid="stMarkdown"],
[data-testid="stMarkdown"] div,
[data-testid="stMarkdown"] span { background-color: transparent !important; }
[data-testid="stMainBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stHorizontalBlock"],
[data-testid="stColumn"],
section[data-testid="stSidebar"],
.stTabs [data-baseweb="tab-panel"] { background-color: transparent !important; }
header[data-testid="stHeader"] { display:none !important; }
/* Forzar color base de texto para evitar herencia de dark mode */
.stApp, .stApp div, .stApp span, .stApp p, .stApp h1, .stApp h2, .stApp h3 { color: #3d3a35; }
[data-testid="stSelectbox"] label { color:#3d3a35 !important; font-weight:700 !important; font-size:13px !important; }
[data-testid="stMultiSelect"] label { color:#3d3a35 !important; font-weight:700 !important; font-size:13px !important; }
.stSelectbox > div > div { background:white !important; color:#1a1815 !important; }
.stMultiSelect > div > div { background:white !important; color:#1a1815 !important; }
/* Expanders */
[data-testid="stExpander"] { background:white !important; border-radius:12px !important; }
[data-testid="stExpander"] summary span { color:#3d3a35 !important; }
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
        for key in ("items", "users", "content", "students", "data", "results", "records"):
            val = data.get(key)
            if isinstance(val, list) and val:
                return val
        for key, val in data.items():
            if isinstance(val, list) and val and key not in ("errors", "warnings"):
                return val
    return []


def _extract_page_token(data):
    """Busca el token de paginación en cualquier ubicación del response."""
    if not isinstance(data, dict):
        return None
    for key in ("next_page_token", "nextPageToken", "page_token", "cursor", "nextCursor"):
        token = data.get(key)
        if token:
            return token
    for wrapper_key in ("pagination", "paging", "page_info", "meta"):
        wrapper = data.get(wrapper_key)
        if isinstance(wrapper, dict):
            for key in ("next_page_token", "nextPageToken", "page_token", "cursor", "next"):
                token = wrapper.get(key)
                if token:
                    return token
    return None


def _try_get_students_endpoint(access_token, subdomain, base_url, max_pages=100):
    """Intenta obtener alumnos de un endpoint específico con paginación."""
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
    todos = []
    page_token = None
    diagnostics = []

    for page_num in range(max_pages):
        url = f"{base_url}?subdomain={subdomain}&max_results=50"
        if page_token:
            url += f"&page_token={page_token}"

        diag = {"page": page_num + 1, "url": url}
        try:
            resp = requests.get(url, headers=headers, timeout=20)
            diag["status_code"] = resp.status_code
            diag["body_length"] = len(resp.text) if resp.text else 0

            resp_headers = resp.headers
            location_header = resp_headers.get("Location", "")
            x_cache = resp_headers.get("X-Cache", "")
            has_ratelimit = "RateLimit-Limit" in resp_headers
            diag["location_header"] = location_header
            diag["x_cache"] = x_cache
            diag["reached_api_backend"] = has_ratelimit

            if location_header == "/docs/" or "Error from cloudfront" in x_cache:
                diag["result"] = "CloudFront redirect — no llega al API backend"
                diagnostics.append(diag)
                if page_num == 0:
                    return [], "cloudfront_redirect", diagnostics
                break

            if resp.status_code not in (200, 204):
                diag["result"] = f"HTTP {resp.status_code}"
                diagnostics.append(diag)
                return todos, f"HTTP {resp.status_code}", diagnostics

            if not resp.text or not resp.text.strip():
                diag["result"] = "Empty body"
                diagnostics.append(diag)
                if page_num == 0:
                    return [], "empty_body", diagnostics
                break

            data = resp.json()
            diag["json_type"] = type(data).__name__
            if isinstance(data, dict):
                diag["json_keys"] = list(data.keys())

            items = _extract_items_from_response(data)
            diag["items_found"] = len(items)

            if not items:
                diag["result"] = "No items in response"
                diagnostics.append(diag)
                if page_num == 0:
                    return [], "no_items", diagnostics
                break

            if page_num == 0 and items and isinstance(items[0], dict):
                diag["first_item_keys"] = list(items[0].keys())

            todos.extend(items)
            diag["result"] = f"OK - {len(items)} items"
            diagnostics.append(diag)

            if isinstance(data, dict):
                page_token = _extract_page_token(data)
                if not page_token:
                    break
            else:
                break

        except Exception as e:
            diag["result"] = f"Exception: {str(e)}"
            diagnostics.append(diag)
            return todos if todos else [], str(e), diagnostics

    return todos, None, diagnostics


def get_students(access_token, subdomain):
    """Obtiene TODOS los alumnos probando múltiples versiones de la API."""
    endpoints = [
        ("v1", "https://developers.hotmart.com/club/api/v1/users"),
    ]

    all_diagnostics = []
    got_cloudfront_redirect = False

    for version_label, base_url in endpoints:
        students, err, diag = _try_get_students_endpoint(access_token, subdomain, base_url)
        for d in diag:
            d["api_version"] = version_label
        all_diagnostics.extend(diag)

        if students:
            return students, None, all_diagnostics

        if err == "cloudfront_redirect":
            got_cloudfront_redirect = True

        if err and err not in ("empty_body", "no_items", "cloudfront_redirect"):
            return [], err, all_diagnostics

    if got_cloudfront_redirect:
        return [], "cloudfront_redirect", all_diagnostics

    return [], "no_data", all_diagnostics


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
                for key in ("lessons", "items", "content", "data", "results"):
                    val = data.get(key)
                    if isinstance(val, list):
                        return val, None
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

PAGE_SIZE = 20

def paginated_bar_chart(df, x_col, y_col, color_values, text_list, key_prefix,
                        layout_kwargs=None, textfont=None, customdata=None,
                        hovertemplate=None, orientation="h"):
    """Muestra un gráfico de barras paginado con navegación."""
    total = len(df)
    if total <= PAGE_SIZE:
        return df, total

    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
    page = st.selectbox(
        f"Página (de {total_pages})",
        range(1, total_pages + 1),
        format_func=lambda p: f"{p} de {total_pages} · alumnos {(p-1)*PAGE_SIZE+1}–{min(p*PAGE_SIZE, total)}",
        key=f"page_{key_prefix}"
    )
    start = (page - 1) * PAGE_SIZE
    end = min(start + PAGE_SIZE, total)
    return df.iloc[start:end], total

def paginated_dataframe(df, key_prefix, page_size=PAGE_SIZE):
    """Muestra un dataframe paginado con navegación."""
    total = len(df)
    if total <= page_size:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return

    total_pages = (total + page_size - 1) // page_size
    col_info, col_nav = st.columns([2, 1])
    with col_info:
        st.markdown(f"<p style='color:#8c8880;font-size:12px;margin:0;'>{total} registros en total</p>", unsafe_allow_html=True)
    with col_nav:
        page = st.selectbox(
            "Página",
            range(1, total_pages + 1),
            format_func=lambda p: f"{p} de {total_pages}",
            key=f"tbl_{key_prefix}",
            label_visibility="collapsed"
        )
    start = (page - 1) * page_size
    end = min(start + page_size, total)
    st.dataframe(df.iloc[start:end], use_container_width=True, hide_index=True)


def render_estados_legend():
    """Renderiza la leyenda explicativa de los estados de alumno."""
    st.markdown("""
    <div style="background:white;border:1px solid #f0ede8;border-radius:12px;padding:18px 22px;margin-top:16px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:14px;">
            <span style="font-size:14px;">ℹ️</span>
            <span style="font-weight:800;font-size:13px;color:#1a1815;letter-spacing:0.02em;">¿CÓMO SE CLASIFICAN LOS ALUMNOS?</span>
        </div>
        <p style="color:#8c8880;font-size:12px;margin:0 0 14px 0;line-height:1.5;">
            La clasificación se basa en el <strong style="color:#3d3a35;">% de avance oficial de Hotmart</strong> por alumno (completed_percentage de la API). Estos rangos ayudan a priorizar acciones de Customer Success.
        </p>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;">
            <div style="background:#fff5f2;border-left:4px solid #ffb3a0;border-radius:8px;padding:12px 14px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ffb3a0;"></div>
                    <strong style="font-size:13px;color:#1a1815;">Sin actividad</strong>
                    <span style="margin-left:auto;font-size:11px;color:#8c8880;font-weight:700;">0%</span>
                </div>
                <p style="font-size:11px;color:#5c5a56;margin:0;line-height:1.5;">
                    Alumnos matriculados que nunca han ingresado al contenido. <strong>Riesgo de churn inmediato</strong> — acción recomendada: contactar hoy.
                </p>
            </div>
            <div style="background:#fff5f2;border-left:4px solid #ff7c4d;border-radius:8px;padding:12px 14px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#ff7c4d;"></div>
                    <strong style="font-size:13px;color:#1a1815;">En riesgo</strong>
                    <span style="margin-left:auto;font-size:11px;color:#8c8880;font-weight:700;">1% – 29%</span>
                </div>
                <p style="font-size:11px;color:#5c5a56;margin:0;line-height:1.5;">
                    Iniciaron pero abandonaron temprano. <strong>Riesgo de churn moderado</strong> — acción: identificar fricciones y reactivar con contenido específico.
                </p>
            </div>
            <div style="background:#fff5f2;border-left:4px solid #E8420A;border-radius:8px;padding:12px 14px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#E8420A;"></div>
                    <strong style="font-size:13px;color:#1a1815;">En progreso</strong>
                    <span style="margin-left:auto;font-size:11px;color:#8c8880;font-weight:700;">30% – 79%</span>
                </div>
                <p style="font-size:11px;color:#5c5a56;margin:0;line-height:1.5;">
                    Alumnos activos con avance consistente. <strong>Foco en retención</strong> — acción: mantener el engagement con recordatorios y celebrar hitos.
                </p>
            </div>
            <div style="background:#fff5f2;border-left:4px solid #b83208;border-radius:8px;padding:12px 14px;">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <div style="width:10px;height:10px;border-radius:50%;background:#b83208;"></div>
                    <strong style="font-size:13px;color:#1a1815;">Avanzado</strong>
                    <span style="margin-left:auto;font-size:11px;color:#8c8880;font-weight:700;">80% – 100%</span>
                </div>
                <p style="font-size:11px;color:#5c5a56;margin:0;line-height:1.5;">
                    Alumnos de alto engagement, cerca de completar el curso. <strong>Oportunidad comercial</strong> — acción: upsell a otros productos, testimonios, referidos.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def calcular_abandono(df_alumno):
    completadas = df_alumno[df_alumno["Completada"] == "Si"].sort_values("Fecha Completado", ascending=False)
    pendientes  = df_alumno[df_alumno["Completada"] != "Si"]
    ul = completadas.iloc[0]["Leccion"]          if not completadas.empty else "—"
    um = completadas.iloc[0]["Modulo"]           if not completadas.empty else "—"
    uf = completadas.iloc[0]["Fecha Completado"] if not completadas.empty else "—"
    ma = pendientes.iloc[0]["Modulo"]            if not pendientes.empty else "Completado ✓"
    la = pendientes.iloc[0]["Leccion"]           if not pendientes.empty else "Completado ✓"
    return ul, um, uf, ma, la


def detectar_tipo(page_type_raw, page_name):
    """Detecta el tipo de contenido usando el campo type de la API de páginas
    y como fallback usa el nombre de la página."""
    if page_type_raw:
        pt = str(page_type_raw).upper()
        if any(k in pt for k in ["QUIZ", "SURVEY", "QUESTIONNAIRE"]): return "Cuestionario"
        if any(k in pt for k in ["VIDEO", "MEDIA", "VIMEO", "YOUTUBE"]):  return "Video"
        if any(k in pt for k in ["PDF", "DOCUMENT", "FILE"]):             return "Documento"
        if any(k in pt for k in ["LINK", "URL", "EMBED", "EXTERNAL"]):    return "Link"
        if any(k in pt for k in ["TEXT", "RICH_TEXT", "HTML"]):           return "Texto"
    pn = (page_name or "").lower()
    if any(k in pn for k in ["cuestionario", "quiz", "evaluac", "test", "examen"]): return "Cuestionario"
    if any(k in pn for k in ["(grabación)", "grabacion", "(recording)", "video"]):  return "Video"
    if any(k in pn for k in ["(link)", "invite", "(invite)", "enlace"]):            return "Link"
    if any(k in pn for k in ["pdf", "documento", "material"]):                      return "Documento"
    return "Clase"


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
            <p style="color:#8c8880; font-size:12px; line-height:1.7;">
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
                        students_check, err_st, diag_st = get_students(token, subdomain_in)
                        if not students_check:
                            is_cloudfront = (err_st == "cloudfront_redirect")

                            if is_cloudfront:
                                st.markdown(f"""
                                <div style="background:#fff5f2;border:1.5px solid #ffd4c4;border-radius:12px;padding:18px 20px;margin:12px 0;">
                                    <p style="font-weight:700;color:#c93608;font-size:15px;margin-bottom:8px;">
                                        El subdominio '{subdomain_in}' no está registrado en la API de Hotmart Developers
                                    </p>
                                    <p style="color:#5c5a56;font-size:13px;line-height:1.7;margin-bottom:12px;">
                                        La petición fue interceptada por CloudFront (CDN) y redirigida a <code>/docs/</code>
                                        sin llegar al backend de la API. Los headers muestran <code>X-Cache: Error from cloudfront</code>
                                        y no hay RateLimit headers — esto confirma que la API no reconoce este subdominio.
                                    </p>
                                    <p style="color:#5c5a56;font-size:13px;line-height:1.7;margin-bottom:12px;">
                                        Tus credenciales son correctas (la autenticación fue exitosa), pero este Club específico no está
                                        habilitado para la API de Hotmart Developers.
                                    </p>
                                    <p style="font-weight:700;color:#1a1815;font-size:13px;margin-bottom:6px;">Posibles causas:</p>
                                    <p style="color:#5c5a56;font-size:13px;line-height:1.7;margin:0;">
                                        • El Club está en una versión de la plataforma no soportada por la API actual<br>
                                        • El subdominio no está correctamente registrado en el gateway de la API<br>
                                        • <strong>Recomendación:</strong> Escalar con el equipo de Hotmart Developers para que habiliten este subdominio
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                detail = f" Detalle: {err_st}" if err_st else ""
                                st.error(
                                    f"No se encontraron alumnos en el subdominio '{subdomain_in}'.{detail}\n\n"
                                    f"Verifica que:\n"
                                    f"- El subdominio sea exacto (sin espacios, en minúsculas)\n"
                                    f"- Tu cuenta tenga acceso a este Club\n"
                                    f"- El Club tenga al menos un alumno matriculado"
                                )

                            if diag_st:
                                with st.expander("🔍 Diagnóstico técnico", expanded=False):
                                    for d in diag_st:
                                        label = d.get('api_version', '?')
                                        st.code(
                                            f"API {label} — Página {d.get('page', '?')}\n"
                                            f"Status: {d.get('status_code', '?')}\n"
                                            f"Body: {d.get('body_length', '?')} chars\n"
                                            f"Location header: {d.get('location_header', 'N/A')}\n"
                                            f"X-Cache: {d.get('x_cache', 'N/A')}\n"
                                            f"Reached API backend: {d.get('reached_api_backend', 'N/A')}\n"
                                            f"Result: {d.get('result', '?')}",
                                            language="text"
                                        )
                            st.stop()

                        mods_main, _  = get_modules(token, subdomain_in, is_extra=False)
                        mods_extra, _ = get_modules(token, subdomain_in, is_extra=True)
                        todos_mods = mods_main + mods_extra
                        modulo_info = {}

                        if todos_mods:
                            for m in todos_mods:
                                mid  = m.get("module_id", m.get("id", ""))
                                name = m.get("name", f"Modulo {mid}")
                                # Siempre obtener las páginas completas para cross-referencing
                                pages_raw = []
                                if mid:
                                    pages_raw, _ = get_pages_for_module(token, subdomain_in, mid)
                                pages = [p for p in pages_raw if p.get("type", "CONTENT") != "ADVERTISEMENT"] if pages_raw else []
                                total_pages = m.get("total_pages", 0) or len(pages)
                                classes = m.get("classes", [])
                                modulo_info[name] = {
                                    "module_id": mid, "total_pages": total_pages,
                                    "is_extra": m.get("is_extra", False),
                                    "classes": classes, "pages": pages
                                }
                        else:
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
            <div style="font-size:13px;color:#8c8880;">{club_name} · {len(modulo_info)} módulos</div>
        </div>
    </div>
    <h2 style="font-weight:800;font-size:22px;color:#1a1815;margin-bottom:8px;">¿Qué módulos quieres analizar?</h2>
    <p style="color:#8c8880;font-size:14px;margin-bottom:28px;">Selecciona los módulos a incluir en el dashboard. Puedes analizar uno o todos.</p>
    """, unsafe_allow_html=True)

    col_sel, col_prev = st.columns([1.3, 1])
    with col_sel:
        nombres = list(modulo_info.keys())
        seleccionados = st.multiselect("Módulos a incluir", options=nombres, default=nombres)
        total_lec = sum(modulo_info.get(m, {}).get("total_pages", 0) for m in seleccionados)
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
                    <div style="font-size:11px;color:#8c8880;">{'Extra' if info['is_extra'] else 'Principal'}{' · ' + str(pages) + ' clases' if pages > 0 else ''}</div>
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

    students, err2, _ = get_students(token, subdomain)
    if not students:
        with col_c:
            st.error(f"No se pudo obtener la lista de alumnos: {err2}")
            if st.button("← Volver"): st.session_state["page"] = "selector"; st.rerun()
        st.stop()

    # ── CARGA RÁPIDA: solo datos de /users, sin llamar /lessons ─────────────
    # El endpoint /users ya trae completed_percentage, completed y total por alumno.
    # Las llamadas a /lessons (1 por alumno) se hacen on-demand en los tabs 3 y 4.
    # Esto permite cargar 5.000+ alumnos en segundos en vez de 50 minutos.
    # ────────────────────────────────────────────────────────────────────────
    errores       = []
    resumen_rows  = []
    student_index = []

    total_students = len(students)
    for i, student in enumerate(students):
        uid          = student.get("user_id", student.get("id", ""))
        name         = student.get("name", "Sin nombre")
        email        = student.get("email", "")
        prog_obj     = student.get("progress", {}) or {}
        pct_hotmart  = float(prog_obj.get("completed_percentage", 0) or 0)
        comp_hotmart = int(prog_obj.get("completed", 0) or 0)
        tot_hotmart  = int(prog_obj.get("total", 0) or 0)
        estado       = estado_riesgo(pct_hotmart)

        prog_bar.progress((i + 1) / total_students)
        if i % 50 == 0 or i == total_students - 1:
            status_txt.markdown(
                f"<p style='text-align:center;color:#8c8880;font-size:13px;'>"
                f"Procesando {i+1} de {total_students} alumnos...</p>",
                unsafe_allow_html=True
            )

        if not uid:
            errores.append({"Alumno": name, "Error": "user_id vacio"}); continue

        student_index.append({
            "uid": uid, "Nombre": name, "Email": email,
            "Pct Hotmart": pct_hotmart, "Estado": estado,
            "Completadas": comp_hotmart, "Total": tot_hotmart
        })
        resumen_rows.append({
            "Nombre": name, "Email": email,
            "Completadas": comp_hotmart, "Total lecciones": tot_hotmart,
            "% Avance": pct_hotmart, "Estado": estado,
            # Campos de detalle — se llenan on-demand desde /lessons
            "Ultima leccion": "—", "Ultimo modulo": "—",
            "Ultima actividad": "—", "Modulo abandono": "—", "Leccion abandono": "—"
        })

    prog_bar.progress(1.0)
    status_txt.markdown(
        "<p style='text-align:center;color:#1aab6d;font-size:14px;font-weight:800;'>"
        "✓ ¡Listo!</p>", unsafe_allow_html=True
    )

    resumen = pd.DataFrame(resumen_rows)

    st.session_state["dashboard_data"] = {
        "resumen": resumen,
        "df_pivot": pd.DataFrame(),       # vacío — se llena on-demand en Tab 3
        "tabla_cruzada": pd.DataFrame(),  # vacío — se llena on-demand en Tab 5
        "errores": errores,
        "modulos_sel": modulos_sel,
        "total_alumnos_raw": total_students,
        "student_index": student_index,
        "modulo_data_loaded": False,      # flag: ¿ya se cargaron datos por módulo?
    }
    time.sleep(0.3)
    st.session_state["page"] = "dashboard"
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

elif st.session_state["page"] == "dashboard":

    data              = st.session_state["dashboard_data"]
    resumen           = data["resumen"]
    df_pivot          = data["df_pivot"]
    tabla_cruzada     = data["tabla_cruzada"]
    errores           = data["errores"]
    modulos_sel       = data["modulos_sel"]
    total_alumnos_raw = data["total_alumnos_raw"]
    student_index     = data.get("student_index", [])
    subdomain         = st.session_state["subdomain"]
    club_name         = st.session_state["club_name"]
    token             = st.session_state["token"]
    modulo_info       = st.session_state["modulo_info"]
    modulo_data_loaded = data.get("modulo_data_loaded", False)

    # ── Helper: cargar datos por módulo para todos los alumnos ──────────────
    def cargar_datos_modulo():
        """Llama /lessons para cada alumno y construye df_pivot + tabla_cruzada.
        Se ejecuta solo cuando el usuario lo solicita explícitamente."""
        pivot_rows = []
        prog_mod = st.progress(0)
        txt_mod  = st.empty()
        total_s  = len(student_index)
        for idx, s in enumerate(student_index):
            prog_mod.progress((idx + 1) / total_s)
            if idx % 50 == 0 or idx == total_s - 1:
                txt_mod.markdown(
                    f"<p style='color:#8c8880;font-size:12px;text-align:center;'>"
                    f"Cargando módulos: {idx+1} de {total_s}</p>",
                    unsafe_allow_html=True
                )
            lecs, _ = get_student_progress(token, subdomain, s["uid"])
            lecs_map = {l.get("page_id"): l for l in (lecs or []) if l.get("page_id")}
            for mn in modulos_sel:
                mod_pages = modulo_info.get(mn, {}).get("pages", [])
                if mod_pages:
                    comp_m = sum(
                        1 for p in mod_pages
                        if lecs_map.get(p.get("page_id", p.get("id",""))) and
                           lecs_map[p.get("page_id", p.get("id",""))].get("is_completed")
                    )
                    total_m = len(mod_pages)
                else:
                    lecs_mod = [l for l in (lecs or []) if l.get("module_name") == mn]
                    comp_m   = sum(1 for l in lecs_mod if l.get("is_completed"))
                    total_m  = len(lecs_mod)
                if total_m > 0:
                    pct_m = min(round(comp_m / total_m * 100, 1), 100.0)
                    pivot_rows.append({
                        "Nombre": s["Nombre"], "Modulo": mn,
                        "Completadas": comp_m, "Total modulo": total_m,
                        "Pendientes": max(0, total_m - comp_m), "% Avance": pct_m
                    })
            time.sleep(0.05)
        prog_mod.empty()
        txt_mod.empty()

        df_pivot_new = pd.DataFrame(pivot_rows) if pivot_rows else pd.DataFrame()
        tc_new = (
            df_pivot_new.pivot_table(index="Nombre", columns="Modulo",
                                     values="% Avance", fill_value=0).reset_index()
            if not df_pivot_new.empty else pd.DataFrame()
        )
        data["df_pivot"]          = df_pivot_new
        data["tabla_cruzada"]     = tc_new
        data["modulo_data_loaded"] = True
        st.session_state["dashboard_data"] = data
        st.rerun()
    # ────────────────────────────────────────────────────────────────────────

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

    # LEYENDA DE ESTADOS
    render_estados_legend()

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
            sorted_r = resumen.sort_values("% Avance", ascending=False)
            page_df, page_total = paginated_bar_chart(sorted_r, "% Avance", "Nombre", None, None, "tab1_bar")
            fig_a = go.Figure(go.Bar(
                x=page_df["% Avance"], y=page_df["Nombre"], orientation="h",
                marker_color=[COLOR_MAP[e] for e in page_df["Estado"]],
                text=[f"{p}%" for p in page_df["% Avance"]],
                textposition="outside",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=11),
                customdata=page_df[["Completadas","Total lecciones"]],
                hovertemplate="<b>%{y}</b><br>%{x}% · %{customdata[0]}/%{customdata[1]} lecciones<extra></extra>"
            ))
            fig_a.update_layout(make_layout(
                xaxis=dict(range=[0,115], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           zeroline=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                yaxis=dict(showgrid=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                margin=dict(t=10,b=10,l=10,r=60),
                height=max(300, len(page_df) * 28)
            ))
            st.plotly_chart(fig_a, use_container_width=True)

        st.markdown("**Tabla detallada**")
        paginated_dataframe(
            resumen[["Nombre","Email","Completadas","Total lecciones","% Avance","Estado"]].sort_values("% Avance", ascending=False),
            "tab1_tabla"
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
                paginated_dataframe(sin_act, "tab2_sinact")

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
                n_s = len(student_index)
                st.markdown(f"""
                <div style="background:#fffbf0;border:1.5px solid #f0d070;border-radius:10px;
                            padding:12px 16px;display:flex;gap:10px;align-items:flex-start;">
                    <span style="font-size:16px;">📊</span>
                    <div>
                        <strong style="color:#7a5c00;font-size:13px;">Datos por módulo no cargados</strong>
                        <p style="color:#7a5c00;font-size:12px;margin:4px 0 0 0;line-height:1.5;">
                            Requiere {n_s} llamadas adicionales (~{max(1,round(n_s*0.6/60))} min).
                            Cárgalos desde el Tab "Por módulo".
                        </p>
                    </div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Última actividad y punto de abandono**")
        st.caption("Disponible después de cargar datos por módulo desde el Tab 📚.")
        df_ab = resumen[resumen["Ultimo modulo"] != "—"][[
            "Nombre","Email","Estado","% Avance",
            "Ultimo modulo","Ultima leccion","Ultima actividad",
            "Modulo abandono","Leccion abandono"
        ]].sort_values("% Avance")
        if not df_ab.empty:
            paginated_dataframe(df_ab, "tab2_abandono")
        else:
            st.info("Sin datos de abandono — carga los datos por módulo para ver el detalle.")

    with tab3:
        caption("Avance <strong>dentro de cada módulo</strong>. Requiere una carga adicional on-demand.")

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
            df_mf = df_pivot[df_pivot["Modulo"] == filtro_mod].sort_values("% Avance", ascending=False)
            page_mf, _ = paginated_bar_chart(df_mf, "% Avance", "Nombre", None, None, "tab3_zoom")
            fig_m2 = go.Figure(go.Bar(
                x=page_mf["% Avance"], y=page_mf["Nombre"], orientation="h",
                marker_color=bar_colors(page_mf["% Avance"]),
                text=[f"{p}% ({int(c)}/{int(t)})" for p,c,t in zip(page_mf["% Avance"], page_mf["Completadas"], page_mf["Total modulo"])],
                textposition="outside",
                textfont=dict(family="Nunito Sans", color="#3d3a35", size=12)
            ))
            fig_m2.update_layout(make_layout(
                xaxis=dict(range=[0,125], ticksuffix="%", showgrid=True, gridcolor="#f0ede8",
                           zeroline=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                yaxis=dict(showgrid=False, tickfont=dict(family="Nunito Sans", color="#3d3a35")),
                margin=dict(t=10,b=10,l=10,r=110),
                height=max(300, len(page_mf) * 36)
            ))
            st.plotly_chart(fig_m2, use_container_width=True)

            st.markdown("---")
            st.markdown("**Detalle de lecciones por módulo y alumno**")
            nombres_index = sorted([s["Nombre"] for s in student_index])
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_mod2 = st.selectbox("Módulo", sorted(modulos_sel), key="mod2")
            with col_f2:
                filtro_al = st.selectbox("Alumno", ["Todos"] + nombres_index, key="al2")

            if filtro_al == "Todos":
                n_alumnos = len(student_index)
                st.markdown(f"""
                <div style="background:#fffbf0;border:1.5px solid #f0d070;border-radius:10px;
                            padding:12px 16px;margin-bottom:12px;display:flex;gap:10px;align-items:flex-start;">
                    <span style="font-size:18px;">⏳</span>
                    <div>
                        <strong style="color:#7a5c00;font-size:13px;">Carga con tiempo de espera</strong>
                        <p style="color:#7a5c00;font-size:12px;margin:4px 0 0 0;line-height:1.6;">
                            Ver el detalle de todos los alumnos requiere {n_alumnos} llamadas adicionales a la API
                            (~{max(1, round(n_alumnos * 0.6 / 60))} min aprox).
                            Selecciona un alumno específico para carga inmediata (1–2 seg).
                        </p>
                    </div>
                </div>""", unsafe_allow_html=True)
                cargar_det = st.button("Cargar detalle de todos los alumnos", key="load_all_tab3")
            else:
                cargar_det = True

            if cargar_det:
                mod_pages = modulo_info.get(filtro_mod2, {}).get("pages", [])
                alumnos_a_cargar = (
                    student_index if filtro_al == "Todos"
                    else [s for s in student_index if s["Nombre"] == filtro_al]
                )
                det_rows = []
                prog_det = st.progress(0)
                for idx, s in enumerate(alumnos_a_cargar):
                    prog_det.progress((idx + 1) / len(alumnos_a_cargar))
                    lecs, _ = get_student_progress(token, subdomain, s["uid"])
                    lecs_map = {l.get("page_id"): l for l in (lecs or []) if l.get("page_id")}
                    if mod_pages:
                        for page in mod_pages:
                            pid    = page.get("page_id", page.get("id", ""))
                            pname  = page.get("page_name", page.get("name", "Sin nombre"))
                            tipo   = detectar_tipo(page.get("content_type", page.get("type", "")), pname)
                            lesson = lecs_map.get(pid)
                            if lesson:
                                completada = "Si" if lesson.get("is_completed") else "No"
                                fecha = ""
                                if lesson.get("completed_date"):
                                    try: fecha = datetime.fromtimestamp(lesson["completed_date"]/1000).strftime("%d/%m/%Y")
                                    except: pass
                            else:
                                completada, fecha = "No iniciada", ""
                            det_rows.append({"Nombre": s["Nombre"], "Tipo": tipo,
                                             "Leccion": pname, "Completada": completada,
                                             "Fecha Completado": fecha})
                    else:
                        for l in (lecs or []):
                            if l.get("module_name") != filtro_mod2: continue
                            pname = l.get("page_name", "Sin nombre")
                            fecha = ""
                            if l.get("completed_date"):
                                try: fecha = datetime.fromtimestamp(l["completed_date"]/1000).strftime("%d/%m/%Y")
                                except: pass
                            det_rows.append({"Nombre": s["Nombre"], "Tipo": detectar_tipo("", pname),
                                             "Leccion": pname,
                                             "Completada": "Si" if l.get("is_completed") else "No",
                                             "Fecha Completado": fecha})
                    time.sleep(0.05)
                prog_det.empty()
                if det_rows:
                    df_det = pd.DataFrame(det_rows)
                    tipos_disp = sorted(df_det["Tipo"].unique().tolist())
                    filtro_tipo = st.multiselect("Tipo de contenido", options=tipos_disp,
                                                 default=tipos_disp, key="tipo_det3")
                    if filtro_tipo:
                        df_det = df_det[df_det["Tipo"].isin(filtro_tipo)]
                    st.caption("✅ Si = completada · ⏳ No = abierta pero pendiente · 🔒 No iniciada = nunca abierta")
                    paginated_dataframe(df_det, "tab3_detalle")
                else:
                    st.info("No hay datos de lecciones para esta selección.")
        else:
            # df_pivot vacío — ofrecer carga on-demand
            n_s = len(student_index)
            st.markdown(f"""
            <div style="background:#fffbf0;border:1.5px solid #f0d070;border-radius:12px;
                        padding:18px 20px;margin-bottom:16px;">
                <div style="font-weight:800;font-size:14px;color:#7a5c00;margin-bottom:6px;">
                    📊 Datos por módulo no cargados aún
                </div>
                <p style="color:#7a5c00;font-size:13px;margin:0 0 12px 0;line-height:1.6;">
                    Los gráficos por módulo requieren una llamada adicional a la API por alumno
                    ({n_s} llamadas · ~{max(1, round(n_s * 0.6 / 60))} min aprox).<br>
                    Mientras se cargan puedes usar el <strong>Tab 1</strong> con el resumen completo
                    y los <strong>Tabs 3 y 4</strong> para drill-down individual sin esperar.
                </p>
            </div>""", unsafe_allow_html=True)
            if st.button("📥 Cargar datos por módulo (todos los alumnos)", key="load_mod_tab3", type="primary"):
                cargar_datos_modulo()

            st.markdown("---")
            st.markdown("**Detalle de lecciones por módulo y alumno (individual — sin espera)**")
            nombres_index_t3 = sorted([s["Nombre"] for s in student_index])
            col_f1b, col_f2b = st.columns(2)
            with col_f1b:
                filtro_mod2b = st.selectbox("Módulo", sorted(modulos_sel), key="mod2b")
            with col_f2b:
                filtro_alb = st.selectbox("Alumno", nombres_index_t3, key="al2b")
            if filtro_alb:
                s_obj = next((s for s in student_index if s["Nombre"] == filtro_alb), None)
                if s_obj:
                    mod_pages_b = modulo_info.get(filtro_mod2b, {}).get("pages", [])
                    lecs_b, _ = get_student_progress(token, subdomain, s_obj["uid"])
                    lecs_map_b = {l.get("page_id"): l for l in (lecs_b or []) if l.get("page_id")}
                    det_rows_b = []
                    if mod_pages_b:
                        for page in mod_pages_b:
                            pid   = page.get("page_id", page.get("id",""))
                            pname = page.get("page_name", page.get("name","Sin nombre"))
                            tipo  = detectar_tipo(page.get("content_type", page.get("type","")), pname)
                            les   = lecs_map_b.get(pid)
                            if les:
                                comp = "Si" if les.get("is_completed") else "No"
                                fecha = ""
                                if les.get("completed_date"):
                                    try: fecha = datetime.fromtimestamp(les["completed_date"]/1000).strftime("%d/%m/%Y")
                                    except: pass
                            else:
                                comp, fecha = "No iniciada", ""
                            det_rows_b.append({"Tipo": tipo, "Leccion": pname,
                                               "Completada": comp, "Fecha Completado": fecha})
                    if det_rows_b:
                        st.caption("✅ Si = completada · ⏳ No = abierta pero pendiente · 🔒 No iniciada = nunca abierta")
                        paginated_dataframe(pd.DataFrame(det_rows_b), "tab3_det_ind")

    with tab4:
        caption("Lecciones <strong>no completadas</strong> por alumno. Distingue entre abiertas pero pendientes (No) y nunca abiertas (No iniciada).")

        nombres_index4 = sorted([s["Nombre"] for s in student_index])
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            filtro_alumno4 = st.selectbox("Alumno", ["Todos"] + nombres_index4, key="pend_al")
        with col_p2:
            filtro_mod4 = st.selectbox("Módulo", ["Todos"] + sorted(modulos_sel), key="pend_mod")

        if filtro_alumno4 == "Todos":
            n_alumnos4 = len(student_index)
            st.markdown(f"""
            <div style="background:#fffbf0;border:1.5px solid #f0d070;border-radius:10px;
                        padding:12px 16px;margin-bottom:12px;display:flex;gap:10px;align-items:flex-start;">
                <span style="font-size:18px;">⏳</span>
                <div>
                    <strong style="color:#7a5c00;font-size:13px;">Carga con tiempo de espera</strong>
                    <p style="color:#7a5c00;font-size:12px;margin:4px 0 0 0;line-height:1.6;">
                        Ver pendientes de todos los alumnos requiere {n_alumnos4} llamadas adicionales a la API
                        (~{max(1, round(n_alumnos4 * 0.6 / 60))} min aprox).
                        Selecciona un alumno específico para carga inmediata.
                    </p>
                </div>
            </div>""", unsafe_allow_html=True)
            cargar_pend = st.button("Cargar pendientes de todos los alumnos", key="load_all_tab4")
        else:
            cargar_pend = True

        if cargar_pend:
            mods_a_cargar4 = modulos_sel if filtro_mod4 == "Todos" else [filtro_mod4]
            alumnos_a_cargar4 = (
                student_index if filtro_alumno4 == "Todos"
                else [s for s in student_index if s["Nombre"] == filtro_alumno4]
            )
            pend_rows = []
            prog_p = st.progress(0)
            for idx, s in enumerate(alumnos_a_cargar4):
                prog_p.progress((idx + 1) / len(alumnos_a_cargar4))
                lecs, _ = get_student_progress(token, subdomain, s["uid"])
                lecs_map = {l.get("page_id"): l for l in (lecs or []) if l.get("page_id")}
                for mn in mods_a_cargar4:
                    mod_pages = modulo_info.get(mn, {}).get("pages", [])
                    if mod_pages:
                        for page in mod_pages:
                            pid    = page.get("page_id", page.get("id",""))
                            pname  = page.get("page_name", page.get("name","Sin nombre"))
                            tipo   = detectar_tipo(page.get("content_type", page.get("type","")), pname)
                            lesson = lecs_map.get(pid)
                            if lesson and lesson.get("is_completed"): continue
                            estado_p = "No" if (lesson and not lesson.get("is_completed")) else "No iniciada"
                            pend_rows.append({"Nombre": s["Nombre"], "Email": s["Email"],
                                              "Modulo": mn, "Tipo": tipo,
                                              "Leccion": pname, "Estado": estado_p})
                    else:
                        for l in (lecs or []):
                            if l.get("module_name") != mn: continue
                            if l.get("is_completed"): continue
                            pname = l.get("page_name","Sin nombre")
                            pend_rows.append({"Nombre": s["Nombre"], "Email": s["Email"],
                                              "Modulo": mn, "Tipo": detectar_tipo("", pname),
                                              "Leccion": pname, "Estado": "No"})
                time.sleep(0.05)
            prog_p.empty()
            if pend_rows:
                df_pend = pd.DataFrame(pend_rows)
                col_fp1, col_fp2 = st.columns(2)
                with col_fp1:
                    estados_disp = sorted(df_pend["Estado"].unique().tolist())
                    filtro_ep = st.multiselect("Estado", options=estados_disp,
                                               default=estados_disp, key="pend_estado")
                with col_fp2:
                    tipos_disp4 = sorted(df_pend["Tipo"].unique().tolist())
                    filtro_tp4 = st.multiselect("Tipo", options=tipos_disp4,
                                                default=tipos_disp4, key="pend_tipo")
                df_pend_fil = df_pend.copy()
                if filtro_ep:  df_pend_fil = df_pend_fil[df_pend_fil["Estado"].isin(filtro_ep)]
                if filtro_tp4: df_pend_fil = df_pend_fil[df_pend_fil["Tipo"].isin(filtro_tp4)]
                st.markdown(f"**{len(df_pend_fil)} lecciones pendientes**")
                st.caption("⏳ No = abierta pero no completada · 🔒 No iniciada = nunca abierta")
                paginated_dataframe(df_pend_fil, "tab4_pend")
            else:
                st.success("¡Todos los alumnos completaron todas las lecciones en esta selección!")

    with tab5:
        caption("Tabla cruzada alumno × módulo. Cada celda = <strong>% de avance en ese módulo específico</strong>.")
        if not tabla_cruzada.empty:
            st.dataframe(tabla_cruzada.set_index("Nombre"), use_container_width=True)
            st.caption("Valores en % completado por módulo.")
        else:
            n_s5 = len(student_index)
            st.markdown(f"""
            <div style="background:#fffbf0;border:1.5px solid #f0d070;border-radius:12px;
                        padding:18px 20px;margin-bottom:16px;">
                <div style="font-weight:800;font-size:14px;color:#7a5c00;margin-bottom:6px;">
                    🗺️ Mapa no disponible aún
                </div>
                <p style="color:#7a5c00;font-size:13px;margin:0 0 12px 0;line-height:1.6;">
                    Requiere los datos por módulo ({n_s5} llamadas · ~{max(1, round(n_s5*0.6/60))} min).
                </p>
            </div>""", unsafe_allow_html=True)
            if st.button("📥 Cargar datos por módulo", key="load_mod_tab5", type="primary"):
                cargar_datos_modulo()

    # EXPORTAR
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='height:2px;background:linear-gradient(90deg,#E8420A,#ff9a7a,transparent);border-radius:2px;margin-bottom:20px;'></div>", unsafe_allow_html=True)

    col_txt, col_btn = st.columns([3, 1])
    with col_txt:
        st.markdown("""
        <p style="font-weight:800;font-size:15px;color:#1a1815;margin-bottom:4px;">Exportar informe</p>
        <p style="color:#8c8880;font-size:13px;margin:0;">Excel con Resumen, Por módulo y Mapa cruzado.</p>
        """, unsafe_allow_html=True)
    with col_btn:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            resumen.to_excel(writer, sheet_name="Resumen", index=False)
            if not df_pivot.empty:
                df_pivot.to_excel(writer, sheet_name="Por modulo", index=False)
            if not tabla_cruzada.empty:
                tabla_cruzada.to_excel(writer, sheet_name="Tabla cruzada", index=False)
        buffer.seek(0)
        st.download_button(
            label="📥 Descargar Excel",
            data=buffer,
            file_name=f"club_analytics_{subdomain}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary"
        )
