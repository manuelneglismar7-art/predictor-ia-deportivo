import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from PIL import Image
import json
import pandas as pd
from datetime import datetime
import os

# Configuración de pantalla optimizada para celulares
st.set_page_config(page_title="Analista IA Deportivo", page_icon="⚽", layout="centered")

st.title("⚽ Predictor Deportivo con IA")
st.write("Análisis en tiempo real, Web Scraping y Algoritmo de Valor.")

# --- CONFIGURACIÓN DE SEGURIDAD (STREAMLIT SECRETS) ---
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Introduce tu Gemini API Key (Modo Local):", type="password")

if not api_key:
    st.info("📌 Configura tu 'GEMINI_API_KEY' en los Secrets de Streamlit o en la barra lateral para continuar.")
    st.stop()

# Inicializar cliente de Gemini
client = genai.Client(api_key=api_key)
HISTORIAL_FILE = "historial_predicciones.csv"

# --- MÓDULO: REGISTRO HISTÓRICO INMODIFICABLE ---
def guardar_en_historial(equipos, cuota, prob_ia, valor, exito):
    nuevo_registro = {
        "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Evento": equipos,
        "Cuota Casa": cuota,
        "Probabilidad IA": f"{prob_ia * 100:.1f}%",
        "Ventaja Encontrada": f"{valor * 100:.1f}%",
        "¿Tiene Valor?": "SÍ" if exito else "NO"
    }
    df_nuevo = pd.DataFrame([nuevo_registro])
    if not os.path.isfile(HISTORIAL_FILE):
        df_nuevo.to_csv(HISTORIAL_FILE, index=False)
    else:
        df_nuevo.to_csv(HISTORIAL_FILE, mode='a', header=False, index=False)

# --- MÓDULOS DE ANÁLISIS Y SCRAPING ---
def scrapear_datos_partido(url_partido):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        respuesta = requests.get(url_partido, headers=headers, timeout=10)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            return {"exito": True, "contexto_html": soup.get_text()[:4000], "titulo": soup.find('title').text if soup.find('title') else "Partido"}
        return {"exito": False, "error": f"Error {respuesta.status_code}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

def analizar_con_gemini(texto_datos, imagen_captura=None):
    prompt_sistema = """Actúa como un Analista Predictivo Cuantitativo de Elite. Calcula la Probabilidad Real Implícita (PRI). 
    Compárala con la de la Casa (PCA = 1/Cuota). Valor si PRI > PCA. Responde ÚNICAMENTE con este JSON:
    {
      "equipos": "Local vs Visitante",
      "analisis_contextual": "Clima, bajas, calendario.",
      "cuota_detectada": 2.00,
      "probabilidad_ia_ganar": 0.60,
      "alerta_valor": true,
      "porcentaje_valor": 0.20
    }"""
    config = types.GenerateContentConfig(system_instruction=prompt_sistema, temperature=0.2, response_mime_type="application/json")
    contenidos = [f"Datos:\n{texto_datos}"]
    if imagen_captura: contenidos.append(imagen_captura)
    try:
        respuesta = client.models.generate_content(model='gemini-1.5-flash', contents=contenidos, config=config)
        return json.loads(respuesta.text)
    except: return None

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["🌐 URL", "📸 Captura / Cámara", "📊 Historial / Auditoría"])

with p_scraping:
    url_input = st.text_input("Pega la URL del partido:")
    cuota_manual = st.number_input("Cuota actual:", min_value=1.01, value=2.00)
    if st.button("Analizar Enlace", type="primary"):
        with st.spinner("Scrapeando..."):
            datos_web = scrapear_datos_partido(url_input)
            if datos_web["exito"]:
                res = analizar_con_gemini(f"{datos_web['contexto_html']}\nCuota: {cuota_manual}")
                if res:
                    st.metric(res.get("equipos"), f"IA: {res.get('probabilidad_ia_ganar')*100:.0f}%")
                    st.write(res.get("analisis_contextual"))
                    guardar_en_historial(res.get("equipos"), cuota_manual, res.get("probabilidad_ia_ganar"), res.get("porcentaje_valor"), res.get("alerta_valor"))
                    if res.get("alerta_valor"): st.balloons(); st.success("🚨 ALTO VALOR")

with p_ocr:
    archivo_imagen = st.file_uploader("Sube o toma una foto", type=["jpg", "jpeg", "png"])
    if archivo_imagen:
        img = Image.open(archivo_imagen)
        st.image(img, use_container_width=True)
        if st.button("Auditar con OCR", type="primary"):
            with st.spinner("Leyendo imagen..."):
                res = analizar_con_gemini("Analiza la cuota e identifica el partido en la imagen.", imagen_captura=img)
                if res:
                    st.subheader(res.get("equipos"))
                    st.write(f"Cuota OCR: {res.get('cuota_detectada')}")
                    st.write(res.get("analisis_contextual"))
                    guardar_en_historial(res.get("equipos"), res.get("cuota_detectada"), res.get("probabilidad_ia_ganar"), res.get("porcentaje_valor"), res.get("alerta_valor"))
                    if res.get("alerta_valor"): st.balloons(); st.success("🔥 APUESTA CON VALOR")

with p_historial:
    st.subheader("Auditoría Pública de Predicciones")
    if os.path.isfile(HISTORIAL_FILE):
        df_historial = pd.read_csv(HISTORIAL_FILE)
        st.dataframe(df_historial, use_container_width=True)
        st.download_button("Descargar Historial CSV", data=df_historial.to_csv(index=False), file_name="registro_ia.csv", mime="text/csv")
    else:
        st.info("Aún no hay predicciones registradas en esta sesión.")
