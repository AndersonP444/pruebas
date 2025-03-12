# app.py
import streamlit as st
import requests
from urllib.parse import urlencode
from uuid import uuid4
import time
import random

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
    .training-panel {
        background: rgba(18, 25, 38, 0.95);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 2rem 0;
        font-family: monospace;
        white-space: pre;
        color: #00a8ff;
        border: 1px solid rgba(0, 168, 255, 0.3);
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
CLIENT_ID = "Ov23liuP3aNdQcqR96Vi"
CLIENT_SECRET = "1d0f05497fb5e04455ace743591a3ab18fab2801"
REDIRECT_URI = "https://wildpasspro8080.streamlit.app"
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

# Función para crear el panel de entrenamiento
def create_training_panel(epoch, accuracy, feature_importances):
    # Asegurarse de que feature_importances tenga la estructura correcta
    if not isinstance(feature_importances, (list, tuple)) or len(feature_importances) != 5:
        raise ValueError("feature_importances debe ser una lista o tupla de 5 elementos.")
    
    # Crear las barras de características
    feature_bars = "\n".join([
        f"Longitud   {'▮' * int(fi[0]*40)} {fi[0]*100:.1f}%",
        f"Mayúsculas {'▮' * int(fi[1]*40)} {fi[1]*100:.1f}%",
        f"Dígitos    {'▮' * int(fi[2]*40)} {fi[2]*100:.1f}%",
        f"Símbolos   {'▮' * int(fi[3]*40)} {fi[3]*100:.1f}%",
        f"Unicidad   {'▮' * int(fi[4]*40)} {fi[4]*100:.1f}%"
    ])
    
    # Crear el panel
    panel = f"""
    ╭────────────────── WildPassPro - Entrenamiento de IA ──────────────────╮
    │                                                                        │
    │ Progreso del Entrenamiento:                                            │
    │ Árboles creados: {epoch}/100                                           │
    │ Precisión actual: {accuracy:.1%}                                      │
    │                                                                        │
    │ Características más importantes:                                       │
    {feature_bars}
    │                                                                        │
    │ Creando protección inteligente...                                      │
    ╰────────────────────────────────────────────────────────────────────────╯
    """
    return panel

# Función para mostrar la animación de entrenamiento
def show_training_animation():
    placeholder = st.empty()
    for epoch in range(1, 101):
        # Simular progreso
        accuracy = min(epoch / 100 + random.uniform(-0.05, 0.05), 1.0)
        
        # Simular feature importances (asegurarse de que sea una lista de 5 elementos)
        feature_importances = [
            (random.uniform(0.7, 0.9),  # Longitud
             random.uniform(0.5, 0.7),  # Mayúsculas
             random.uniform(0.6, 0.8),  # Dígitos
             random.uniform(0.4, 0.6),  # Símbolos
             random.uniform(0.3, 0.5))  # Unicidad
        ]
        
        # Crear el panel de entrenamiento
        panel = create_training_panel(epoch, accuracy, feature_importances)
        
        # Mostrar el panel en el placeholder
        with placeholder:
            st.markdown(f"```\n{panel}\n```", unsafe_allow_html=True)
        
        # Simular tiempo de entrenamiento
        time.sleep(0.1)

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

    # Mostrar animación de entrenamiento
    if st.button("Iniciar sesión con GitHub", key="login_button"):
        with st.spinner("Entrenando modelo de IA..."):
            show_training_animation()
        start_github_oauth()

    # Manejar la respuesta de OAuth
    if handle_oauth_response():
        st.experimental_rerun()

if __name__ == "__main__":
    main()
