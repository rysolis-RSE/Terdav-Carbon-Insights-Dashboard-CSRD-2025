import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 0. BASE DE DONNÉES GPS (Mise à jour avec CAP VERT) ---
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
    "Cap Vert": [16.0, -24.0], "Guadeloupe": [16.2, -61.5], "Martinique": [14.6, -61.0]
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

# --- 2. INTERFACE ---
st.sidebar.title("🎛️ Paramètres Stratégiques")
st.sidebar.subheader("💰 Finance & Climat")
prix_tonne = st.sidebar.slider("Prix Tonne CO2 (€)", 0, 200, 80, 10)
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Import Données")
uploaded_file = st.sidebar.file_uploader("Importer votre Excel", type=["xlsx"])

# --- 3. CHARGEMENT ---
df = None
# Données de secours (Demo)
demo_data = {
    'Pays': ['France', 'Italie', 'Vietnam', 'Maroc', 'Islande', 'Japon'],
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
        
        # Filtrer les lignes vides
        df = df[df['Nb_Pax_Total'] > 0].copy()
        
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()
else:
    df = pd.DataFrame(demo_data)

# --- 4. TRAITEMENT ---
if df is not None:
    # Nettoyage des noms de pays
    df['Pays'] = df['Pays'].astype(str).str.strip()

    # Ajout GPS
    def get_coords(pays_name):
        return COORDINATES_DB.get(pays_name, [None, None])
    
    df['coords'] = df['Pays'].apply(get_coords)
    df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)

    # Calculs
    if 'CO2_Total' not in df.columns:
        df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']

    # Simulation
    df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
    df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

    total_co2 = df['CO2_Total_Simule'].sum()
    cout_carbone = (total_co2 / 1000) * prix_tonne

    # --- DASHBOARD ---
    st.title(f"🌍 Pilotage Stratégique & Financier (CSRD)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions", f"{total_co2/1000:,.0f} tCO2e")
    c2.metric("Risque Financier", f"{cout_carbone:,.0f} €", delta=f"{prix_tonne}€/t", delta_color="inverse")
    c3.metric("Scénario Air", f"-{reduction_objectif}%")
    c4.metric("Pays Analysés", f"{len(df)}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🗺️ Cartographie (Heatmap)", "📉 Trajectoire SBTi", "📊 Détails"])

    with tab1:
        st.subheader("Cartographie des Hotspots (Classement)")
        
        # Préparation Carte
        df_map = df.dropna(subset=['lat', 'lon']).groupby('Pays').agg({
            'lat': 'first', 'lon': 'first', 'CO2_Total_Simule': 'sum'
        }).reset_index()

        if not df_map.empty:
            # ICI LE CHANGEMENT MAJEUR POUR LA COULEUR
            fig_map = px.scatter_geo(
                df_map, 
                lat="lat", lon="lon", 
                size="CO2_Total_Simule", # La taille dépend du CO2
                color="CO2_Total_Simule", # La COULEUR aussi (c'est ça qui fait le dégradé)
                hover_name="Pays",
                title="Intensité des émissions par Pays",
                projection="natural earth",
                size_max=60,
                color_continuous_scale="Reds", # Dégradé du rose au rouge sang
                opacity=0.9
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("⚠️ Carte vide. Aucun pays reconnu.")

    with tab2:
        st.subheader("Trajectoire Accord de Paris (SBTi)")
        annees = list(range(2020, 2031))
        # On estime une référence 2020 basée sur le total actuel
        ref_2020 = total_co2 * 1.15
        sbti_target = [ref_2020 * ((1 - 0.042) ** (annee - 2020)) for annee in annees]
        
        fig_traj = go.Figure()
        fig_traj.add_trace(go.Scatter(x=annees, y=sbti_target, mode='lines', name='Objectif 1.5°C', line=dict(color='green', dash='dash')))
        fig_traj.add_trace(go.Scatter(x=[2025], y=[total_co2], mode='markers', name='Bilan Actuel', marker=dict(color='red', size=15)))
        st.plotly_chart(fig_traj, use_container_width=True)

    with tab3:
        # Tableau de classement
        st.subheader("Classement des émissions")
        st.dataframe(
            df[['Pays', 'Nb_Pax_Total', 'CO2_Total_Simule']]
            .sort_values('CO2_Total_Simule', ascending=False)
            .style.format({'CO2_Total_Simule': '{:,.0f}'})
        )

    # Export PDF
    if st.button("Générer PDF Stratégique"):
        pdf_bytes = generate_pdf({'Total_CO2': total_co2, 'Cout_Carbone': cout_carbone})
        if pdf_bytes:
            st.download_button("📥 Rapport PDF", pdf_bytes, "Rapport_CSRD.pdf")
