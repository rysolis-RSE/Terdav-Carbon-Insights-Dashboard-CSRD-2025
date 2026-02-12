import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io
import numpy as np

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 0. BASE DE DONNÉES GPS ---
COORDINATES_DB = {
    "France": [46.6, 1.8], "Italie": [41.8, 12.5], "Espagne": [40.4, -3.7], 
    "Portugal": [39.3, -8.2], "Grece": [39.0, 21.8], "Maroc": [31.7, -7.0],
    "Tunisie": [33.8, 9.5], "Egypte": [26.8, 30.8], "Turquie": [38.9, 35.2],
    "Islande": [64.9, -19.0], "Norvege": [60.4, 8.4], "Suede": [60.1, 18.6],
    "Finlande": [61.9, 25.7], "Royaume-Uni": [55.3, -3.4], "Irlande": [53.4, -8.2],
    "Etats-Unis": [37.0, -95.7], "Canada": [56.1, -106.3], "Mexique": [23.6, -102.5],
    "Perou": [-9.1, -75.0], "Bresil": [-14.2, -51.9], "Argentine": [-38.4, -63.6],
    "Chili": [-35.6, -71.5], "Colombie": [4.5, -74.2], "Costa Rica": [9.7, -83.7],
    "Tanzanie": [-6.3, 34.8], "Afrique du Sud": [-30.5, 22.9], "Namibie": [-22.9, 18.4],
    "Kenya": [-0.0, 37.9], "Madagascar": [-18.7, 46.8], "Reunion": [-21.1, 55.5],
    "Japon": [36.2, 138.2], "Vietnam": [14.0, 108.2], "Thailande": [15.8, 100.9],
    "Inde": [20.5, 78.9], "Nepal": [28.3, 84.1], "Chine": [35.8, 104.1],
    "Indonesie": [-0.7, 113.9], "Australie": [-25.2, 133.7], "Nouvelle-Zelande": [-40.9, 174.8],
    "Jordanie": [30.5, 36.2], "Oman": [21.4, 57.0], "Ouzbekistan": [41.3, 64.5]
}

# --- 1. FONCTION PDF ---
def generate_pdf(kpi, simulation_text=""):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Rapport Strategique Carbone (CSRD)", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, f"Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"Risque Financier : {kpi['Cout_Carbone']:,.0f} EUR", ln=True)
        if simulation_text:
            pdf.ln(5)
            pdf.multi_cell(190, 8, simulation_text)
        return pdf.output(dest="S").encode("latin-1")
    except:
        return None

# --- 2. INTERFACE & PARAMÈTRES FINANCIERS ---
st.sidebar.title("🎛️ Paramètres Stratégiques")

# NOUVEAU : Simulation Financière
st.sidebar.subheader("💰 Taxe Carbone Interne")
prix_tonne = st.sidebar.slider("Prix de la tonne CO2 (€)", 0, 200, 80, 10, help="Pour évaluer le risque financier selon ESRS E1-9")

# Simulation Physique
st.sidebar.subheader("✈️ Transition Physique")
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Importer Excel", type=["xlsx"])

# Template simplifié
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Pays', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, sheet_name='Destinations', index=False)
st.sidebar.download_button("📥 Template Simplifié", buffer.getvalue(), "Template_Simple.xlsx")

# --- 3. LOGIQUE & CALCULS ---
df = None
# Données démo par défaut
demo_data = {
    'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon'],
    'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450],
    'CO2_Aerien': [20000, 150000, 1200000, 500000, 450000, 900000],
    'CO2_Terrestre': [150000, 120000, 40000, 80000, 30000, 20000]
}

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        if 'Destinations' in xls.sheet_names:
            df = pd.read_excel(xls, 'Destinations')
        else:
            df = pd.read_excel(xls)
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        st.stop()
else:
    df = pd.DataFrame(demo_data)

