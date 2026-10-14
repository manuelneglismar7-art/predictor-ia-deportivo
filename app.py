import os
import requests
import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE ARCHIVOS ---
HISTORIAL_FILE = "historial.csv"

# --- MÓDULOS DE ANÁLISIS Y SCRAPING ---
def scrapear_datos_partido(url_partido):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        respuesta = requests.get(url_partido, headers=headers)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, "html.parser")
            return {"exito": True, "contenido": soup}
        return {"exito": False, "error": f"Status code: {respuesta.status_code}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["Scraping", "OCR", "Historial"])

with p_scraping:
    url_input = st.text_input("Pega la URL aquí")
    cuota_manual = st.number_input("Cuota manual")
    
    if st.button("Analizar Enlace", type="primary"):
        with st.spinner("Scrapeando..."):
            datos_web = scrapear_datos_partido(url_input)
            
            if datos_web["exito"]:
                st.success("¡Datos obtenidos correctamente!")
                soup_data = datos_web["contenido"]
                st.write(soup_data.title.text if soup_data.title else "Sin título")
            else:
                st.error(f"Error al scrapear el enlace: {datos_web['error']}")
    
