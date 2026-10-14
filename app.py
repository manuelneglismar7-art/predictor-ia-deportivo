import os
import sys

# Forzado absoluto del entorno del servidor a UTF-8 antes de cualquier importación
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["LANG"] = "en_US.UTF-8"

import json
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE ARCHIVOS ---
HISTORIAL_FILE = "historial.csv"

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_key = st.secrets.get("GEMINI_API_KEY", None)
client = genai.Client(api_key=api_key) if api_key else None

def scrapear_datos_partido(url_partido):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        respuesta = requests.get(url_partido, headers=headers)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, "html.parser")
            return {"exito": True, "contenido": {"partido": "Partido", "marcador": "0-0"}}
        return {"exito": False, "error": f"Status: {respuesta.status_code}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["Scraping", "OCR", "Historial"])

with p_scraping:
    url_input = st.text_input("Pega la URL aquí")
    if st.button("Analizar Enlace", type="primary"):
        st.write("Módulo de scraping activo")

with p_ocr:
    st.markdown("### 📸 Visión Artificial para Flashscore")
    
    if not client:
        st.warning("⚠️ Falta la clave de Gemini en Secrets.")
        
    imagen_subida = st.file_uploader("Selecciona una captura de Flashscore...", type=["png", "jpg", "jpeg"])
    
    if imagen_subida is not None:
        bytes_imagen = imagen_subida.getvalue()
        st.image(bytes_imagen, caption="Captura cargada", use_container_width=True)
        
        if st.button("Procesar Captura con Gemini IA", type="primary", disabled=not client):
            with st.spinner("Gemini analizando la estructura..."):
                try:
                    prompt_instruccion = (
                        "Analyze this Flashscore screenshot. Extract all matches and their decimal betting odds. "
                        "Do not use any special characters, accents, or non-ascii symbols in the team names. "
                        "Return ONLY a clean JSON object without markdown formatting. "
                        "Format: {\"partidos_detectados\": [{\"partido\": \"Team A vs Team B\", \"cuotas\": {\"1\": \"1.50\", \"X\": \"3.00\", \"2\": \"4.00\"}}]}"
                    )
                    
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[
                            types.Part.from_bytes(data=bytes_imagen, mime_type=imagen_subida.type),
                            prompt_instruccion
                        ]
                    )
                    
                    # Limpieza radical del texto recibido (Remueve marcas de formato e ignora caracteres rotos)
                    texto_ia = response.text.replace("```json", "").replace("```", "").strip()
                    texto_filtrado = texto_ia.encode("ascii", "ignore").decode("ascii")
                    
                    datos_ia = json.loads(texto_filtrado)
                    st.success("¡Captura interpretada correctamente!")
                    
                    for item in datos_ia.get("partidos_detectados", []):
                        st.markdown(f"### ⚽ {item.get('partido', 'Partido')}")
                        cuotas = item.get("cuotas", {"1": "N/A", "X": "N/A", "2": "N/A"})
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Local (1)", cuotas.get("1", "N/A"))
                        c2.metric("Empate (X)", cuotas.get("X", "N/A"))
                        c3.metric("Visitante (2)", cuotas.get("2", "N/A"))
                        st.markdown("---")
                        
                except Exception as e:
                    # Obliga a mostrar el error en consola de manera limpia sin romper la pantalla
                    error_limpio = str(e).encode("ascii", "ignore").decode("ascii")
                    st.error(f"Error de procesamiento: {error_limpio}")
            
