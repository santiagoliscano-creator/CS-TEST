"""
Hotmart Club API · Tester de Diagnóstico
Solo hace llamados a la API y muestra las respuestas crudas.
"""

import streamlit as st
import requests
import json

st.set_page_config(page_title="API Tester · Hotmart Club", page_icon="🔬", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700;800&display=swap');
* { font-family: 'Nunito Sans', sans-serif !important; }
.stApp { background:#faf9f7 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("## 🔬 Hotmart Club API Tester")
st.markdown("Prueba los endpoints de la API con diferentes subdominios y compara las respuestas crudas.")

# ─── CREDENCIALES ──────────────────────────────────────────────────────

with st.container(border=True):
    st.markdown("### Credenciales")
    col1, col2 = st.columns(2)
    with col1:
        basic_token = st.text_input("Basic Token", placeholder="Basic NTM5OWZlMD...", key="basic")
        client_id = st.text_input("Client ID", placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", key="cid")
    with col2:
        client_secret = st.text_input("Client Secret", placeholder="••••••••", type="password", key="secret")
        subdomain = st.text_input("Subdominio", placeholder="mi-curso", key="sub")

    run = st.button("🔬 Ejecutar todos los tests", type="primary", use_container_width=True)


# ─── HELPERS ──────────────────────────────────────────────────────────

def show_response(label, resp):
    """Muestra la respuesta cruda de un request."""
    st.markdown(f"#### {label}")

    col_s, col_h = st.columns([1, 3])
    with col_s:
        color = "🟢" if resp.status_code == 200 else "🟡" if resp.status_code == 204 else "🔴"
        st.markdown(f"**Status:** {color} `{resp.status_code}`")
        st.markdown(f"**Body size:** `{len(resp.text)} chars`")
        st.markdown(f"**Content-Type:** `{resp.headers.get('Content-Type', 'N/A')}`")

    with col_h:
        if resp.text and resp.text.strip():
            try:
                data = resp.json()
                st.markdown(f"**JSON type:** `{type(data).__name__}`")
                if isinstance(data, dict):
                    st.markdown(f"**Top-level keys:** `{list(data.keys())}`")
                    # Mostrar conteos de items en cada key
                    for k, v in data.items():
                        if isinstance(v, list):
                            st.markdown(f"  → `{k}`: lista con **{len(v)}** items")
                            if v and isinstance(v[0], dict):
                                st.markdown(f"    → Primer item keys: `{list(v[0].keys())}`")
                        elif isinstance(v, dict):
                            st.markdown(f"  → `{k}`: dict con keys `{list(v.keys())}`")
                        else:
                            st.markdown(f"  → `{k}`: `{str(v)[:100]}`")
                elif isinstance(data, list):
                    st.markdown(f"**Lista con {len(data)} items**")
                    if data and isinstance(data[0], dict):
                        st.markdown(f"**Primer item keys:** `{list(data[0].keys())}`")
            except:
                pass

    with st.expander("📄 Body crudo completo", expanded=False):
        if resp.text and resp.text.strip():
            try:
                pretty = json.dumps(resp.json(), indent=2, ensure_ascii=False)
                # Limitar a primeros 3000 chars para no sobrecargar
                if len(pretty) > 3000:
                    st.code(pretty[:3000] + "\n\n... (truncado)", language="json")
                else:
                    st.code(pretty, language="json")
            except:
                st.code(resp.text[:3000], language="text")
        else:
            st.code("(VACÍO - 0 bytes)", language="text")

    st.markdown("---")


# ─── TESTS ──────────────────────────────────────────────────────────

if run:
    if not all([basic_token, client_id, client_secret, subdomain]):
        st.error("Completa todos los campos.")
        st.stop()

    # ═══ TEST 0: AUTH ═══
    st.markdown("### 🔑 Test 0: Autenticación")
    auth_url = "https://api-sec-vlc.hotmart.com/security/oauth/token"
    auth_headers = {"Content-Type": "application/x-www-form-urlencoded", "Authorization": basic_token}
    auth_body = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}

    try:
        auth_resp = requests.post(auth_url, headers=auth_headers, data=auth_body, timeout=15)
        show_response("POST /security/oauth/token", auth_resp)

        if auth_resp.status_code != 200:
            st.error("❌ Autenticación fallida. No se pueden ejecutar los demás tests.")
            st.stop()

        token = auth_resp.json().get("access_token")
        if not token:
            st.error("❌ No se obtuvo access_token en la respuesta.")
            st.stop()

        st.success(f"✅ Token obtenido: `{token[:20]}...`")
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        st.stop()

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    # ═══ TEST 1: GET USERS v1 ═══
    st.markdown("### 👥 Test 1: Obtener alumnos (v1)")
    url_v1 = f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}&max_results=10"
    st.code(f"GET {url_v1}", language="text")
    try:
        resp_v1 = requests.get(url_v1, headers=headers, timeout=20)
        show_response(f"v1/users — subdomain={subdomain}", resp_v1)
    except Exception as e:
        st.error(f"Error: {e}")

    # ═══ TEST 2: GET USERS v2 ═══
    st.markdown("### 👥 Test 2: Obtener alumnos (v2 — no documentado)")
    url_v2 = f"https://developers.hotmart.com/club/api/v2/users?subdomain={subdomain}&max_results=10"
    st.code(f"GET {url_v2}", language="text")
    try:
        resp_v2 = requests.get(url_v2, headers=headers, timeout=20)
        show_response(f"v2/users — subdomain={subdomain}", resp_v2)
    except Exception as e:
        st.error(f"Error: {e}")

    # ═══ TEST 3: GET MODULES v1 ═══
    st.markdown("### 📚 Test 3: Obtener módulos (v1)")
    url_mod_v1 = f"https://developers.hotmart.com/club/api/v1/modules?subdomain={subdomain}"
    st.code(f"GET {url_mod_v1}", language="text")
    try:
        resp_mod_v1 = requests.get(url_mod_v1, headers=headers, timeout=15)
        show_response(f"v1/modules — subdomain={subdomain}", resp_mod_v1)
    except Exception as e:
        st.error(f"Error: {e}")

    # ═══ TEST 4: GET MODULES v2 ═══
    st.markdown("### 📚 Test 4: Obtener módulos (v2)")
    url_mod_v2 = f"https://developers.hotmart.com/club/api/v2/modules?subdomain={subdomain}"
    st.code(f"GET {url_mod_v2}", language="text")
    try:
        resp_mod_v2 = requests.get(url_mod_v2, headers=headers, timeout=15)
        show_response(f"v2/modules — subdomain={subdomain}", resp_mod_v2)
    except Exception as e:
        st.error(f"Error: {e}")

    # ═══ TEST 5: Comparación rápida con agencypro si es diferente ═══
    if subdomain.lower() != "agencypro":
        st.markdown("### 🔄 Test 5: Comparación directa con 'agencypro'")
        st.markdown("Mismo token, mismo endpoint, solo cambia el subdominio:")

        url_comp = f"https://developers.hotmart.com/club/api/v1/users?subdomain=agencypro&max_results=5"
        st.code(f"GET {url_comp}", language="text")
        try:
            resp_comp = requests.get(url_comp, headers=headers, timeout=20)
            show_response("v1/users — subdomain=agencypro (comparación)", resp_comp)
        except Exception as e:
            st.error(f"Error: {e}")

    # ═══ TEST 6: Headers completos de la respuesta vacía ═══
    st.markdown("### 🔍 Test 6: Headers completos de la respuesta")
    st.markdown("Todos los headers que devuelve la API para el subdominio que falla:")
    try:
        resp_headers = requests.get(
            f"https://developers.hotmart.com/club/api/v1/users?subdomain={subdomain}&max_results=1",
            headers=headers, timeout=20
        )
        headers_dict = dict(resp_headers.headers)
        st.json(headers_dict)
    except Exception as e:
        st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("""
    <div style="background:#f5f2ee;border-radius:10px;padding:16px;border-left:3px solid #E8420A;">
        <p style="font-size:13px;color:#5c5a56;margin:0;">
            <strong>Cómo usar estos resultados:</strong> Compara el Test 1 entre el subdominio que falla y agencypro (Test 5).
            Si agencypro devuelve items y el otro devuelve body vacío con las mismas credenciales,
            el problema es específico del subdominio en la API de Hotmart — no del código.
            Comparte este screenshot con el equipo de developers de Hotmart para escalar.
        </p>
    </div>
    """, unsafe_allow_html=True)
