# app.py
import streamlit as st
import requests
from urllib.parse import urlencode
from uuid import uuid4
import time

# Configuración de la página
st.set_page_config(
    page_title="Inicio de Sesión - WildPassPro",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS personalizado
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
                    url('https://raw.githubusercontent.com/AndersonP444/PROYECTO-IA-SIC-The-Wild-Project/main/secuencia-vector-diseno-codigo-binario_53876-164420.png');
        background-size: cover;
        background-attachment: fixed;
        animation: fadeIn 1.5s ease-in;
    }
    @keyframes fadeIn {
        0% { opacity: 0; }
        100% { opacity: 1; }
    }
    .stButton > button {
        background-color: #00a8ff;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-size: 1rem;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #0097e6;
        transform: scale(1.05);
    }
    h1, h2, h3 {
        text-shadow: 0 0 12px rgba(0,168,255,0.5);
    }
    .neural-network {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
        margin: 2rem 0;
    }
    .neuron {
        width: 20px;
        height: 20px;
        background-color: #00a8ff;
        border-radius: 50%;
        margin: 0 10px;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.2); opacity: 0.7; }
        100% { transform: scale(1); opacity: 1; }
    }
    .connection {
        width: 50px;
        height: 2px;
        background-color: #00a8ff;
        margin: 0 5px;
        animation: flow 2s infinite;
    }
    @keyframes flow {
        0% { transform: scaleX(1); }
        50% { transform: scaleX(1.2); }
        100% { transform: scaleX(1); }
    }
    .loading-text {
        text-align: center;
        font-size: 1.2rem;
        color: #00a8ff;
        margin-top: 1rem;
        animation: blink 1.5s infinite;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configuración de GitHub OAuth (ACTUALIZAR CON TUS CREDENCIALES REALES)
CLIENT_ID = "TU_CLIENT_ID_REAL"
CLIENT_SECRET = "TU_CLIENT_SECRET_REAL"
REDIRECT_URI = "TU_URL_DE_STREAMLIT"
AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"

# Generar estado único para prevenir CSRF
def generate_state():
    if 'oauth_state' not in st.session_state:
        st.session_state.oauth_state = str(uuid4())
    return st.session_state.oauth_state

# Flujo de autenticación mejorado
def start_github_oauth():
    state = generate_state()
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "user",
        "state": state
    }
    auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"
    st.markdown(f"[Iniciar sesión con GitHub]({auth_url})", unsafe_allow_html=True)

# Manejo de respuesta de OAuth mejorado
def handle_oauth_response():
    query_params = st.query_params
    
    if "code" in query_params and "state" in query_params:
        saved_state = st.session_state.get("oauth_state")
        returned_state = query_params["state"][0]
        
        # Verificar estado para prevenir CSRF
        if saved_state != returned_state:
            st.error("Error de seguridad: Estado no coincide")
            return False
        
        code = query_params["code"][0]
        token = get_access_token(code)
        
        if token:
            user_info = get_user_info(token)
            if user_info:
                st.session_state.user_info = user_info
                st.session_state.token = token
                st.success("¡Autenticación exitosa! Redirigiendo...")
                st.experimental_rerun()
            else:
                st.error("Error al obtener información del usuario")
        else:
            st.error("Error en la autenticación: Token no recibido")
        return True
    return False

# Función para obtener token mejorada
def get_access_token(code):
    try:
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI
        }
        headers = {"Accept": "application/json"}
        response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            st.error(f"Error del servidor: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return None

# Función para obtener información del usuario
def get_user_info(token):
    try:
        headers = {"Authorization": f"token {token}"}
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        st.error(f"Error al obtener información: {str(e)}")
        return None

# Animación de red neuronal
def show_neural_network_animation():
    st.markdown(
        """
        <div class="neural-network">
            <div class="neuron"></div>
            <div class="connection"></div>
            <div class="neuron"></div>
            <div class="connection"></div>
            <div class="neuron"></div>
        </div>
        <div class="loading-text">Entrenando red neuronal...</div>
        """,
        unsafe_allow_html=True
    )

# Interfaz de la página de inicio de sesión
def main():
    st.title("🔐 WildPassPro")
    st.markdown("""
    <div style='text-align: center; padding: 2rem; border-radius: 15px; 
    background: rgba(18, 25, 38, 0.95); margin-top: 5rem;'>
        <h2 style='color: #00a8ff;'>Bienvenido a WildPassPro</h2>
        <p>Por favor, inicia sesión con GitHub para acceder a la plataforma.</p>
    </div>
    """, unsafe_allow_html=True)

    # Mostrar animación de red neuronal
    show_neural_network_animation()

    # Botón de inicio de sesión centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Iniciar sesión con GitHub", key="login_button"):
            start_github_oauth()

    # Manejar la respuesta de OAuth
    if handle_oauth_response():
        st.experimental_rerun()

if __name__ == "__main__":
    main()
