import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Strategic Carbon Monitor", layout="wide", page_icon="🌍")

# --- 1. GÉNÉRATEUR DE DONNÉES DE DÉMO (Pour l'effet Wow) ---
def load_demo_data():
    data = {
        'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon', 'Perou', 'Tanzanie', 'Norvege', 'Grece'],
        'Continent': ['Europe', 'Europe', 'Asie', 'Afrique', 'Europe', 'Asie', 'Amerique', 'Afrique', 'Europe', 'Europe'],
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

# Le curseur magique
reduction_objectif = st.sidebar.slider("Réduction du trafic Aérien (%)", 0, 50, 0, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("### Gestion des Données")
uploaded_file = st.sidebar.file_uploader("Importer Excel", type=["xlsx"])

# Téléchargement Template (Format corrigé Multi-onglets)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    # On crée la structure exacte attendue
    pd.DataFrame(columns=['Pays', 'Continent', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre']).to_excel(writer, sheet_name='Destinations', index=False)
st.sidebar.download_button("📥 Télécharger Template Vide", buffer.getvalue(), "Template_Correct.xlsx")


# --- 4. LOGIQUE DE LECTURE ROBUSTE ---
df = None

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        
        # C'EST ICI QUE JE CORRIGE L'ERREUR :
        # On vérifie si l'onglet 'Destinations' existe (cas du fichier multi-onglets)
        if 'Destinations' in xls.sheet_names:
            df = pd.read_excel(xls, 'Destinations')
        else:
            # Sinon on lit le premier onglet (cas d'un fichier simple)
            df = pd.read_excel(xls)
            
        # Vérification des colonnes
        required_cols = ['Pays', 'CO2_Aerien', 'CO2_Terrestre']
        if not all(col in df.columns for col in required_cols):
            st.error(f"⚠️ Colonnes manquantes ! Le fichier doit contenir : {required_cols}")
            st.stop()
            
        # Calcul du total si absent
        if 'CO2_Total' not in df.columns:
            df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
            
        st.toast("Fichier chargé avec succès !", icon="✅")
        
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        st.stop()
else:
    # Si rien n'est chargé, on utilise la Démo
    df = load_demo_data()


# --- 5. CALCULS & SIMULATION ---

# On applique la réduction du curseur
df['CO2_Aerien_Simule'] = df['CO2_Aerien'] * (1 - reduction_objectif/100)
df['CO2_Total_Simule'] = df['CO2_Aerien_Simule'] + df['CO2_Terrestre']

# KPIs globaux recalculés
total_co2_simule = df['CO2_Total_Simule'].sum()
nb_pax = df['Nb_Pax_Total'].sum()
intensite = total_co2_simule / nb_pax if nb_pax > 0 else 0
gain_co2 = df['CO2_Total'].sum() - total_co2_simule

kpi_dict = {'Total_CO2': total_co2_simule, 'Intensite': intensite}


# --- 6. DASHBOARD ---

st.title(f"🌍 Pilotage Stratégique Carbone")

# INDICATEURS
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Emissions", f"{total_co2_simule/1000:,.0f} tCO2e", delta=f"-{gain_co2/1000:,.0f} t" if gain_co2 > 1 else None, delta_color="inverse")
c2.metric("Intensité Carbone", f"{intensite:.0f} kg/pax", delta_color="inverse")
c3.metric("Volume Voyageurs", f"{nb_pax:,.0f}")
c4.metric("Scénario Aérien", f"-{reduction_objectif}%")

st.markdown("---")

# ONGLETS
tab1, tab2 = st.tabs(["📊 Analyse Matérialité", "☀️ Répartition Géographique"])

with tab1:
    st.subheader("Comparaison Avant / Après Simulation")
    
    # On prépare les données pour le graphique groupé
    top10 = df.sort_values("CO2_Total", ascending=False).head(10)
    
    import plotly.graph_objects as go
    fig = go.Figure()
    fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total'], name='Actuel', marker_color='#E63946'))
    
    if reduction_objectif > 0:
        fig.add_trace(go.Bar(x=top10['Pays'], y=top10['CO2_Total_Simule'], name=f'Simulé (-{reduction_objectif}%)', marker_color='#2A9D8F'))
    
    fig.update_layout(barmode='group', title="Impact de la réduction aérienne par pays")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Sunburst : Continent > Pays")
    if 'Continent' in df.columns:
        fig_sun = px.sunburst(df, path=['Continent', 'Pays'], values='CO2_Total_Simule', color='CO2_Total_Simule', title="Hiérarchie des émissions")
        st.plotly_chart(fig_sun, use_container_width=True)
    else:
        st.info("Ajoutez une colonne 'Continent' dans votre Excel pour voir ce graphique.")
        st.dataframe(df)

# EXPORT
st.markdown("---")
sim_txt = f"Scenario : Reduction de {reduction_objectif}% de l'aerien.\nGain CO2 : {gain_co2/1000:,.1f} tonnes."
pdf_bytes = generate_pdf(kpi_dict, simulation_text=sim_txt)
if pdf_bytes:
    st.download_button("📑 Exporter Rapport PDF", pdf_bytes, "Rapport_Simulation.pdf", "application/pdf")
