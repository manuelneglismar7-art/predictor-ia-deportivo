import os
import json
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from google import genai
from PIL import Image

# --- CONFIGURACIÓN DE ARCHIVOS ---
HISTORIAL_FILE = "historial.csv"

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_key = st.secrets.get("GEMINI_API_KEY", None)
client = genai.Client(api_key=api_key) if api_key else None

# --- MÓDULOS DE ANÁLISIS Y SCRAPING ---
def scrapear_datos_partido(url_partido):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        respuesta = requests.get(url_partido, headers=headers)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, "html.parser")
            
            team_tags = soup.find_all(["h1", "h2", "span"], class_=[
                "team-name", "participant-name", "home-team", "away-team", "team"
            ])
            equipo_local = team_tags[0].get_text(strip=True) if len(team_tags) > 0 else "Equipo Local"
            equipo_visitante = team_tags[1].get_text(strip=True) if len(team_tags) > 1 else "Equipo Visitante"
            
            score_tag = soup.find(["div", "span"], class_=["score", "current-score", "match-score", "result"])
            marcador = score_tag.get_text(strip=True) if score_tag else "0 - 0"

            return {"exito": True, "contenido": {"partido": f"{equipo_local} vs {equipo_visitante}", "marcador": marcador}}
        return {"exito": False, "error": f"Status code: {respuesta.status_code}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["Scraping", "OCR", "Historial"])

# --- PESTAÑA 1: SCRAPING ---
with p_scraping:
    url_input = st.text_input("Pega la URL aquí")
    cuota_manual = st.number_input("Cuota manual", min_value=0.0, value=0.0)
    if st.button("Analizar Enlace", type="primary"):
        with st.spinner("Scrapeando datos del partido..."):
            datos_web = scrapear_datos_partido(url_input)
            if datos_web["exito"]:
                st.success("¡Análisis completo!")
                st.write(datos_web["contenido"])

# --- PESTAÑA 2: OCR REAL CON GEMINI VISION ---
with p_ocr:
    st.markdown("### 📸 Visión Artificial para Flashscore")
    
    if not client:
        st.warning("⚠️ No se detectó la clave de Gemini en Secrets.")
    
    imagen_subida = st.file_uploader("Selecciona una captura de Flashscore...", type=["png", "jpg", "jpeg"])
    
    if imagen_subida is not None:
        img = Image.open(imagen_subida)
        st.image(img, caption="Captura cargada con éxito", use_container_width=True)
        
        if st.button("Procesar Captura con Gemini IA", type="primary", disabled=not client):
            with st.spinner("Gemini analizando la estructura..."):
                try:
                    prompt_instruccion = (
                        "Analiza con precisión esta captura de Flashscore y extrae la información en un formato JSON limpio. "
                        "Estructura esperada:\n"
                        "{\n"
                        '  "partido": "Nombre Local vs Nombre Visitante",\n'
                        '  "marcador": "Goles Local - Goles Visitante",\n'
                        '  "cuotas": {"1": "cuota", "X": "cuota", "2": "cuota"}\n'
                        "}"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[img, prompt_instruccion]
                    )
                    
                    json_texto = response.text.replace("```json", "").replace("```", "").strip()
                    datos_ia = json.loads(json_texto)
                    
                    st.success("¡Captura interpretada correctamente!")
                    st.write(datos_ia)
                    
                except Exception as e:
                    st.error(f"Error al procesar: {str(e)}")
                    