# --- 4. TRAITEMENT ---
if df is not None:
    # 1. Coordonnées
    def get_coords(pays_name):
        return COORDINATES_DB.get(str(pays_name).strip(), [None, None])
    df['coords'] = df['Pays'].apply(get_coords)
    df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)
    
    # 2. Simulation Physique
    df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
    df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

    # 3. KPIs
    total_co2 = df['CO2_Total_Simule'].sum()
    nb_pax = df['Nb_Pax_Total'].sum()
    intensite = total_co2 / nb_pax if nb_pax > 0 else 0
    
    # NOUVEAU : Calcul Financier
    cout_carbone = (total_co2 / 1000) * prix_tonne

    # --- 5. DASHBOARD ---
    st.title(f"🌍 Pilotage Stratégique & Financier (CSRD)")
    
    # KPIs avec le financier
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions", f"{total_co2/1000:,.0f} tCO2e")
    c2.metric("Intensité", f"{intensite:.0f} kg/pax")
    c3.metric("Scénario Air", f"-{reduction_objectif}%")
    # La métrique qui tue :
    c4.metric("Risque Financier", f"{cout_carbone:,.0f} €", delta=f"Prix: {prix_tonne}€/t", delta_color="off")
    
    st.markdown("---")
    
    # ONGLETS : On ajoute la trajectoire
    tab1, tab2, tab3 = st.tabs(["📉 Trajectoire SBTi", "🗺️ Cartographie", "📊 Analyse Pays"])
    
    with tab1:
        st.subheader("Trajectoire de Décarbonation (Accord de Paris 1.5°C)")
        st.caption("Comparaison entre vos émissions actuelles et la courbe idéale SBTi (-4.2% par an).")
        
        # Simulation d'une courbe SBTi basée sur le volume actuel
        annees = list(range(2020, 2031))
        # On imagine que 2020 était l'année de référence (un peu plus haute)
        ref_2020 = total_co2 * 1.15 
        
        # Calcul de la courbe SBTi (-4.2% par an depuis 2020)
        sbti_target = [ref_2020 * ((1 - 0.042) ** (annee - 2020)) for annee in annees]
        
        # Donnée actuelle (On place le point actuel en 2025)
        current_year = 2025
        
        fig_traj = go.Figure()
        # Ligne Cible
        fig_traj.add_trace(go.Scatter(x=annees, y=sbti_target, mode='lines', name='Objectif SBTi (1.5°C)', line=dict(color='green', dash='dash')))
        # Point Actuel
        fig_traj.add_trace(go.Scatter(x=[current_year], y=[total_co2], mode='markers', name='Votre Bilan 2025', marker=dict(color='red', size=15)))
        
        # Zone de dépassement ou succès
        delta_sbti = total_co2 - sbti_target[current_year - 2020]
        annotation_text = "⚠️ Retard sur l'objectif" if delta_sbti > 0 else "✅ Alignement OK"
        
        fig_traj.add_annotation(x=current_year, y=total_co2, text=annotation_text, showarrow=True, arrowhead=1)
        fig_traj.update_layout(title="Positionnement vs Trajectoire 2030", yaxis_title="Emissions (kg CO2e)")
        st.plotly_chart(fig_traj, use_container_width=True)

    with tab2:
        # Code Carte (Optimisé)
        df_map = df.dropna(subset=['lat', 'lon']).groupby('Pays').agg({
            'lat': 'first', 'lon': 'first', 'CO2_Total_Simule': 'sum'
        }).reset_index()
        
        if not df_map.empty:
            fig_map = px.scatter_geo(
                df_map, lat="lat", lon="lon", size="CO2_Total_Simule", hover_name="Pays",
                title=f"Carte des risques (Agrégée)", projection="natural earth", size_max=40
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Pas de données géographiques valides.")

    with tab3:
        top10 = df.sort_values("CO2_Total_Simule", ascending=False).head(10)
        fig_bar = px.bar(top10, x='Pays', y='CO2_Total_Simule', title="Top 10 Emetteurs", color='CO2_Total_Simule')
        st.plotly_chart(fig_bar, use_container_width=True)

    # Export PDF avec données financières
    if st.button("Générer Rapport Stratégique (PDF)"):
        pdf_bytes = generate_pdf({'Total_CO2': total_co2, 'Cout_Carbone': cout_carbone}, f"Scenario: -{reduction_objectif}% Air | Taxe: {prix_tonne} EUR/t")
        if pdf_bytes:
            st.download_button("📥 Télécharger PDF", pdf_bytes, "Rapport_SBTi.pdf")
