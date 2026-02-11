import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Terdav Carbon Analytics", layout="wide", page_icon="🌍")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION EXPORT PDF ---
def generate_pdf(kpi, df_dest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Rapport Annuel d'Emissions Carbone - Terres d'Aventure", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "1. Indicateurs Clefs", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"- Total Emissions : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 8, f"- Nombre de Voyageurs : {kpi['Nb_Pax_Total']:,.0f}", ln=True)
    pdf.cell(190, 8, f"- Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f} kgCO2e/pax", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, "2. Top 5 Destinations (Impact Total)", ln=True)
    pdf.set_font("Arial", "", 10)
    top_5 = df_dest.sort_values("CO2_Total", ascending=False).head(5)
    for i, row in top_5.iterrows():
        pdf.cell(190, 7, f"- {row['Pays']} : {row['CO2_Total']/1000:,.1f} tCO2e", ln=True)
        
    return pdf.output(dest="S").encode("latin-1")

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/fr/6/69/Logo_Terres_d_Aventure.png", width=150)
    st.title("Pilotage CSRD")
    
    # Bouton Template (On suppose que le fichier est présent sur le GitHub)
    try:
        with open("Bilan_Carbone_Database.xlsx", "rb") as f:
            st.sidebar.download_button(
                label="📥 Télécharger le Template Excel",
                data=f,
                file_name="Template_Terdav_Carbone.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except:
        st.sidebar.info("Le template 'Bilan_Carbone_Database.xlsx' doit être à la racine de votre GitHub.")

    st.markdown("---")
    uploaded_file = st.file_uploader("Importer vos données (Excel)", type=["xlsx"])

# --- CHARGEMENT DES DONNÉES ---
if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)
    df_kpi = pd.read_excel(xls, 'KPI_Globaux')
    df_dest = pd.read_excel(xls, 'Destinations')
    df_vols = pd.read_excel(xls, 'Details_Vols')
    
    kpi = df_kpi.iloc[0]

    # --- HEADER DASHBOARD ---
    st.title(f"🌍 Bilan Carbone Terres d'Aventure - {kpi['Annee']}")
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Emissions Totales", f"{kpi['Total_CO2']/1000:,.0f} tCO2e")
    c2.metric("Intensité Carbone", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f} kg/pax")
    c3.metric("Taux Sans Avion", f"{(df_dest['Nb_Pax_Sans_Aérien'].sum()/kpi['Nb_Pax_Total'])*100:.1f} %")
    
    # Export PDF
    pdf_data = generate_pdf(kpi, df_dest)
    c4.download_button("📄 Rapport PDF", pdf_data, "Rapport_Carbone_Terdav.pdf", "application/pdf")

    st.markdown("---")

    # --- ONGLETS ---
    tab1, tab2, tab3 = st.tabs(["📊 Analyse par Pays", "✈️ Détail des Vols", "🔍 Table de Données"])

    with tab1:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Top 10 : Part Aérien vs Terrestre")
            top_10 = df_dest.sort_values("CO2_Total", ascending=False).head(10)
            fig_stack = px.bar(top_10, x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                               title="kgCO2e par destination",
                               color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#457B9D"},
                               barmode="stack")
            st.plotly_chart(fig_stack, use_container_width=True)

        with col_right:
            st.subheader("Matrice Volume Pax vs Intensité")
            fig_scatter = px.scatter(df_dest[df_dest['Nb_Pax_Total'] > 50], 
                                     x="Nb_Pax_Total", y="CO2_Total", 
                                     size="CO2_Total", color="Pays",
                                     log_x=True, title="Impact par pays (Log Scale)")
            st.plotly_chart(fig_scatter, use_container_width=True)

    with tab2:
        st.subheader("Analyse granulaire des segments de vols")
        st.dataframe(df_vols, use_container_width=True)
        
        fig_dist = px.histogram(df_vols, x="Distance Km", y="Kg_CO2", 
                                title="Distribution des émissions par distance",
                                color_discrete_sequence=["#1D3557"])
        st.plotly_chart(fig_dist, use_container_width=True)

    with tab3:
        st.subheader("Base de données complète")
        st.write("Ce tableau regroupe les données fusionnées pour audit.")
        st.dataframe(df_dest, use_container_width=True)

else:
    # Message si aucun fichier n'est chargé
    st.info("👋 Bienvenue ! Veuillez télécharger le template dans la barre latérale, le remplir avec vos données, puis l'importer ici pour générer le dashboard.")
    
    # Illustration du processus
    st.markdown("""
    ### Comment utiliser cet outil ?
    1. **Téléchargez** le fichier `Template_Terdav_Carbone.xlsx`.
    2. **Remplissez** les onglets (KPI, Destinations, Vols).
    3. **Glissez-déposez** le fichier dans la zone d'importation à gauche.
    4. **Analysez** vos données et **Exportez** votre rapport PDF.
    """)
