import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 1. DONNÉES DE DÉMO (RICHE : AVEC GPS & CONTINENTS) ---
def load_demo_data():
    data = {
        'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon', 'Perou', 'Tanzanie', 'Norvege', 'Grece'],
        'Continent': ['Europe', 'Europe', 'Asie', 'Afrique', 'Europe', 'Asie', 'Amerique', 'Afrique', 'Europe', 'Europe'],
        'lat': [46.22, 41.87, 28.39, 31.79, 64.96, 36.20, -9.19, -6.36, 60.47, 39.07],
        'lon': [2.21, 12.56, 84.12, -7.09, -19.02, 138.25, -75.01, 34.88, 8.46, 21.82],
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
        pdf.set_font("Arial", "B", 20)
        pdf.cell(190, 15, "Rapport Strategique Carbone", ln=True, align="C")
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "Bilan Scope 3 Aval", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 8, f"Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"Intensite Moyenne : {kpi['Intensite']:.0f} kgCO2e/pax", ln=True)
        
        if simulation_text:
            pdf.ln(5)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(190, 10, "Scenario de Simulation", ln=True)
            pdf.set_font("Arial", "I", 11)
            pdf.multi_cell(190, 8, simulation_text)

        return pdf.output(dest="S").encode("latin-1")
    except:
        return None

# --- 3. BARRE LATÉRALE ---
st.sidebar.title("🎛️ Simulateur")
reduction_objectif = st.sidebar.slider("Réduction du trafic Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Gestion des Données")
uploaded_file = st.sidebar.file_uploader("Importer Excel", type=["xlsx"])

# Téléchargement Template (Format corrigé)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Pays', 'Continent', 'lat', 'lon', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, sheet_name='Destinations', index=False)
st.sidebar.download_button("📥 Télécharger Template Complet", buffer.getvalue(), "Template_Full.xlsx")


# --- 4. LOGIQUE DE LECTURE INTELLIGENTE ---
df = None

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        # On cherche l'onglet 'Destinations'
        if 'Destinations' in xls.sheet_names:
            df = pd.read_excel(xls, 'Destinations')
        else:
            df = pd.read_excel(xls) # Sinon 1er onglet
            
        # Calcul du total si absent
        if 'CO2_Total' not in df.columns and 'CO2_Aerien' in df.columns:
            df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
            
        st.toast("Fichier chargé !", icon="✅")
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        st.stop()
else:
    df = load_demo_data()


# --- 5. CALCULS & SIMULATION ---
if df is not None:
    # On applique la réduction
    df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
    df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

    total_co2_simule = df['CO2_Total_Simule'].sum()
    nb_pax = df['Nb_Pax_Total'].sum()
    intensite = total_co2_simule / nb_pax if nb_pax > 0 else 0
    gain_co2 = df['CO2_Total'].sum() - total_co2_simule

    kpi_dict = {'Total_CO2': total_co2_simule, 'Intensite': intensite}


    # --- 6. DASHBOARD ---
    st.title(f"🌍 Pilotage Stratégique Carbone")

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Emissions", f"{total_co2_simule/1000:,.0f} tCO2e", delta=f"-{gain_co2/1000:,.0f} t", delta_color="inverse")
    c2.metric("Intensité Carbone", f"{intensite:.0f} kg/pax", delta_color="inverse")
    c3.metric("Volume Voyageurs", f"{nb_pax:,.0f}")
    c4.metric("Scénario Aérien", f"-{reduction_objectif}%")

    st.markdown("---")

    # ONGLETS (LE RETOUR DE LA CARTE)
    tab1, tab2, tab3 = st.tabs(["🗺️ Cartographie", "☀️ Sunburst & Détails", "📊 Comparaison Scénario"])

    with tab1:
        st.subheader("Empreinte Carbone Géospatiale")
        # On vérifie si les colonnes lat/lon existent pour afficher la carte
        if 'lat' in df.columns and 'lon' in df.columns:
            fig_map = px.scatter_geo(
                df, 
                lat="lat", lon="lon", 
                size="CO2_Total_Simule", 
                color="Continent" if 'Continent' in df.columns else "Pays",
                hover_name="Pays",
                projection="natural earth",
                title=f"Carte des émissions (Scénario : -{reduction_objectif}% Aérien)",
                size_max=40
            )
            fig_map.update_layout(margin={"r":0,"t":30,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("⚠️ Pour afficher la carte, votre fichier Excel doit contenir les colonnes 'lat' et 'lon'. (Utilisez le template complet)")
            st.dataframe(df.head())

    with tab2:
        st.subheader("Hiérarchie des émissions")
        if 'Continent' in df.columns:
            fig_sun = px.sunburst(df, path=['Continent', 'Pays'], values='CO2_Total_Simule', color='CO2_Total_Simule', title="Zoom par Continent")
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.warning("⚠️ Pour le graphique Sunburst, ajoutez une colonne 'Continent' dans votre Excel.")
            # Fallback sur un simple bar chart si pas de continent
            fig_bar = px.bar(df.head(15), x="Pays", y="CO2_Total_Simule", title="Top 15 Pays")
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.subheader("Impact de la Simulation sur le Top 10 Destinations")
        top10 = df.sort_values("CO2_Total", ascending=False).head(10)
        
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total'], name='Actuel', marker_color='#E63946'))
        if reduction_objectif > 0:
            fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total_Simule'], name=f'Simulé (-{reduction_objectif}%)', marker_color='#2A9D8F'))
        
        fig.update_layout(barmode='group', title="Gains potentiels par pays")
        st.plotly_chart(fig, use_container_width=True)

    # EXPORT
    st.markdown("---")
    sim_txt = f"Scenario : Reduction de {reduction_objectif}% de l'aerien.\nGain CO2 : {gain_co2/1000:,.1f} tonnes."
    pdf_bytes = generate_pdf(kpi_dict, simulation_text=sim_txt)
    if pdf_bytes:
        st.download_button("📑 Exporter Rapport PDF", pdf_bytes, "Rapport_Simulation.pdf", "application/pdf")
