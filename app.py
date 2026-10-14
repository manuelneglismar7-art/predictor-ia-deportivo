import os
import json
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
from google import genai
from google.genai import types

# --- CONFIGURACIÓN DE LA API DE GEMINI ---
api_key = st.secrets.get("GEMINI_API_KEY", None)
client = genai.Client(api_key=api_key) if api_key else None

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["Scraping", "OCR", "Historial"])

with p_scraping:
    st.markdown("### Módulo de Scraping Activo")
    url_input = st.text_input("Pega la URL aquí")

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
                    
                    # Limpieza básica de formato markdown si la IA lo incluye por error
                    texto_ia = response.text.replace("```json", "").replace("```", "").strip()
                    datos_ia = json.loads(texto_ia)
                    
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
                    # Solución radical: Mostramos un mensaje genérico seguro sin procesar el texto del error
                    st.error("Ocurrió un problema en la comunicación con la Inteligencia Artificial.")
                    st.info("Por favor, asegúrate de que tu GEMINI_API_KEY en Secrets esté bien escrita.")
                    
