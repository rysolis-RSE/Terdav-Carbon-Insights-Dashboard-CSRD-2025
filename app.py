import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# ==============================================================================
# 1. DONNÉES FICTIVES (POUR LA DÉMO UNIQUEMENT)
# ==============================================================================

# Entreprise fictive "TravelCorp" - Evolution inventée
DEMO_HISTORY = pd.DataFrame({
    'Annee': [2023, 2024, 2025],
    'Total_CO2': [50000000, 51500000, 49000000], # Chiffres ronds fictifs
    'Nb_Pax': [30000, 31000, 30500]
})

# Destinations fictives (Répartition au hasard)
DEMO_DESTINATIONS = pd.DataFrame({
    'Pays': [
        'Australie', 'Mexique', 'Thailande', 'Japon', 'Etats-Unis', 
        'Perou', 'Indonesie', 'Afrique du Sud', 'Vietnam', 'Costa Rica',
        'France', 'Italie', 'Espagne', 'Grece', 'Portugal'
    ],
    'Nb_Pax_Total': [
        500, 800, 1200, 600, 400, 
        700, 900, 300, 1000, 450, 
        5000, 3000, 2500, 1500, 1200
    ],
    # CO2 inventé : Loin = Beaucoup, Près = Peu
    'CO2_Total': [
        4500000, 3200000, 3000000, 2800000, 2500000, 
        2400000, 2200000, 1800000, 1700000, 1500000, 
        500000, 800000, 700000, 900000, 600000
    ]
})
# On sépare arbitrairement Aérien/Terrestre pour la démo
DEMO_DESTINATIONS['CO2_Aerien'] = DEMO_DESTINATIONS['CO2_Total'] * 0.85
DEMO_DESTINATIONS['CO2_Terrestre'] = DEMO_DESTINATIONS['CO2_Total'] * 0.15


# Base GPS (Publique)
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
    "Jordanie": [30.5, 36.2], "Oman": [21.4, 57.0], "Ouzbekistan": [41.3, 64.5],
    "Cap Vert": [16.0, -24.0]
}

# ==============================================================================
# 2. FONCTIONS
# ==============================================================================
def generate_pdf(kpi, simulation_text=""):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Rapport Strategique Carbone (DEMO)", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, f"Emissions Totales 2025 : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"Risque Financier : {kpi['Cout_Carbone']:,.0f} EUR", ln=True)
        if simulation_text:
            pdf.ln(5)
            pdf.multi_cell(190, 8, simulation_text)
        return pdf.output(dest="S").encode("latin-1")
    except:
        return None

# ==============================================================================
# 3. INTERFACE
# ==============================================================================
st.sidebar.title("🎛️ Paramètres Stratégiques")
prix_tonne = st.sidebar.slider("Prix Tonne CO2 (€)", 0, 200, 80, 10)
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
st.sidebar.warning("⚠️ **MODE DÉMO ACTIF**")
st.sidebar.caption("Données fictives générées pour la présentation.")
# Le bouton upload reste là si tu veux mettre tes vraies données en privé plus tard
uploaded_file = st.sidebar.file_uploader("Importer des données réelles (Optionnel)", type=["xlsx"])

# CHOIX DES DONNÉES
df_evol = DEMO_HISTORY.copy()
df_dest = DEMO_DESTINATIONS.copy()

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        if 'Destinations' in xls.sheet_names:
            df_dest = pd.read_excel(xls, 'Destinations')
        if 'Evolution' in xls.sheet_names:
            df_evol = pd.read_excel(xls, 'Evolution')
        st.sidebar.success("✅ Données réelles chargées !")
    except:
        st.sidebar.error("Erreur de lecture fichier")

# 4. PREPARATION
# Ajout GPS
df_dest['coords'] = df_dest['Pays'].apply(lambda x: COORDINATES_DB.get(str(x).strip(), [None, None]))
df_dest[['lat', 'lon']] = pd.DataFrame(df_dest['coords'].tolist(), index=df_dest.index)

# Simulation sur Destinations
df_dest['CO2_Aerien_Simule'] = df_dest['CO2_Aerien'] * (1 - reduction_objectif/100)
df_dest['CO2_Total_Simule'] = df_dest['CO2_Aerien_Simule'] + df_dest['CO2_Terrestre']

