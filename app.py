import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Terdav Carbon Analytics", layout="wide", page_icon="🌍")

# --- STYLE CSS POUR LE LOOK PRO ---
st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #eee; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f1f1f1; border-radius: 5px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTION EXPORT PDF (CORRIGÉE) ---
def generate_pdf(kpi, df_dest):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(190, 10, "Rapport Carbone - Terres d'Aventure", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "1. Indicateurs Globaux", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.cell(190, 8, f"- Total Emissions : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
        pdf.cell(190, 8, f"- Nombre de Voyageurs : {kpi['Nb_Pax_Total']:,.0f}", ln=True)
        pdf.cell(190, 8, f"- Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f} kgCO2e/pax", ln=True)
        
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(190, 10, "2. Top Destinations (Impact CO2)", ln=True)
        pdf.set_font("Arial", "", 10)
        top_5 = df_dest.sort_values("CO2_Total", ascending=False).head(5)
        for i, row in top_5.iterrows():
            pdf.cell(190, 7, f"- {row['Pays']} : {row['CO2_Total']/1000:,.1f} tCO2e", ln=True)
            
        return pdf.output(dest="S").encode("latin-1")
    except Exception as e:
        return str(e)

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/fr/6/69/Logo_Terres_d_Aventure.png", width=150)
    st.title("Outil CSRD")
    
    # 1. BOUTON TÉLÉCHARGEMENT DU TEMPLATE
    st.subheader("1. Préparation")
    try:
        with open("Bilan_Carbone_Database.xlsx", "rb") as file:
            st.download_button(
                label="📥 Télécharger le Template Excel",
                data=file,
                file_name="Template_Terdav_Carbone.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except FileNotFoundError:
        st.warning("⚠️ Template 'Bilan_Carbone_Database.xlsx' non trouvé à la racine.")

    st.markdown("---")
    
    # 2. UPLOAD DU FICHIER
    st.subheader("2. Analyse")
    uploaded_file = st.file_uploader("Importer le fichier Excel rempli", type=["xlsx"])

# --- AFFICHAGE PRINCIPAL ---
if uploaded_file:
    try:
        # Lecture des onglets
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        df_vols = pd.read_excel(xls, 'Details_Vols')
        
        kpi = df_kpi.iloc[0]

        st.title(f"🌍 Analyse Carbone {int(kpi['Annee'])}")
        
        # METRICS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total tCO2e", f"{kpi['Total_CO2']/1000:,.0f}")
        m2.metric("Intensité (kg/pax)", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.0f}")
        m3.metric("Voyageurs", f"{kpi['Nb_Pax_Total']:,.0f}")
        
        # PDF BUTTON
        pdf_data = generate_pdf(kpi, df_dest)
        if isinstance(pdf_data, bytes):
            m4.download_button("📄 Rapport PDF", pdf_data, "Rapport_Terdav.pdf", "application/pdf")
        else:
            m4.error("Erreur PDF")

        st.markdown("---")

        # ONGLETS
        t1, t2, t3 = st.tabs(["📊 Destinations", "✈️ Détail Vols", "📂 Données Brutes"])
        
        with t1:
            col_a, col_b = st.columns(2)
            with col_a:
                top_10 = df_dest.sort_values("CO2_Total", ascending=False).head(10)
                fig_bar = px.bar(top_10, x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                                 title="Répartition Air vs Terrestre (kgCO2)",
                                 color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#457B9D"},
                                 barmode="stack")
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_b:
                fig_pax = px.pie(df_dest.head(10), values='Nb_Pax_Total', names='Pays', title="Répartition des Pax (Top 10)")
                st.plotly_chart(fig_pax, use_container_width=True)

        with t2:
            st.dataframe(df_vols, use_container_width=True)

        with t3:
            st.dataframe(df_dest, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
        st.info("Vérifiez que votre Excel contient bien les onglets : 'KPI_Globaux', 'Destinations', 'Details_Vols'.")
else:
    # Page d'accueil si pas de fichier
    st.title("🚀 Bienvenue sur l'outil Carbone Terdav")
    st.info("Pour commencer, utilisez la barre latérale pour télécharger le template et importer vos données.")
    
    # Simulation visuelle pour le GitHub
    st.image("https://streamlit.io/images/brand/streamlit-logo-secondary-colormark-darktext.png", width=200)
    st.markdown("""
    ### Manuel d'utilisation :
    1. **Téléchargez le Template** (bouton à gauche).
    2. **Remplissez les colonnes** dans Excel.
    3. **Glissez le fichier** dans la zone 'File Uploader'.
    4. **Consultez vos résultats** et téléchargez le rapport PDF officiel.
    """)
