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
            
            # --- MOTOR DE EXTRACCIÓN COMÚN EXTRA ---
            # 1. Intentar extraer nombres de equipos (Búsqueda por etiquetas comunes de títulos)
            team_tags = soup.find_all(["h1", "h2", "span"], class_=[
                "team-name", "participant-name", "home-team", "away-team", "team"
            ])
            equipo_local = team_tags[0].get_text(strip=True) if len(team_tags) > 0 else "Equipo Local"
            equipo_visitante = team_tags[1].get_text(strip=True) if len(team_tags) > 1 else "Equipo Visitante"
            
            if equipo_local == "Equipo Local" and soup.title:
                # Alternativa si están en el título de la página (ej: "Real Madrid vs Barcelona Live Score")
                title_text = soup.title.text
                if "vs" in title_text:
                    partes = title_text.split("vs")
                    equipo_local = partes[0].strip()
                    equipo_visitante = partes[1].split("-")[0].strip()

            # 2. Intentar extraer el marcador / goles
            score_tag = soup.find(["div", "span"], class_=["score", "current-score", "match-score", "result"])
            marcador = score_tag.get_text(strip=True) if score_tag else "0 - 0"

            # 3. Intentar extraer Cuotas (Estructura típica 1 X 2 de tablas de apuestas)
            cuotas = {"1": "N/A", "X": "N/A", "2": "N/A"}
            odds_elements = soup.find_all(["span", "td", "button"], class_=["odds", "odd", "bets-value", "kx"])
            if len(odds_elements) >= 3:
                cuotas["1"] = odds_elements[0].get_text(strip=True)
                cuotas["X"] = odds_elements[1].get_text(strip=True)
                cuotas["2"] = odds_elements[2].get_text(strip=True)

            # 4. Intentar extraer Estadísticas comunes (Posesión, Tiros, Faltas)
            estadisticas = {}
            stat_rows = soup.find_all(["tr", "div"], class_=["stat-row", "statistic-data", "item"])
            for row in stat_rows:
                texto = row.get_text(" ", strip=True)
                if text:
                    # Guardar filas tipo: "Posesión 55% 45%"
                    partes_stat = texto.split()
                    if len(partes_stat) >= 2:
                        nombre_stat = "".join([c for c in partes_stat if c.isalpha()])
                        estadisticas[nombre_stat if nombre_stat else "Dato"] = texto

            # Compilar toda la información limpia en el diccionario de retorno
            datos_extraidos = {
                "titulo_pagina": soup.title.text if soup.title else "Sin Título",
                "partido": f"{equipo_local} vs {equipo_visitante}",
                "marcador": marcador,
                "cuotas_1X2": cuotas,
                "estadisticas_comunes": estadisticas if estadisticas else {"Info": "Disponibles en entorno dinámico JS"}
            }

            return {"exito": True, "contenido": datos_extraidos}
        return {"exito": False, "error": f"Status code: {respuesta.status_code}"}
    except Exception as e:
        return {"exito": False, "error": str(e)}

# --- INTERFAZ GRÁFICA MÓVIL (PESTAÑAS) ---
p_scraping, p_ocr, p_historial = st.tabs(["Scraping", "OCR", "Historial"])

with p_scraping:
    url_input = st.text_input("Pega la URL aquí")
    cuota_manual = st.number_input("Cuota manual", min_value=0.0, value=0.0)
    
    if st.button("Analizar Enlace", type="primary"):
        with st.spinner("Scrapeando datos del partido..."):
            datos_web = scrapear_datos_partido(url_input)
            
            if datos_web["exito"]:
                res = datos_web["contenido"]
                st.success(f"¡Análisis completo para: {res['partido']}!")
                
                # Despliegue visual ordenado en la App
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="⚽ Marcador en Vivo / Resultado", value=res["marcador"])
                with col2:
                    st.metric(label="📌 Evento", value=res["partido"])
                
                st.markdown("### 📊 Cuotas de Apuesta Detectadas (1 X 2)")
                c1, c2, c3 = st.columns(3)
                c1.metric("Gana Local (1)", res["cuotas_1X2"]["1"])
                c2.metric("Empate (X)", res["cuotas_1X2"]["X"])
                c3.metric("Gana Visitante (2)", res["cuotas_1X2"]["2"])
                
                st.markdown("### 📈 Estadísticas Adicionales")
                st.json(res["estadisticas_comunes"])
                
            else:
                st.error(f"Error al scrapear el enlace: {datos_web['error']}")
