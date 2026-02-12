import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

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
    "Jordanie": [30.5, 36.2], "Oman": [21.4, 57.0], "Ouzbekistan": [41.3, 64.5],
    "Cap Vert": [16.0, -24.0]
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
        pdf.cell(190, 8, f"Emissions Totales 2025 : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"Risque Financier : {kpi['Cout_Carbone']:,.0f} EUR", ln=True)
        if simulation_text:
            pdf.ln(5)
            pdf.multi_cell(190, 8, simulation_text)
        return pdf.output(dest="S").encode("latin-1")
    except:
        return None

# --- 2. INTERFACE ---
st.sidebar.title("🎛️ Paramètres Stratégiques")
prix_tonne = st.sidebar.slider("Prix Tonne CO2 (€)", 0, 200, 80, 10)
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Importer Excel Mis à Jour", type=["xlsx"])

# --- 3. CHARGEMENT DONNÉES ---
df = None
df_evol = None

# Données démo (Evolution Terdav réelle)
demo_evol = pd.DataFrame({
    'Annee': [2023, 2024, 2025],
    'Total_CO2': [48317903, 52996946, 48053409],
    'Nb_Pax_Total': [33676, 34093, 34479],
    'Intensite': [1434, 1554, 1393] # En kg
})

demo_dest = {
    'Pays': ['France', 'Italie', 'Vietnam', 'Maroc', 'Islande', 'Japon'],
    'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450],
    'CO2_Aerien': [20000, 150000, 1200000, 500000, 450000, 900000],
    'CO2_Terrestre': [150000, 120000, 40000, 80000, 30000, 20000]
}

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        # 1. Lecture Destinations (Onglet 'Destinations')
        if 'Destinations' in xls.sheet_names:
            df = pd.read_excel(xls, 'Destinations')
        else:
            df = pd.read_excel(xls) # Fallback
            
        # 2. Lecture Evolution (Onglet 'Evolution_2023_2025')
        if 'Evolution_2023_2025' in xls.sheet_names:
            df_evol = pd.read_excel(xls, 'Evolution_2023_2025')
        else:
            df_evol = demo_evol # Si l'onglet manque, on met la démo
            
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()
else:
    df = pd.DataFrame(demo_dest)
    df_evol = demo_evol

# --- 4. TRAITEMENT ---
if df is not None:
    # Nettoyage
    df['Pays'] = df['Pays'].astype(str).str.strip()
    df['coords'] = df['Pays'].apply(lambda x: COORDINATES_DB.get(x, [None, None]))
    df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)

    if 'CO2_Total' not in df.columns:
        df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']

    # Simulation 2025
    df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
    df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

    total_co2 = df['CO2_Total_Simule'].sum()
    cout_carbone = (total_co2 / 1000) * prix_tonne

    # --- DASHBOARD ---
    st.title(f"🌍 Pilotage Stratégique & Financier (CSRD)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions 2025", f"{total_co2/1000:,.0f} tCO2e")
    c2.metric("Risque Financier", f"{cout_carbone:,.0f} €", delta=f"{prix_tonne}€/t", delta_color="inverse")
    c3.metric("Scénario Air", f"-{reduction_objectif}%")
    
    # Calcul Variation vs 2024 (si dispo)
    if df_evol is not None:
        co2_2024 = df_evol[df_evol['Annee'] == 2024]['Total_CO2'].values[0]
        var_2025 = ((total_co2 - co2_2024) / co2_2024) * 100
        c4.metric("Evolution vs 2024", f"{var_2025:+.1f}%", delta_color="inverse")
    else:
        c4.metric("Pays Analysés", f"{len(df)}")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📈 Trajectoire 2023-2025", "🗺️ Cartographie", "📊 Détails Pays"])

    with tab1:
        st.subheader("Evolution des Émissions sur 3 ans")
        if df_evol is not None:
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                fig_evol_co2 = px.line(df_evol, x='Annee', y='Total_CO2', markers=True, 
                                       title="Total CO2 (tCO2e)", labels={'Total_CO2': 'Emissions'})
                fig_evol_co2.update_traces(line_color='#E63946', line_width=3)
                st.plotly_chart(fig_evol_co2, use_container_width=True)
                
            with col_g2:
                fig_evol_int = px.line(df_evol, x='Annee', y='Intensite', markers=True, 
                                       title="Intensité Carbone (kgCO2e/pax)", labels={'Intensite': 'kg/pax'})
                fig_evol_int.update_traces(line_color='#2A9D8F', line_width=3)
                st.plotly_chart(fig_evol_int, use_container_width=True)
                
            st.info("💡 Analyse : On observe une baisse significative de l'intensité carbone en 2025 par rapport à 2024, signe que les actions de décarbonation (ou la baisse de l'aérien) fonctionnent.")

    with tab2:
        st.subheader("Cartographie des Hotspots (2025)")
        df_map = df.dropna(subset=['lat', 'lon']).groupby('Pays').agg({
            'lat': 'first', 'lon': 'first', 'CO2_Total_Simule': 'sum'
        }).reset_index()

        if not df_map.empty:
            fig_map = px.scatter_geo(
                df_map, lat="lat", lon="lon", size="CO2_Total_Simule", color="CO2_Total_Simule",
                hover_name="Pays", title="Intensité des émissions", projection="natural earth",
                size_max=50, color_continuous_scale="Reds", opacity=0.9
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Carte vide.")

    with tab3:
        st.dataframe(df.sort_values('CO2_Total_Simule', ascending=False))

    # Export PDF
    if st.button("Générer PDF Stratégique"):
        pdf_bytes = generate_pdf({'Total_CO2': total_co2, 'Cout_Carbone': cout_carbone})
        if pdf_bytes:
            st.download_button("📥 Rapport PDF", pdf_bytes, "Rapport_CSRD.pdf")
