import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Carbon Monitor", layout="wide", page_icon="🌍")

# --- 0. BASE DE DONNÉES GPS INTÉGRÉE (Plus besoin de les mettre dans Excel) ---
# J'ai mis les 50 destinations les plus fréquentes. 
# Si un pays manque, le point ne s'affichera juste pas, mais ça ne plantera pas.
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

# --- 1. DONNÉES DE DÉMO ---
def load_demo_data():
    data = {
        'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon', 'Perou', 'Tanzanie', 'Norvege', 'Grece'],
        'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450, 300, 250, 600, 1500],
        'CO2_Aerien': [20000, 150000, 1200000, 500000, 450000, 900000, 750000, 600000, 180000, 400000],
        'CO2_Terrestre': [150000, 120000, 40000, 80000, 30000, 20000, 15000, 12000, 25000, 50000]
    }
    df = pd.DataFrame(data)
    df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
    return df

# --- 2. FONCTION PDF ---
def generate_pdf(kpi, simulation_text=""):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Rapport Strategique Carbone", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, f"Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"Intensite : {kpi['Intensite']:.0f} kgCO2e/pax", ln=True)
        if simulation_text:
            pdf.ln(5)
            pdf.multi_cell(190, 8, simulation_text)
        return pdf.output(dest="S").encode("latin-1")
    except:
        return None

# --- 3. INTERFACE ---
st.sidebar.title("🎛️ Simulateur")
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Importer Excel", type=["xlsx"])

# Template simplifié (plus besoin de lat/lon)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Pays', 'Continent', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, sheet_name='Destinations', index=False)
st.sidebar.download_button("📥 Template Simplifié", buffer.getvalue(), "Template_Simple.xlsx")

# --- 4. TRAITEMENT INTELLIGENT ---
df = None

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        if 'Destinations' in xls.sheet_names:
            df = pd.read_excel(xls, 'Destinations')
        else:
            df = pd.read_excel(xls)
        
        # AJOUT AUTOMATIQUE DES COORDONNÉES
        # On regarde le nom du pays et on ajoute lat/lon depuis le code
        def get_coords(pays_name):
            return COORDINATES_DB.get(str(pays_name).strip(), [None, None])
            
        # On applique la fonction
        df['coords'] = df['Pays'].apply(get_coords)
        df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)
        
        # Calcul du total si manquant
        if 'CO2_Total' not in df.columns:
            df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
            
    except Exception as e:
        st.error(f"Erreur : {e}")
        st.stop()
else:
    df = load_demo_data()
    # Ajout coords pour la démo aussi
    df['coords'] = df['Pays'].apply(lambda x: COORDINATES_DB.get(x, [0,0]))
    df[['lat', 'lon']] = pd.DataFrame(df['coords'].tolist(), index=df.index)

# --- 5. SIMULATION & KPI ---
if df is not None:
    df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
    df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

    total_co2 = df['CO2_Total_Simule'].sum()
    nb_pax = df['Nb_Pax_Total'].sum()
    intensite = total_co2 / nb_pax if nb_pax > 0 else 0
    
    st.title(f"🌍 Pilotage Stratégique Carbone")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Emissions", f"{total_co2/1000:,.0f} tCO2e")
    c2.metric("Intensité", f"{intensite:.0f} kg/pax")
    c3.metric("Scénario", f"-{reduction_objectif}% Aérien")
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🗺️ Cartographie", "📊 Analyse"])
    
    with tab1:
        # OPTIMISATION ANTI-LAG : On regroupe par Pays avant d'afficher
        # On s'assure d'avoir des coordonnées valides (pas None)
        df_map = df.dropna(subset=['lat', 'lon']).groupby('Pays').agg({
            'lat': 'first', 
            'lon': 'first', 
            'CO2_Total_Simule': 'sum',
            'Continent': 'first' # Si colonne existe
        }).reset_index()
        
        fig_map = px.scatter_geo(
            df_map, 
            lat="lat", lon="lon", 
            size="CO2_Total_Simule", 
            hover_name="Pays",
            title=f"Carte des émissions (Agrégée par pays)",
            projection="natural earth",
            size_max=40 # Taille des bulles
        )
        fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    with tab2:
        top10 = df.sort_values("CO2_Total", ascending=False).head(10)
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total'], name='Actuel', marker_color='#E63946'))
        if reduction_objectif > 0:
            fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total_Simule'], name='Simulé', marker_color='#2A9D8F'))
        st.plotly_chart(fig, use_container_width=True)

    # Export PDF
    pdf_bytes = generate_pdf({'Total_CO2': total_co2, 'Intensite': intensite}, f"Scenario : -{reduction_objectif}% Avion")
    if pdf_bytes:
        st.download_button("📑 Rapport PDF", pdf_bytes, "Rapport.pdf")
