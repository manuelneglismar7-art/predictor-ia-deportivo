import streamlit as st
from google import genai

# 1. Leer de forma segura la API Key desde los Secrets de Streamlit
api_key_gemini = st.secrets["GEMINI_API_KEY"]

# 2. Inicializar el cliente pasándole la clave configurada
client = genai.Client(api_key=api_key_gemini)

st.title("Predictor Deportivo con IA")

# Aquí continúa el resto del código que creaste para subir la captura
# y el botón "Procesar Captura con Gemini IA"
