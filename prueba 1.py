import streamlit as st
import hashlib
import pandas as pd
import numpy as np
import re
import requests
import joblib
import tensorflow as tf
import secrets
import string
import os
import io
import time
import json
import nltk
from nltk.stem import PorterStemmer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from cryptography.fernet import Fernet
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.feature_extraction.text import CountVectorizer
from tensorflow.keras.optimizers import Adam
import openai
from urllib.parse import urlencode
from oauthlib.oauth2 import WebApplicationClient

# Configuración de la página para eliminar "Manage app" y "Share"
st.set_page_config(
    page_title="WildPassPro",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items=None  # Desactiva el menú de la esquina superior derecha
)

# CSS personalizado para ocultar elementos no deseados
st.markdown(
    """
    <style>
    /* Ocultar la barra de herramientas */
    .stDeployButton, .stActionButton, .stToolbar {
        display: none !important;
    }
    
    /* Ocultar el logo de GitHub si está en el sidebar */
    .sidebar .stImage {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configuración de Groq
GROQ_API_KEY = "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"
MODEL_NAME = "llama3-70b-8192"

client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=GROQ_API_KEY
)

# ========== CONFIGURACIÓN AUTENTICACIÓN GITHUB ==========
# Configuración de GitHub OAuth
CLIENT_ID = "Ov23liuP3aNdQcqR96Vi"
CLIENT_SECRET = "ed282057cd1a02d51e39d7a8b3064d7075e029fa"
REDIRECT_URI = "https://pruebas-444.streamlit.app/callback"
AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"

client = WebApplicationClient(CLIENT_ID)

def get_github_login_url():
    base_url = "https://github.com/login/oauth/authorize"
    return f"{base_url}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=user:email"

def get_access_token(code):
    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

def get_user_info(access_token):
    headers = {"Authorization": f"token {access_token}"}
    response = requests.get("https://api.github.com/user", headers=headers)
    return response.json()
# ========== CONFIGURACIONES INICIALES ==========
nltk.download('punkt')

# Configuración de seguridad
MASTER_PASSWORD = "WildPassPro2024!"
CLAVE_CIFRADO = Fernet.generate_key() if not os.path.exists("clave.key") else open("clave.key", "rb").read()
fernet = Fernet(CLAVE_CIFRADO)

# ========== FUNCIONES DE SEGURIDAD ==========
def generar_clave_cifrado():
    if not os.path.exists("clave.key"):
        clave = Fernet.generate_key()
        with open("clave.key", "wb") as archivo_clave:
            archivo_clave.write(clave)
    return open("clave.key", "rb").read()

CLAVE_CIFRADO = generar_clave_cifrado()
fernet = Fernet(CLAVE_CIFRADO)

def cifrar_archivo(ruta_archivo):
    with open(ruta_archivo, "rb") as archivo:
        datos = archivo.read()
    datos_cifrados = fernet.encrypt(datos)
    with open(ruta_archivo + ".encrypted", "wb") as archivo_cifrado:
        archivo_cifrado.write(datos_cifrados)
    os.remove(ruta_archivo)
    return f"{ruta_archivo}.encrypted"

def descifrar_archivo(ruta_archivo):
    with open(ruta_archivo, "rb") as archivo:
        datos_cifrados = archivo.read()
    datos_descifrados = fernet.decrypt(datos_cifrados)
    ruta_original = ruta_archivo.replace(".encrypted", "")
    with open(ruta_original, "wb") as archivo_descifrado:
        archivo_descifrado.write(datos_descifrados)
    return ruta_original

# ========== EFECTO MAQUINA DE ESCRIBIR ==========
def typewriter_effect(text):
    placeholder = st.empty()
    displayed_text = ""
    for char in text:
        displayed_text += char
        placeholder.markdown(f'<div class="chat-message">{displayed_text}</div>', unsafe_allow_html=True)
        time.sleep(0.02)
    return displayed_text

# ========== CHATBOT ==========
try:
    with open('intents.json') as file:
        intents = json.load(file)
except FileNotFoundError:
    try:
        url = "https://raw.githubusercontent.com/AndersonP444/pruebas/main/intents.json"
        response = requests.get(url)
        response.raise_for_status()
        intents = response.json()
        with open('intents.json', 'w') as file:
            json.dump(intents, file)
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        intents = {"intents": []}

# Preparar datos del chatbot
patterns = []
tags = []
all_words = []
stemmer = PorterStemmer()

for intent in intents['intents']:
    for pattern in intent['patterns']:
        patterns.append(pattern)
        tags.append(intent['tag'])
    words = nltk.word_tokenize(pattern)
    words = [stemmer.stem(w.lower()) for w in words if w.isalnum()]
    all_words.extend(words)

all_words = sorted(list(set(all_words)))
encoder = LabelEncoder()
y_train = encoder.fit_transform(tags)

# Crear Bag of Words
vectorizer = CountVectorizer(vocabulary=all_words)
X_train = vectorizer.transform(patterns).toarray()

# Cargar modelo de chatbot
if os.path.exists('chatbot_model.h5'):
    os.remove('chatbot_model.h5')

@st.cache_resource
def cargar_modelo_chatbot():
    model = Sequential([
        Dense(128, input_shape=(X_train.shape[1],), activation='relu'),
        Dropout(0.3),
        Dense(64, activation='relu'),
        Dense(len(set(tags)), activation='softmax')
    ])
    model.compile(loss='sparse_categorical_crossentropy', 
                 optimizer=Adam(0.001), 
                 metrics=['accuracy'])
    model.fit(X_train, y_train, epochs=150, batch_size=5, verbose=0)
    model.save('chatbot_model.h5')
    return model

modelo_chatbot = cargar_modelo_chatbot()

# Función de respuesta del chatbot
def respuesta_chatbot(texto_usuario):
    try:
        palabras = nltk.word_tokenize(texto_usuario)
        palabras = [stemmer.stem(w.lower()) for w in palabras if w.isalnum()]
        bow = np.zeros(len(all_words))
        for palabra in palabras:
            if palabra in all_words:
                bow[all_words.index(palabra)] = 1
        if len(bow) != modelo_chatbot.input_shape[1]:
            return f"Error: Dimensión inválida ({len(bow)} vs {modelo_chatbot.input_shape[1]})"
        prediccion = modelo_chatbot.predict(np.array([bow]), verbose=0)[0]
        tag = encoder.inverse_transform([np.argmax(prediccion)])[0]
        for intent in intents['intents']:
            if intent['tag'] == tag:
                return np.random.choice(intent['responses'])
        return "No entendí. ¿Podrías reformularlo?"
    except Exception as e:
        return f"Error: {str(e)}"

# ========== FUNCIONES PRINCIPALES ==========
def generar_contraseña_segura(longitud=16):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def generar_llave_acceso():
    return secrets.token_urlsafe(32)

def cargar_contraseñas_debiles(url):
    respuesta = requests.get(url)
    return set(linea.strip().lower() for linea in respuesta.text.splitlines() if linea.strip())

WEAK_PASSWORDS = cargar_contraseñas_debiles("https://github.com/AndersonP444/PROYECTO-IA-SIC-The-Wild-Project/raw/main/rockyou.txt")

def detectar_debilidades(contraseña):
    debilidades = []
    contraseña_lower = contraseña.lower()
    if contraseña_lower in WEAK_PASSWORDS:
        debilidades.append("❌ Está en la lista rockyou.txt")
    if contraseña.islower():
        debilidades.append("❌ Solo minúsculas")
    if contraseña.isupper():
        debilidades.append("❌ Solo mayúsculas")
    if not any(c.isdigit() for c in contraseña):
        debilidades.append("❌ Sin números")
    if not any(c in "!@#$%^&*()" for c in contraseña):
        debilidades.append("❌ Sin símbolos")
    if len(contraseña) < 12:
        debilidades.append(f"❌ Longitud insuficiente ({len(contraseña)}/12)")
    if contraseña_lower in ["diego", "juan", "maria", "pedro", "media"]:
        debilidades.append("❌ Contiene un nombre común")
    if "123" in contraseña or "abc" in contraseña_lower or "809" in contraseña:
        debilidades.append("❌ Contiene una secuencia simple")
    return debilidades

# ========== FUNCIONES DE LA RED NEURONAL ==========
def crear_modelo():
    model = Sequential([
        Dense(64, activation='relu', input_shape=(8,)),
        BatchNormalization(),
        Dropout(0.3),
        Dense(32, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(16, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        Dense(3, activation='softmax')
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def entrenar_modelo(model, X, y):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    early_stop = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_val, y_val), callbacks=[early_stop], verbose=0)
    model.save("password_strength_model.h5")
    return model, history

def predecir_fortaleza(model, password):
    features = np.array([
        len(password),
        sum(1 for c in password if c.islower()),
        sum(1 for c in password if c.isupper()),
        sum(1 for c in password if c.isdigit()),
        sum(1 for c in password if c in "!@#$%^&*()"),
        int(password.lower() in ["maria", "juan", "pedro", "diego", "media"]),
        int("123" in password or "abc" in password.lower() or "809" in password),
        len(set(password))
    ]).reshape(1, 8)
    prediction = model.predict(features, verbose=0)
    return np.argmax(prediction)

def explicar_fortaleza(password):
    explicaciones = []
    if len(password) >= 12:
        explicaciones.append("✅ Longitud adecuada (más de 12 caracteres)")
    else:
        explicaciones.append("❌ Longitud insuficiente (menos de 12 caracteres)")
    if any(c.isupper() for c in password):
        explicaciones.append("✅ Contiene mayúsculas")
    if any(c.isdigit() for c in password):
        explicaciones.append("✅ Contiene números")
    if any(c in "!@#$%^&*()" for c in password):
        explicaciones.append("✅ Contiene símbolos especiales")
    if password.lower() in ["maria", "juan", "pedro", "diego", "media"]:
        explicaciones.append("❌ Contiene un nombre común")
    if "123" in password or "abc" in password.lower() or "809" in password:
        explicaciones.append("❌ Contiene una secuencia simple")
    if len(set(password)) < len(password) * 0.5:
        explicaciones.append("❌ Baja variabilidad de caracteres")
    return explicaciones

# ========== PREPROCESAR DATASET ==========
def preprocesar_dataset(df):
    X = np.array([[
        len(row["password"]),
        sum(1 for c in row["password"] if c.islower()),
        sum(1 for c in row["password"] if c.isupper()),
        sum(1 for c in row["password"] if c.isdigit()),
        sum(1 for c in row["password"] if c in "!@#$%^&*()"),
        int(row["password"].lower() in ["maria", "juan", "pedro", "diego", "media"]),
        int("123" in row["password"] or "abc" in row["password"].lower() or "809" in row["password"]),
        len(set(row["password"]))
    ] for _, row in df.iterrows()])
    y = df["strength"].values
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    return X, y, label_encoder

# ========== GESTOR DE CONTRASEÑAS ==========
def guardar_contraseña(sitio, usuario, contraseña):
    if not os.path.exists("passwords.json.encrypted"):
        with open("passwords.json", "w") as f:
            json.dump([], f)
        cifrar_archivo("passwords.json")
    descifrar_archivo("passwords.json.encrypted")
    with open("passwords.json", "r") as f:
        datos = json.load(f)
    datos.append({"sitio": sitio, "usuario": usuario, "contraseña": fernet.encrypt(contraseña.encode()).decode()})
    with open("passwords.json", "w") as f:
        json.dump(datos, f)
    cifrar_archivo("passwords.json")

def obtener_contraseñas():
    if not os.path.exists("passwords.json.encrypted"):
        return []
    descifrar_archivo("passwords.json.encrypted")
    with open("passwords.json", "r") as f:
        datos = json.load(f)
    cifrar_archivo("passwords.json")
    for item in datos:
        item["contraseña"] = fernet.decrypt(item["contraseña"].encode()).decode()
    return datos

# ========== ESCANER DE VULNERABILIDADES ==========
def escanear_vulnerabilidades(url):
    try:
        response = requests.get(url)
        content = response.text
        vulnerabilidades = []
        if re.search(r"<script>.*</script>", content, re.IGNORECASE):
            vulnerabilidades.append("XSS (Cross-Site Scripting)")
        if re.search(r"select.*from|insert into|update.*set|delete from", content, re.IGNORECASE):
            vulnerabilidades.append("SQL Injection")
        if not re.search(r"csrf_token", content, re.IGNORECASE):
            vulnerabilidades.append("Posible CSRF (Cross-Site Request Forgery)")
        return vulnerabilidades
    except Exception as e:
        return [f"Error al escanear: {str(e)}"]

def explicar_vulnerabilidades(vulnerabilidades):
    explicaciones = {
        "XSS (Cross-Site Scripting)": [
            "✅ **Qué es:** Ataque donde se inyectan scripts maliciosos en páginas web",
            "🔒 **Solución:** Sanitizar entradas de usuario y usar Content Security Policy (CSP)"
        ],
        "SQL Injection": [
            "✅ **Qué es:** Inyección de código SQL para manipular bases de datos",
            "🔒 **Solución:** Usar consultas parametrizadas y ORMs"
        ],
        "CSRF (Cross-Site Request Forgery)": [
            "✅ **Qué es:** Ataque que engaña al usuario para ejecutar acciones no deseadas",
            "🔒 **Solución:** Implementar tokens CSRF y validar origen de las peticiones"
        ]
    }
    resultado = "## Explicación de Vulnerabilidades\n\n"
    for vuln in vulnerabilidades:
        if vuln in explicaciones:
            resultado += f"### {vuln}\n" + "\n".join(explicaciones[vuln]) + "\n\n"
        else:
            resultado += f"### {vuln}\n⚠️ Información no disponible\n\n"
    return resultado

# ========== FUNCIÓN PARA DESCARGAR CONTRASEÑAS EN TXT ==========
def descargar_contraseñas_txt(contraseñas):
    contenido = "Contraseñas generadas:\n\n"
    for idx, pwd in enumerate(contraseñas, start=1):
        contenido += f"{idx}. {pwd}\n"
    buffer = io.StringIO()
    buffer.write(contenido)
    buffer.seek(0)
    return buffer

# ========== VERIFICADOR DE FUGAS DE DATOS ==========
def verificar_fuga_datos(password):
    try:
        sha1_password = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
        if response.status_code == 200:
            for line in response.text.splitlines():
                if line.startswith(suffix):
                    count = int(line.split(":")[1])
                    return f"⚠️ **Advertencia:** Esta contraseña ha sido expuesta en {count} fugas de datos."
            return "✅ **Segura:** Esta contraseña no ha sido expuesta en fugas de datos conocidas."
        else:
            return "🔴 **Error:** No se pudo verificar la contraseña. Inténtalo de nuevo más tarde."
    except Exception as e:
        return f"🔴 **Error:** {str(e)}"

# ========== FUNCIÓN PARA ANALIZAR CONTRASEÑA CON GROQ ==========
def analizar_contraseña_con_groq(password):
    # Crear el mensaje para Groq
    mensaje = f"""
    Analiza la siguiente contraseña y proporciona una explicación detallada de por qué es débil o fuerte:
    Contraseña: {password}

    Si es débil, enumera las vulnerabilidades críticas, compara con patrones comunes y proporciona recomendaciones personalizadas.
    Si es fuerte, explica qué características la hacen segura y por qué es resistente a ataques.
    """

    # Enviar la solicitud a Groq
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": "Eres un experto en seguridad de contraseñas."},
            {"role": "user", "content": mensaje}
        ]
    )

    # Obtener la respuesta de Groq
    explicacion = response.choices[0].message.content
    return explicacion

# ========== INTERFAZ PRINCIPAL ==========
def main():
    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
                        url('https://raw.githubusercontent.com/AndersonP444/PROYECTO-IA-SIC-The-Wild-Project/main/secuencia-vector-diseno-codigo-binario_53876-164420.png');
            background-size: cover;
            background-attachment: fixed;
            animation: fadeIn 1.5s ease-in;
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        .stExpander > div {{
            background: rgba(18, 25, 38, 0.95) !important;
            backdrop-filter: blur(12px);
            border-radius: 15px;
            border: 1px solid rgba(0, 168, 255, 0.3);
            transition: all 0.3s ease;
        }}
        .stExpander > div:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0,150,255,0.2);
        }}
        .stButton > button {{
            transition: all 0.3s !important;
            border: 1px solid #00a8ff !important;
        }}
        .stButton > button:hover {{
            transform: scale(1.03);
            background: rgba(0,168,255,0.15) !important;
        }}
        .chat-message {{
            animation: slideIn 0.4s ease-out;
        }}
        @keyframes slideIn {{
            0% {{ transform: translateX(15px); opacity: 0; }}
            100% {{ transform: translateX(0); opacity: 1; }}
        }}
        h1, h2, h3 {{
            text-shadow: 0 0 12px rgba(0,168,255,0.5);
        }}
        .stProgress > div > div {{
            background: linear-gradient(90deg, #00a8ff, #00ff88);
            border-radius: 3px;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Verificar autenticación primero
    # Verificar autenticación
    query_params = st.query_params  # Reemplazar experimental_get_query_params
    
    if 'code' in query_params:
        try:
            code = query_params['code'][0]  # Acceder al primer elemento de la lista
            access_token = get_access_token(code)
            user_info = get_user_info(access_token)
            
            if 'login' in user_info:
                st.session_state.auth_state = True
                st.session_state.user = user_info['login']
                st.query_params.clear()  # Reemplazar experimental_set_query_params  # Limpiar parámetros después de autenticar
                st.rerun()
            else:
                st.error("Error en la autenticación. Intenta nuevamente.")
                
        except Exception as e:
            st.error(f"Error crítico: {str(e)}")

    if 'auth_state' not in st.session_state or not st.session_state.auth_state:
        st.title("Bienvenido a WildPassPro")
        st.markdown("Debes iniciar sesión con GitHub para continuar")
        login_url = get_github_login_url()
        st.markdown(f"[Iniciar sesión con GitHub]({login_url})")
        return

    st.markdown(f"""
    <style>
        .stApp {{
            background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)),
                        url('https://raw.githubusercontent.com/AndersonP444/PROYECTO-IA-SIC-The-Wild-Project/main/secuencia-vector-diseno-codigo-binario_53876-164420.png');
            background-size: cover;
            background-attachment: fixed;
            animation: fadeIn 1.5s ease-in;
        }}
        
        .chat-message {{
            animation: slideIn 0.4s ease-out;
        }}
    </style>
    """, unsafe_allow_html=True)

    # Si está autenticado, mostrar el contenido principal

    st.title(f"🔐 WildPassPro - Suite de Seguridad - Bienvenido {st.session_state.user}")
    
    dataset_url = "https://github.com/AndersonP444/PROYECTO-IA-SIC-The-Wild-Project/raw/main/password_dataset_final.csv"
    df = pd.read_csv(dataset_url)

    X, y, label_encoder = preprocesar_dataset(df)

    if not os.path.exists("password_strength_model.h5"):
        with st.spinner("Entrenando la red neuronal..."):
            model = crear_modelo()
            model, history = entrenar_modelo(model, X, y)
            st.success("Modelo entrenado exitosamente!")
    else:
        model = tf.keras.models.load_model("password_strength_model.h5")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🛠️ Generadores", "🔒 Bóveda", "🔍 Analizador", "💬 Chatbot", "🌐 Escáner Web", "🔐 Verificador de Fugas"])

    with tab1:
        st.subheader("🛠️ Generadores")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🔑 Generar Contraseña Segura")
            password_length = st.slider("Longitud de la contraseña", 12, 32, 16)
            if st.button("Generar Contraseña"):
                secure_password = generar_contraseña_segura(password_length)
                st.success(f"**Contraseña generada:** `{secure_password}`")
                buffer = descargar_contraseñas_txt([secure_password])
                st.download_button(
                    label="📥 Descargar Contraseña",
                    data=buffer.getvalue(),
                    file_name="contraseña_generada.txt",
                    mime="text/plain"
                )
        with col2:
            st.markdown("### 🔑 Generar Llave de Acceso")
            if st.button("Generar Llave de Acceso"):
                access_key = generar_llave_acceso()
                st.success(f"**Llave de acceso generada:** `{access_key}`")
                buffer = descargar_contraseñas_txt([access_key])
                st.download_button(
                    label="📥 Descargar Llave de Acceso",
                    data=buffer.getvalue(),
                    file_name="llave_acceso_generada.txt",
                    mime="text/plain"
                )
    
    with tab2:
        st.subheader("🔒 Bóveda de Contraseñas")
        with st.expander("➕ Añadir Nueva Contraseña"):
            sitio = st.text_input("Sitio Web/App")
            usuario = st.text_input("Usuario")
            contraseña = st.text_input("Contraseña", type="password")
            if st.button("Guardar Contraseña"):
                if sitio and usuario and contraseña:
                    guardar_contraseña(sitio, usuario, contraseña)
                    st.success("Contraseña guardada con éxito!")
                else:
                    st.error("Por favor, completa todos los campos.")
        with st.expander("🔍 Ver Contraseñas"):
            contraseñas = obtener_contraseñas()
            if contraseñas:
                for idx, item in enumerate(contraseñas):
                    with st.container():
                        st.write(f"**Sitio:** {item['sitio']}")
                        st.write(f"**Usuario:** {item['usuario']}")
                        st.write(f"**Contraseña:** `{item['contraseña']}`")
                        if st.button(f"Eliminar {item['sitio']}", key=f"del_{idx}"):
                            contraseñas.pop(idx)
                            with open("passwords.json", "w") as f:
                                json.dump(contraseñas, f)
                            cifrar_archivo("passwords.json")
                            st.rerun()
            else:
                st.info("No hay contraseñas guardadas aún.")
    
    with tab3:
        st.subheader("🔍 Analizar Contraseña")
        password = st.text_input("Ingresa tu contraseña:", type="password", key="pwd_input")
        
        if password:
            weaknesses = detectar_debilidades(password)
            final_strength = "DÉBIL 🔴" if weaknesses else "FUERTE 🟢"
            
            strength_prediction = predecir_fortaleza(model, password)
            strength_labels = ["DÉBIL 🔴", "MEDIA 🟡", "FUERTE 🟢"]
            neural_strength = strength_labels[strength_prediction]
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.subheader("📋 Clasificación Final")
                st.markdown(f"## {final_strength}")
                if weaknesses:
                    st.error("### Razones de debilidad:")
                    for weakness in weaknesses:
                        st.write(weakness)
                else:
                    st.success("### Cumple con todos los criterios")
                
                st.subheader("🧠 Predicción de Red Neuronal")
                st.markdown(f"## {neural_strength}")
                
                if strength_prediction == 2:
                    st.success("### Explicación de la fortaleza:")
                    explicaciones = explicar_fortaleza(password)
                    for explicacion in explicaciones:
                        st.write(explicacion)
            
            with col2:
                st.subheader("📝 Análisis Detallado")
                if st.button("Obtener Análisis Detallado"):
                    with st.spinner("Analizando contraseña..."):
                        explicacion = analizar_contraseña_con_groq(password)
                        st.markdown(f"### Explicación:\n{explicacion}")
    
    with tab4:
        st.subheader("💬 Asistente de Seguridad")
        if "historial_chat" not in st.session_state:
            st.session_state.historial_chat = []
        for mensaje in st.session_state.historial_chat:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])
        if prompt := st.chat_input("Escribe tu pregunta sobre seguridad..."):
            respuesta = respuesta_chatbot(prompt)
            if "||contraseña||" in respuesta:
                nueva_contraseña = generar_contraseña_segura()
                respuesta = respuesta.replace("||contraseña||", f"`{nueva_contraseña}`")
            st.session_state.historial_chat.append({"role": "user", "content": prompt})
            st.session_state.historial_chat.append({"role": "assistant", "content": respuesta})
            st.rerun()
    
    with tab5:
        st.subheader("🌐 Escáner Web")
        url = st.text_input("Ingresa la URL del sitio web a escanear:")
        if url:
            with st.spinner("Escaneando..."):
                try:
                    response = requests.get(url)
                    content = response.text
                    vulnerabilidades = []
                    if re.search(r"<script>.*</script>", content, re.IGNORECASE):
                        vulnerabilidades.append("XSS (Cross-Site Scripting)")
                    if re.search(r"select.*from|insert into|update.*set|delete from", content, re.IGNORECASE):
                        vulnerabilidades.append("SQL Injection")
                    if not re.search(r"csrf_token", content, re.IGNORECASE):
                        vulnerabilidades.append("Posible CSRF (Cross-Site Request Forgery)")
                    if vulnerabilidades:
                        st.error("⚠️ Vulnerabilidades encontradas:")
                        for vuln in vulnerabilidades:
                            st.write(f"- {vuln}")
                        st.markdown(explicar_vulnerabilidades(vulnerabilidades))
                    else:
                        st.success("✅ No se encontraron vulnerabilidades comunes")
                except Exception as e:
                    st.error(f"Error al escanear: {str(e)}")
    
    with tab6:
        st.subheader("🔐 Verificador de Fugas de Datos")
        password = st.text_input("Ingresa tu contraseña para verificar si ha sido comprometida:", type="password")
        if st.button("Verificar"):
            if password:
                resultado = verificar_fuga_datos(password)
                st.markdown(resultado)
            else:
                st.error("Por favor, ingresa una contraseña para verificar.")

if __name__ == "__main__":
    main()
