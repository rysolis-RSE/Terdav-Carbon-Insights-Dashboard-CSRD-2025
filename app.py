import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 0. DONNÉES DE DÉMO (Au cas où aucun fichier n'est chargé) ---
DEMO_HISTORY = pd.DataFrame({
    'Annee': [2023, 2024, 2025],
    'Total_CO2': [50000000, 51500000, 49000000], 
    'Nb_Pax_Total': [30000, 31000, 30500]
})

DEMO_DESTINATIONS = pd.DataFrame({
    'Pays': ['France', 'Italie', 'Vietnam', 'Maroc', 'Islande', 'Japon'],
    'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450],
    'CO2_Total': [200000, 300000, 1200000, 500000, 450000, 900000],
    'CO2_Aerien': [20000, 150000, 1000000, 400000, 400000, 800000],
    'CO2_Terrestre': [180000, 150000, 200000, 100000, 50000, 100000]
})

# Base GPS
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

# --- 1. FONCTIONS ---
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
st.sidebar.title("🎛️ Paramètres")
prix_tonne = st.sidebar.slider("Prix Tonne CO2 (€)", 0, 200, 80, 10)
reduction_objectif = st.sidebar.slider("Réduction Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")

# BOUTON TÉLÉCHARGEMENT DU TEMPLATE COMPLET
# On génère un fichier Excel exemple avec les 2 onglets requis
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # Onglet 1 : Destinations (Structure vide)
    pd.DataFrame(columns=['Pays', 'Nb_Pax_Total', 'CO2_Total', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, sheet_name='Destinations', index=False)
    # Onglet 2 : Evolution (Structure vide)
    pd.DataFrame(columns=['Annee', 'Total_CO2', 'Nb_Pax_Total']).to_excel(writer, sheet_name='Evolution', index=False)
    
st.sidebar.download_button(
    label="📥 Télécharger Template Vierge (2 Onglets)",
    data=buffer.getvalue(),
    file_name="Template_Carbone_Complet.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Utilisez ce modèle qui contient déjà les onglets 'Destinations' et 'Evolution'."
)

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("Importer le fichier Excel", type=["xlsx"])


# --- 3. CHARGEMENT ET LECTURE ---
df_dest = DEMO_DESTINATIONS.copy()
df_evol = DEMO_HISTORY.copy()
is_demo = True

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        is_demo = False
        
        # Lecture Destinations
        if 'Destinations' in xls.sheet_names:
            df_dest = pd.read_excel(xls, 'Destinations')
        else:
            df_dest = pd.read_excel(xls) # Tentative 1er onglet
        
        # Lecture Evolution
        if 'Evolution' in xls.sheet_names:
            df_evol = pd.read_excel(xls, 'Evolution')
        else:
            # Si l'onglet manque, on reste sur la démo pour cette partie et on avertit
            st.warning("⚠️ L'onglet 'Evolution' est manquant dans votre fichier. La trajectoire affichée est fictive.")
            df_evol = DEMO_HISTORY.copy()
            
        st.sidebar.success("✅ Fichier chargé avec succès")
            
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        st.stop()
else:
    st.sidebar.info("ℹ️ Mode Démo (Données fictives)")

# --- 4. TRAITEMENT ---
# Nettoyage
df_dest['Pays'] = df_dest['Pays'].astype(str).str.strip()
df_dest['coords'] = df_dest['Pays'].apply(lambda x: COORDINATES_DB.get(x, [None, None]))
df_dest[['lat', 'lon']] = pd.DataFrame(df_dest['coords'].tolist(), index=df_dest.index)

# Calculs
if 'CO2_Total' not in df_dest.columns:
    df_dest['CO2_Total'] = df_dest['CO2_Aerien'] + df_dest['CO2_Terrestre']

# Simulation
df_dest['CO2_Aerien_Simule'] = df_dest['CO2_Aerien'] * (1 - reduction_objectif/100)
df_dest['CO2_Total_Simule'] = df_dest['CO2_Aerien_Simule'] + df_dest['CO2_Terrestre']

total_simule = df_dest['CO2_Total_Simule'].sum()
cout_carbone = (total_simule / 1000) * prix_tonne

# --- 5. DASHBOARD ---
st.title("🌍 Pilotage Stratégique & Financier (CSRD)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total CO2 2025 (Simulé)", f"{total_simule/1000:,.0f} tCO2e")
c2.metric("Risque Financier", f"{cout_carbone:,.0f} €", delta=f"{prix_tonne}€/t", delta_color="inverse")
c3.metric("Obj. Réduction CSRD", "-1.5% / an")

# Evolution N vs N-1
if not df_evol.empty and len(df_evol) >= 2:
    val_actuelle = df_evol.iloc[-1]['Total_CO2']
    val_precedente = df_evol.iloc[-2]['Total_CO2']
    evo = ((val_actuelle - val_precedente) / val_precedente) * 100
    c4.metric("Evolution vs N-1", f"{evo:+.1f}%", delta_color="inverse")
else:
    c4.metric("Pays Analysés", f"{len(df_dest)}")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📉 Trajectoire & Cible", "🗺️ Carte Hotspots", "📊 Détails Pays"])

with tab1:
    st.subheader("Trajectoire vs Objectif CSRD (-1.5%)")
    
    if not df_evol.empty:
        start_year = int(df_evol['Annee'].min())
        ref_value = df_evol[df_evol['Annee'] == start_year]['Total_CO2'].values[0]
        annees_proj = [start_year + i for i in range(5)]
        target_values = [ref_value * ((1 - 0.015) ** (yr - start_year)) for yr in annees_proj]
        
        fig_traj = go.Figure()
        
        fig_traj.add_trace(go.Scatter(
            x=df_evol['Annee'], y=df_evol['Total_CO2'],
            mode='lines+markers', name='Historique Réel',
            line=dict(color='#E63946', width=4), marker=dict(size=12)
        ))
        
        fig_traj.add_trace(go.Scatter(
            x=annees_proj, y=target_values,
            mode='lines', name='Cible CSRD (-1.5%)',
            line=dict(color='purple', dash='dot', width=2)
        ))

        if reduction_objectif > 0:
            current_year = int(df_evol['Annee'].max())
            fig_traj.add_trace(go.Scatter(
                x=[current_year], y=[total_simule],
                mode='markers', name=f'Simulation (-{reduction_objectif}%)',
                marker=dict(color='#2A9D8F', size=15, symbol='star')
            ))

        fig_traj.update_layout(title="Trajectoire CO2", yaxis_title="kg CO2e")
        st.plotly_chart(fig_traj, use_container_width=True)
    else:
        st.info("Données d'évolution non disponibles.")

with tab2:
    st.subheader("Cartographie des Risques")
    df_map = df_dest.dropna(subset=['lat', 'lon']).groupby('Pays').agg({
        'lat': 'first', 'lon': 'first', 'CO2_Total_Simule': 'sum'
    }).reset_index()

    if not df_map.empty:
        fig_map = px.scatter_geo(
            df_map, lat="lat", lon="lon", size="CO2_Total_Simule", color="CO2_Total_Simule",
            hover_name="Pays", projection="natural earth",
            size_max=50, color_continuous_scale="Reds", opacity=0.9,
            title="Intensité Carbone par Destination"
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Aucun pays reconnu pour la carte.")

with tab3:
    st.dataframe(df_dest[['Pays', 'Nb_Pax_Total', 'CO2_Total_Simule']].sort_values('CO2_Total_Simule', ascending=False))

# Export PDF
if st.button("📄 Télécharger Rapport"):
    pdf_bytes = generate_pdf({'Total_CO2': total_simule, 'Cout_Carbone': cout_carbone})
    if pdf_bytes:
        st.download_button("📥 Rapport PDF", pdf_bytes, "Rapport_Carbone.pdf")