# Chiffres Clés (Basés sur le total 2025 fictif)
total_2025_reel = df_evol[df_evol['Annee'] == 2025]['Total_CO2'].values[0]
total_simule = total_2025_reel * (1 - (reduction_objectif/100 * 0.75)) # Estimation impact
cout_carbone = (total_simule / 1000) * prix_tonne

# ==============================================================================
# 5. DASHBOARD
# ==============================================================================
st.title("🌍 Pilotage Stratégique & Financier (DÉMO)")

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total CO2 2025", f"{total_2025_reel/1000:,.0f} tCO2e")
c2.metric("Risque Financier", f"{cout_carbone:,.0f} €", delta=f"{prix_tonne}€/t", delta_color="inverse")
c3.metric("Obj. Réduction CSRD", "-1.5% / an")
# Evolution Réelle 24-25
val_24 = df_evol[df_evol['Annee']==2024]['Total_CO2'].values[0]
val_25 = df_evol[df_evol['Annee']==2025]['Total_CO2'].values[0]
evo = ((val_25 - val_24) / val_24) * 100
c4.metric("Evolution 24-25", f"{evo:+.1f}%", delta_color="inverse")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📉 Trajectoire & Objectifs", "🗺️ Carte Hotspots", "📊 Détails Pays"])

with tab1:
    st.subheader("Performance vs Objectif CSRD (-1.5%)")
    
    # Construction de la courbe cible (-1.5% par an depuis 2023)
    ref_2023 = df_evol[df_evol['Annee']==2023]['Total_CO2'].values[0]
    annees_proj = [2023, 2024, 2025, 2026, 2027]
    target_values = [ref_2023 * ((1 - 0.015) ** (yr - 2023)) for yr in annees_proj]
    
    fig_traj = go.Figure()
    
    # 1. Courbe Réelle
    fig_traj.add_trace(go.Scatter(
        x=df_evol['Annee'], y=df_evol['Total_CO2'],
        mode='lines+markers', name='Emissions (Données Démo)',
        line=dict(color='#E63946', width=4), marker=dict(size=12)
    ))
    
    # 2. Courbe Cible CSRD
    fig_traj.add_trace(go.Scatter(
        x=annees_proj, y=target_values,
        mode='lines', name='Cible CSRD (-1.5%/an)',
        line=dict(color='purple', dash='dot', width=2)
    ))

    # 3. Point Simulé
    if reduction_objectif > 0:
        fig_traj.add_trace(go.Scatter(
            x=[2025], y=[total_simule],
            mode='markers', name=f'Simulation (-{reduction_objectif}%)',
            marker=dict(color='#2A9D8F', size=15, symbol='star')
        ))

    fig_traj.update_layout(title="Trajectoire vs Cible -1.5%", yaxis_title="kg CO2e")
    st.plotly_chart(fig_traj, use_container_width=True)

with tab2:
    st.subheader("Cartographie (Données Fictives)")
    
    df_map = df_dest.dropna(subset=['lat', 'lon'])
    
    if not df_map.empty:
        fig_map = px.scatter_geo(
            df_map, 
            lat="lat", lon="lon", 
            size="CO2_Total_Simule", 
            color="CO2_Total_Simule",
            hover_name="Pays", 
            projection="natural earth",
            size_max=50, 
            color_continuous_scale="Reds", 
            opacity=0.9,
            title="Intensité Carbone par Destination"
        )
        fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Erreur carte")

with tab3:
    st.dataframe(df_dest[['Pays', 'Nb_Pax_Total', 'CO2_Total_Simule']].sort_values('CO2_Total_Simule', ascending=False))

# Export PDF
if st.button("📄 Télécharger Rapport (Démo)"):
    pdf_bytes = generate_pdf({'Total_CO2': total_simule, 'Cout_Carbone': cout_carbone}, "CECI EST UN RAPPORT DE DEMONSTRATION")
    if pdf_bytes:
        st.download_button("📥 Rapport PDF", pdf_bytes, "Rapport_Demo.pdf")
