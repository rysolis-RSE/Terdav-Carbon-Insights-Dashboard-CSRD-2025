import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Dashboard CSRD & Transition Bas-Carbone", layout="wide", page_icon="🌍")

# --- STYLE CSS (Pour le look "Pro") ---
st.markdown("""
    <style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #2A9D8F;}
    .stMetric label {font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 1. GÉNÉRATEUR DE DONNÉES DE DÉMO (SYNTHÉTIQUES) ---
# C'est ce qui rend ton app "vivante" immédiatement sans fichiers
def load_demo_data():
    data = {
        'Pays': ['France', 'Italie', 'Nepal', 'Maroc', 'Islande', 'Japon', 'Perou', 'Tanzanie', 'Norvege', 'Grece'],
        'Nb_Pax_Total': [5000, 3200, 800, 2100, 900, 450, 300, 250, 600, 1500],
        'Nb_Pax_Sans_Aérien': [4800, 2500, 0, 100, 0, 0, 0, 0, 100, 200], # Le point fort RSE
        'CO2_Aerien': [20000, 150000, 1200000, 500000, 450000, 900000, 750000, 600000, 180000, 400000],
        'CO2_Terrestre': [150000, 120000, 40000, 80000, 30000, 20000, 15000, 12000, 25000, 50000]
    }
    df = pd.DataFrame(data)
    df['Nb_Pax_Aérien'] = df['Nb_Pax_Total'] - df['Nb_Pax_Sans_Aérien']
    df['CO2_Total'] = df['CO2_Aerien'] + df['CO2_Terrestre']
    
    # KPI Global fictif
    kpi = {
        'Annee': 2025,
        'Total_CO2': df['CO2_Total'].sum(),
        'Nb_Pax_Total': df['Nb_Pax_Total'].sum(),
        'Nb_Pax_Sans_Aérien': df['Nb_Pax_Sans_Aérien'].sum()
    }
    return kpi, df

# --- 2. FONCTION PDF (RAPPORT CSRD) ---
def generate_pdf(kpi, df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(190, 15, "Rapport de Durabilite - CSRD E1", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Bilan Carbone {kpi['Annee']} - Scope 3 Aval", ln=True)
    
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 8, f"Intensite Carbone : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f} kgCO2e/pax", ln=True)
    
    # Calcul du taux de report modal
    ratio = (kpi['Nb_Pax_Sans_Aérien'] / kpi['Nb_Pax_Total']) * 100
    pdf.cell(190, 8, f"Part de voyageurs Bas-Carbone (Sans Avion) : {ratio:.1f}%", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Top 5 Destinations Critiques (Matérialité)", ln=True)
    
    top_5 = df.sort_values("CO2_Total", ascending=False).head(5)
    for i, row in top_5.iterrows():
        pdf.cell(190, 7, f"- {row['Pays']} : {row['CO2_Total']/1000:,.0f} tCO2e (Dont Air: {row['CO2_Aerien']/row['CO2_Total']*100:.0f}%)", ln=True)
        
    return pdf.output(dest="S").encode("latin-1")

# --- 3. BARRE LATÉRALE ---
st.sidebar.title("🛠️ Paramètres")
st.sidebar.info("💡 **Mode Démo actif** : L'application affiche des données synthétiques pour illustrer les fonctionnalités.")

# Upload
uploaded_file = st.sidebar.file_uploader("📂 Importer vos données réelles (Excel)", type=["xlsx"])

# Téléchargement Template (Code généré en mémoire)
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Annee', 'Total_CO2', 'Nb_Pax_Total', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
    pd.DataFrame(columns=['Pays', 'CO2_Aerien', 'CO2_Terrestre', 'Nb_Pax_Total', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='Destinations', index=False)
    
st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=buffer.getvalue(),
    file_name="Template_CSRD.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- 4. LOGIQUE DE CHARGEMENT ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        # On essaie de lire les vraies données
        df_kpi_real = pd.read_excel(xls, 'KPI_Globaux')
        df_dest_real = pd.read_excel(xls, 'Destinations')
        
        # Adaptation des colonnes
        kpi_data = df_kpi_real.iloc[0]
        # On recrée un dictionnaire standardisé
        kpi = {
            'Annee': int(kpi_data.get('Annee', 2025)),
            'Total_CO2': kpi_data['Total_CO2'],
            'Nb_Pax_Total': kpi_data['Nb_Pax_Total'],
            'Nb_Pax_Sans_Aérien': kpi_data.get('Nb_Pax_Sans_Aérien', 0) 
        }
        df_display = df_dest_real
        df_display['CO2_Total'] = df_display['CO2_Aerien'] + df_display['CO2_Terrestre']
        st.success("✅ Données importées avec succès")
        
    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
        st.stop()
else:
    # SI PAS DE FICHIER -> ON CHARGE LA DÉMO
    kpi, df_display = load_demo_data()

# --- 5. DASHBOARD PRINCIPAL ---

st.title(f"🌍 Pilotage Carbone & CSRD - Vision {kpi['Annee']}")
st.markdown("Ce tableau de bord permet de piloter la trajectoire de décarbonation (**ESRS E1-1**) et le report modal.")

# --- SECTION KPIs (La partie stratégique) ---
col1, col2, col3, col4 = st.columns(4)

intensity = kpi['Total_CO2'] / kpi['Nb_Pax_Total']
taux_sans_avion = (kpi['Nb_Pax_Sans_Aérien'] / kpi['Nb_Pax_Total']) * 100

col1.metric("Scope 3 Aval (Total)", f"{kpi['Total_CO2']/1000:,.0f} tCO2e", delta="ESRS E1-6")
col2.metric("Intensité Carbone", f"{intensity:.0f} kgCO2e/pax", delta_color="inverse", help="Métrique clé pour mesurer l'efficacité carbone")
col3.metric("Voyageurs Totaux", f"{kpi['Nb_Pax_Total']:,.0f}")
col4.metric("Part Sans Aérien", f"{taux_sans_avion:.1f}%", delta="Objectif Transition", help="Part des voyageurs n'utilisant pas l'avion")

st.markdown("---")

# --- SECTION GRAPHIQUES ---
tab1, tab2 = st.tabs(["📊 Matérialité (Impact)", "🚄 Focus Report Modal"])

with tab1:
    st.subheader("Identification des 'Hotspots' (Aérien vs Terrestre)")
    st.caption("Ce graphique permet de distinguer l'impact du transport international de l'impact local.")
    
    fig = px.bar(
        df_display.sort_values("CO2_Total", ascending=False).head(12),
        x="Pays",
        y=["CO2_Aerien", "CO2_Terrestre"],
        title="Émissions par Destination et par Mode",
        labels={"value": "kgCO2e", "variable": "Scope"},
        color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#2A9D8F"}
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Performance du 'Sans Aérien' par Destination")
    # Calcul du ratio par pays pour le graphe
    df_display['Ratio_Sans_Air'] = (df_display['Nb_Pax_Sans_Aérien'] / df_display['Nb_Pax_Total']) * 100
    
    fig2 = px.scatter(
        df_display[df_display['Nb_Pax_Total'] > 50], # Filtre petits volumes
        x="Nb_Pax_Total",
        y="Ratio_Sans_Air",
        size="CO2_Total",
        color="Pays",
        title="Matrice : Volume vs Taux de décarbonation",
        labels={"Ratio_Sans_Air": "% Sans Avion", "Nb_Pax_Total": "Volume Pax"},
        text="Pays"
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- SECTION EXPORT ---
st.markdown("---")
st.subheader("📑 Reporting Réglementaire")
col_pdf, col_spacer = st.columns([1, 4])
pdf_bytes = generate_pdf(kpi, df_display)
col_pdf.download_button("Générer le Rapport CSRD (PDF)", pdf_bytes, "Rapport_CSRD.pdf", "application/pdf")
