import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Terdav Carbon Analytics", layout="wide", page_icon="🌍")

# --- STYLE VISUEL ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION EXPORT PDF ---
def generate_pdf(kpi, df_dest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Rapport Strategique Carbone - Terres d'Aventure", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Total Emissions : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 10, f"Nombre de Voyageurs : {kpi['Nb_Pax_Total']:,.0f}", ln=True)
    pdf.cell(190, 10, f"Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f} kgCO2e/pax", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/fr/6/69/Logo_Terres_d_Aventure.png", width=150)
    st.title("Pilotage RSE")
    
    st.subheader("1. Récupérer le Template")
    # --- BOUTON DE TÉLÉCHARGEMENT DIRECT ---
    template_name = "Bilan_Carbone_Database.xlsx"
    if os.path.exists(template_name):
        with open(template_name, "rb") as file:
            st.download_button(
                label="📥 Télécharger le fichier Excel",
                data=file,
                file_name="Template_Terdav_Carbone.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                help="Cliquez ici pour obtenir le fichier Excel à remplir."
            )
    else:
        st.error("Fichier template introuvable sur le serveur.")

    st.markdown("---")
    st.subheader("2. Analyser vos données")
    uploaded_file = st.file_uploader("Importer le fichier rempli", type=["xlsx"])

# --- CONTENU PRINCIPAL ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        
        kpi = df_kpi.iloc[0]
        
        st.title(f"📊 Bilan Carbone Annuel")
        
        # INDICATEURS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Emissions (tCO2)", f"{kpi['Total_CO2']/1000:,.0f}")
        c2.metric("Passagers", f"{kpi['Nb_Pax_Total']:,.0f}")
        c3.metric("kgCO2 / pax", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f}")
        
        # EXPORT PDF
        pdf_bytes = generate_pdf(kpi, df_dest)
        c4.download_button("📄 Rapport PDF", pdf_bytes, "Rapport_Carbone.pdf", "application/pdf")

        st.markdown("---")
        
        # GRAPHIQUE
        top_10 = df_dest.sort_values("CO2_Total", ascending=False).head(10)
        fig = px.bar(top_10, x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                     title="Impact par Destination (Aérien vs Terrestre)",
                     barmode="stack", color_discrete_sequence=["#E63946", "#457B9D"])
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur de lecture : {e}")
else:
    st.title("🚀 Outil d'Analyse Carbone Terdav")
    st.info("Utilisez le menu à gauche pour télécharger le template Excel, le compléter et le recharger ici.")
    st.markdown("""
    ### Procédure :
    1. **Télécharger** : Récupérez le fichier Excel via le bouton dans la barre latérale.
    2. **Remplir** : Ajoutez vos données dans les colonnes prévues (ne changez pas les noms des onglets).
    3. **Visualiser** : Glissez le fichier dans la zone d'importation pour voir les analyses et télécharger le rapport PDF.
    """)
