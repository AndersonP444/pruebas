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
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from tensorflow.keras.optimizers import Adam

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
# Cargar intenciones # Cambia la ruta por la ubicación real de tu archivo
# Intenta cargar localmente primero
try:
    with open('intents.json') as file:
        intents = json.load(file)
except FileNotFoundError:
    # Si falla, descarga desde GitHub
    try:
        url = "https://raw.githubusercontent.com/AndersonP444/pruebas/main/intents.json"
        response = requests.get(url)
        response.raise_for_status()
        intents = response.json()
        
        # Guarda localmente para próximas ejecuciones
        with open('intents.json', 'w') as file:
            json.dump(intents, file)
            
    except Exception as e:
        st.error(f"Error crítico: {str(e)}")
        intents = {"intents": []}  # Evita que la app se caiga

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
# Elimina el modelo existente para forzar reentrenamiento
if os.path.exists('chatbot_model.h5'):
    os.remove('chatbot_model.h5')

@st.cache_resource
def cargar_modelo_chatbot():
    model = Sequential([
        Dense(128, input_shape=(X_train.shape[1],), activation='relu'),  # Ajuste automático
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

# ========== FUNCIÓN CORREGIDA DEL CHATBOT ==========
# Función de respuesta del chatbot
def respuesta_chatbot(texto_usuario):
    try:
        # Preprocesamiento
        # Preprocesamiento consistente
        palabras = nltk.word_tokenize(texto_usuario)
        palabras = [stemmer.stem(w.lower()) for w in palabras if w.isalnum()]
        
        # Crear BoW
        bow = np.zeros(len(all_words))
        for palabra in palabras:
            if palabra in all_words:
                bow[all_words.index(palabra)] = 1
                
        # Validación crítica
        if len(bow) != modelo_chatbot.input_shape[1]:
            return f"Error: Dimensión inválida ({len(bow)} vs {modelo_chatbot.input_shape[1]})"

        # Predicción
        prediccion = modelo_chatbot.predict(np.array([bow]), verbose=0)[0]
        tag = encoder.inverse_transform([np.argmax(prediccion)])[0]
        
        # Respuesta
        for intent in intents['intents']:
            if intent['tag'] == tag:
                return np.random.choice(intent['responses'])
        
        return "No entendí. ¿Podrías reformularlo?"
    
    except Exception as e:
        return f"Error: {str(e)}"
    
    # Crear BoW
    #bow = np.zeros(len(all_words))
    #for palabra in palabras:
    #    if palabra in all_words:
    #        bow[all_words.index(palabra)] = 1
    
    # Predecir
    #prediccion = modelo_chatbot.predict(np.array([bow]), verbose=0)[0]
    #tag = encoder.inverse_transform([np.argmax(prediccion)])[0]
    
    # Obtener respuesta
    #for intent in intents['intents']:
    #    if intent['tag'] == tag:
    #        return np.random.choice(intent['responses'])
    
    #return "Lo siento, no entendí. ¿Podrías reformularlo?"

# ========== FUNCIONES PRINCIPALES ==========
def generar_contraseña_segura(longitud=16):
    caracteres = string.ascii_letters + string.digits + "!@#$%^&*()"
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))

def generar_llave_acceso():  # Nombre en español
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
        Dense(64, activation='relu', input_shape=(8,)),  # Aumentamos el número de neuronas
        BatchNormalization(),
        Dropout(0.3),
        
        Dense(32, activation='relu'),  # Aumentamos el número de neuronas
        BatchNormalization(),
        Dropout(0.3),
        
        Dense(16, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),
        
        Dense(3, activation='softmax')  # 3 clases: débil, media, fuerte
    ])
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    return model

def entrenar_modelo(model, X, y):
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    early_stop = EarlyStopping(
        monitor='val_loss',
        patience=5,  # Aumentamos la paciencia para permitir más iteraciones
        restore_best_weights=True
    )
    
    history = model.fit(
        X_train, y_train,
        epochs=100,  # Aumentamos el número de épocas
        batch_size=32,
        validation_data=(X_val, y_val),
        callbacks=[early_stop],
        verbose=0
    )
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

    st.title("🔐 WildPassPro - Suite de Seguridad")
    
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
                secure_password = generar_contraseña_segura(password_length)  # <-- Nombre en español
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
            weaknesses = detect_weakness(password)
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
    
    with tab4:
        st.subheader("💬 Asistente de Seguridad")
        
        if "historial_chat" not in st.session_state:
            st.session_state.historial_chat = []
        
        # Mostrar historial
        for mensaje in st.session_state.historial_chat:
            with st.chat_message(mensaje["role"]):
                st.markdown(mensaje["content"])
        
        # Manejar nueva entrada
        if prompt := st.chat_input("Escribe tu pregunta sobre seguridad..."):
            # Respuesta del chatbot
            respuesta = respuesta_chatbot(prompt)
            
            # Reemplazar marcador de contraseña si es necesario
            if "||contraseña||" in respuesta:
                nueva_contraseña = generar_contraseña_segura()  # <-- Nombre en español
                respuesta = respuesta.replace("||contraseña||", f"`{nueva_contraseña}`")
            
            # Actualizar historial
            st.session_state.historial_chat.append({"role": "user", "content": prompt})
            st.session_state.historial_chat.append({"role": "assistant", "content": respuesta})
            
            # Forzar rerun para mostrar actualización
            st.rerun()
    
    with tab5:
        st.subheader("🌐 Escáner de Vulnerabilidades Web")
        
        url = st.text_input("Ingresa la URL del sitio web a escanear:")
        if url:
            with st.spinner("Escaneando..."):
                vulnerabilidades = escanear_vulnerabilidades(url)
                if vulnerabilidades:
                    st.error("⚠️ Vulnerabilidades encontradas:")
                    for vuln in vulnerabilidades:
                        st.write(f"- {vuln}")
                    
                    st.subheader("📚 Explicación de las Vulnerabilidades")
                    explicacion = groq_explicacion_vulnerabilidades(vulnerabilidades)
                    st.markdown(explicacion)
                else:
                    st.success("✅ No se encontraron vulnerabilidades comunes.")
    
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
