import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Terdav Carbon Dashboard", layout="wide", page_icon="🌍")

# --- FONCTION GENERATION PDF ---
def generate_pdf(kpi, df_dest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Rapport d'Analyse Carbone - CSRD", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Bilan Annuel", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"- Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 8, f"- Nombre de Voyageurs : {kpi['Nb_Pax_Total']:,.0f}", ln=True)
    pdf.cell(190, 8, f"- Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f} kgCO2e/pax", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "Top 5 Destinations les plus emetrices :", ln=True)
    pdf.set_font("Arial", "", 10)
    top_5 = df_dest.sort_values("CO2_Total", ascending=False).head(5)
    for i, row in top_5.iterrows():
        pdf.cell(190, 7, f"- {row['Pays']} : {row['CO2_Total']/1000:,.1f} tCO2e", ln=True)
        
    return pdf.output(dest="S").encode("latin-1")

# --- BARRE LATÉRALE ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/fr/6/69/Logo_Terres_d_Aventure.png", width=150)
st.sidebar.title("Configuration")

# 1. GENERATION DU TEMPLATE VIDE DYNAMIQUE
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Annee', 'Total_CO2', 'Part_Aerien', 'Part_Terrestre', 'Part_Salaries', 'Nb_Pax_Total']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
    pd.DataFrame(columns=['Pays', 'CO2_Total', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre', 'Nb_Pax_Aérien', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='Destinations', index=False)
    pd.DataFrame(columns=['Date Dep', 'Pays', 'Trajet', 'Type', 'Distance Km', 'Kg_CO2']).to_excel(writer, sheet_name='Details_Vols', index=False)
    writer.close()

st.sidebar.subheader("1. Template")
st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=buffer.getvalue(),
    file_name="Template_Carbone_Vierge.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.markdown("---")

# 2. UPLOAD DES DONNÉES
st.sidebar.subheader("2. Analyse")
uploaded_file = st.sidebar.file_uploader("Importer votre fichier Excel rempli", type=["xlsx"])

# --- CONTENU PRINCIPAL ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        df_vols = pd.read_excel(xls, 'Details_Vols')

        kpi = df_kpi.iloc[0]

        st.title(f"📊 Dashboard d'Analyse Carbone - {int(kpi['Annee'])}")

        # KPIS EN HAUT
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Emissions (tCO2e)", f"{kpi['Total_CO2']/1000:,.0f}")
        c2.metric("Total Voyageurs", f"{kpi['Nb_Pax_Total']:,.0f}")
        c3.metric("kgCO2 / Pax", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f}")
        
        # Bouton PDF
        pdf_bytes = generate_pdf(kpi, df_dest)
        c4.download_button("📄 Rapport PDF", pdf_bytes, f"Rapport_Carbone_{int(kpi['Annee'])}.pdf", "application/pdf")

        st.markdown("---")

        # GRAPHIQUES
        tab1, tab2 = st.tabs(["🗺️ Analyse par Pays", "✈️ Détail Aérien"])
        
        with tab1:
            st.subheader("Répartition de l'impact par destination (Air vs Terre)")
            # Graphique Stacked Bar
            top_15 = df_dest.sort_values("CO2_Total", ascending=False).head(15)
            fig = px.bar(top_15, x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                         labels={"value": "kg CO2e", "variable": "Poste d'émission"},
                         title="Comparaison Aérien vs Terrestre sur les 15 pays les plus émetteurs",
                         barmode="stack",
                         color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#457B9D"})
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            st.subheader("Analyse granulaire des segments de vols")
            st.dataframe(df_vols, use_container_width=True)
            
            # Graphe de distribution par distance
            fig_scat = px.scatter(df_vols, x="Distance Km", y="Kg_CO2", color="Type", 
                                  hover_name="Trajet", title="Émissions par segment de vol")
            st.plotly_chart(fig_scat, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur : Le fichier Excel ne respecte pas le format du template. Détail : {e}")
else:
    # Page d'accueil vide
    st.title("🚀 Outil de Pilotage Carbone CSRD")
    st.info("👋 Bienvenue ! Téléchargez le template à gauche, remplissez-le et importez-le ici pour générer le dashboard.")
    
    st.markdown("""
    ### Pourquoi utiliser cet outil ?
    - **Automatisation** : Ne perdez plus de temps à faire des graphiques Excel à la main.
    - **Vision CSRD** : Séparez l'impact de l'aérien du terrestre pour des plans d'action précis.
    - **Rapportable** : Exportez un rapport PDF pour vos réunions RSE en un clic.
    """)
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
