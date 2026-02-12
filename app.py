import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 0. DONNÉES HISTORIQUES TERDAV (Corrigées & Intégrées) ---
# J'ai extrait ces valeurs directement de ton fichier pour éviter les bugs de lecture
TERDAV_HISTORY = pd.DataFrame({
    'Annee': [2023, 2024, 2025],
    'Total_CO2': [48317903, 52996946, 48053409], # En kg
    'Nb_Pax': [33676, 34093, 34479],
    'Intensite': [1434, 1554, 1393]
})

# --- 1. BASE DE DONNÉES GPS ---
COORDINATES_DB = {
    "France": [46.6, 1.8], "Italie": [41.8, 12.5], "Espagne": [40.4, -3.7], 
    "Portugal": [39.3, -8.2], "Grece": [39.0, 21.8], "Maroc": [31.7, -7.0],
    "Tunisie": [33.8, 9.5], "Egypte": [26.8, 30.8], "Turquie": [38.9, 35.2],
    "Islande": [64.9, -19.0], "Norvege": [60.4, 8.4], "Suede": [60.1, 18.6],
    "Finlande": [61.9, 25.7], "Royaume-Uni": [55.3, -3.4], "Irlande": [53.4, -8.2],
    "Etats-Unis": [37.0, -95.7], "Canada": [56.1, -106.3], "Mexique": [23.6, -102.5],
    "Perou": [-9.1, -75.0], "Bresil": [-14.2, -51.9], "Argentine": [-38.4, -63.6],
    "Chili": [-35.6, -7
