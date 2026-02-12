import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- STYLE CSS AVANCÉ ---
st.markdown("""
    <style>
    .metric-card {background-color: #f8f9fa; border-left: 5px solid #2A9D8F; padding: 15px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);}
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 4px; padding-top: 8px; padding-bottom: 8px; }
    h1 { color: #264653; }
    h3 { color: #2A9D8F; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. GÉNÉRATEUR DE DONNÉES DE DÉMO (AVEC COORDONNÉES GPS) ---
def load_demo_data():
    data = {
        'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon', 'Perou', 'Tanzanie', 'Norvege', 'Grece'],
        'Continent': ['Europe', 'Europe', 'Asie', 'Afrique', 'Europe', 'Asie', 'Amerique', 'Afrique', 'Europe', 'Europe'],
        'lat': [46.22, 41.87, 28.39, 31.79, 64.96, 36.20, -9.19, -6.36, 60.47, 39.07],
        'lon': [2.21, 12.56, 84.12, -7.09, -19.02, 138.25, -75.01, 34.88, 8.46, 21.82],
        'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450, 300, 250, 600, 1500],
        'Nb_Pax_Sans_Aérien': [4800, 2500, 0, 100, 0, 0, 0, 0, 100, 200],
        'CO2_Aerien': [20000, 150000, 1200000, 500000, 450000, 900000, 750000, 600000, 180000, 400000],
        'CO2_Terrestre': [150000, 120000, 40000, 80000, 30000, 20000, 15000, 12000, 25000, 50000]
    }
    df = pd.DataFrame(data)
    df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
    return df

# --- 2. FONCTION PDF ---
def generate_pdf(kpi, df, simulation_text=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(190, 15, "Rapport CSRD & Strategie Climat", ln=True, align="C")
    
    pdf.set_font("Arial", "I", 10)
    pdf.cell(190, 10, "Genere par Terdav Analytics Tool", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "1. Bilan Carbone (Scope 3 Aval)", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 8, f"Intensite Moyenne : {kpi['Intensite']:.0f} kgCO2e/pax", ln=True)
    
    if simulation_text:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "2. Scenario de Simulation", ln=True)
        pdf.set_font("Arial", "I", 11)
        pdf.multi_cell(190, 8, simulation_text)

    return pdf.output(dest="S").encode("latin-1")

# --- 3. BARRE LATÉRALE (SIMULATEUR) ---
st.sidebar.title("🎛️ Simulateur")
st.sidebar.markdown("### Objectifs de Réduction")

# Le curseur magique
reduction_objectif = st.sidebar.slider(
    "Réduction du trafic Aérien (%)", 
    min_value=0, max_value=50, value=0, step=5,
    help="Simulez une baisse du volume aérien ou un report modal."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Données")
uploaded_file = st.sidebar.file_uploader("Importer Excel", type=["xlsx"])

# Téléchargement Template (généré à la volée)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Pays', 'Continent', 'lat', 'lon', 'Nb_Pax_Total', 'Nb_Pax_Sans_Aérien', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, index=False)
st.sidebar.download_button("📥 Template Vide", buffer.getvalue(), "Template_Advanced.xlsx")


# --- 4. LOGIQUE DES DONNÉES ---
if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        # Calculs basiques si colonnes manquantes
        if 'CO2_Total' not in df.columns:
            df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
        st.toast("Données réelles chargées !", icon="✅")
    except Exception as e:
        st.error(f"Erreur Excel : {e}")
        st.stop()
else:
    df = load_demo_data()

# APPLIQUER LA SIMULATION (Le cœur de l'intelligence)
# Si on réduit l'aérien de X%, on recalcule le CO2 Total
df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

# KPIs globaux
total_co2_actuel = df['CO2_Total'].sum()
total_co2_simule = df['CO2_Total_Simule'].sum()
nb_pax = df['Nb_Pax_Total'].sum()
intensite_actuelle = total_co2_actuel / nb_pax
intensite_simulee = total_co2_simule / nb_pax
gain_co2 = total_co2_actuel - total_co2_simule

kpi_dict = {'Total_CO2': total_co2_simule, 'Intensite': intensite_simulee}

# --- 5. DASHBOARD ---

st.title(f"🌍 Pilotage Stratégique Carbone")
st.markdown("Analyse d'impact, Matérialité et Scénarios de transition (**ESRS E1**).")

# CARTES INDICATEURS
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Emissions (Scope 3)", f"{total_co2_simule/1000:,.0f} tCO2e", 
          delta=f"-{gain_co2/1000:,.0f} t" if reduction_objectif > 0 else None, delta_color="inverse")
c2.metric("Intensité Carbone", f"{intensite_simulee:.0f} kg/pax", 
          delta=f"{intensite_simulee - intensite_actuelle:.0f}", delta_color="inverse")
c3.metric("Volume Voyageurs", f"{nb_pax:,.0f}")
c4.metric("Objectif Réduction Air", f"-{reduction_objectif}%")

st.markdown("---")

# ONGLETS D'ANALYSE AVANCÉE
tab1, tab2, tab3 = st.tabs(["🗺️ Cartographie Mondiale", "☀️ Analyse Granulaire", "📉 Comparaison Scénario"])

with tab1:
    st.subheader("Empreinte Carbone Géospatiale")
    # Carte à bulles interactive
    fig_map = px.scatter_geo(
        df, 
        lat="lat", lon="lon", 
        size="CO2_Total_Simule", 
        color="Continent",
        hover_name="Pays",
        projection="natural earth",
        title=f"Localisation des émissions (Scénario : -{reduction_objectif}% Aérien)",
        size_max=50
    )
    fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

with tab2:
    st.subheader("Répartition 'Sunburst' (Continent > Pays)")
    # Le Sunburst est le meilleur graph pour voir la hiérarchie
    fig_sun = px.sunburst(
        df, 
        path=['Continent', 'Pays'], 
        values='CO2_Total_Simule',
        color='CO2_Total_Simule',
        color_continuous_scale='RdBu_r',
        title="Où se cachent les émissions ?"
    )
    st.plotly_chart(fig_sun, use_container_width=True)

with tab3:
    st.subheader("Impact de la Simulation sur le Top 10 Destinations")
    # Comparaison avant/après simulation
    top10 = df.sort_values("CO2_Total", ascending=False).head(10)
    
    import plotly.graph_objects as go
    fig_comp = go.Figure()
    fig_comp.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total'], name='Actuel (2025)', marker_color='#E63946'))
    if reduction_objectif > 0:
        fig_comp.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total_Simule'], name=f'Simulé (-{reduction_objectif}%)', marker_color='#2A9D8F'))
    
    fig_comp.update_layout(title="Gain potentiel par destination", barmode='group')
    st.plotly_chart(fig_comp, use_container_width=True)

# EXPORT
st.markdown("---")
col_pdf, _ = st.columns([1,4])
sim_txt = f"Scenario retenu : Reduction de {reduction_objectif}% des emissions aeriennes.\nGain total estime : {gain_co2/1000:,.1f} tonnes de CO2e."
pdf_data = generate_pdf(kpi_dict, df, simulation_text=sim_txt)
col_pdf.download_button("📑 Exporter le Rapport de Simulation (PDF)", pdf_data, "Plan_Transition.pdf", "application/pdf")
