import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Outil de Reporting Carbone CSRD", layout="wide", page_icon="🌍")

# --- 2. GÉNÉRATION DU TEMPLATE VIDE (En mémoire) ---
def create_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Onglet KPI
        pd.DataFrame(columns=['Annee', 'Total_CO2', 'Part_Aerien', 'Part_Terrestre', 'Part_Salaries', 'Nb_Pax_Total']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
        # Onglet Destinations
        pd.DataFrame(columns=['Pays', 'CO2_Total', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre', 'Nb_Pax_Aérien', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='Destinations', index=False)
        # Onglet Vols
        pd.DataFrame(columns=['Date Dep', 'Pays', 'Trajet', 'Type', 'Distance Km', 'Kg_CO2']).to_excel(writer, sheet_name='Details_Vols', index=False)
    return output.getvalue()

# --- 3. FONCTION EXPORT PDF ---
def generate_pdf(kpi, df_dest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Rapport d'Analyse Carbone Automatique", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Total des Emissions : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 10, f"Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f} kgCO2e/pax", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- 4. INTERFACE LATÉRALE ---
st.sidebar.title("🛠️ Configuration")
st.sidebar.markdown("### 1. Préparer vos données")

# Bouton pour télécharger le template vide
template_data = create_template()
st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=template_data,
    file_name="Template_Carbone_Agnostique.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Analyser")
uploaded_file = st.sidebar.file_uploader("Importer votre fichier rempli (Excel)", type=["xlsx"])

# --- 5. LOGIQUE PRINCIPALE ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        df_vols = pd.read_excel(xls, 'Details_Vols')
        
        kpi = df_kpi.iloc[0]
        st.title(f"🌍 Analyse Carbone - {int(kpi['Annee'])}")

        # Affichage des KPIs
        c1, c2, c3 = st.columns(3)
        c1.metric("Total tCO2e", f"{kpi['Total_CO2']/1000:,.0f}")
        c2.metric("Passagers", f"{kpi['Nb_Pax_Total']:,.0f}")
        
        # Bouton PDF
        pdf_bytes = generate_pdf(kpi, df_dest)
        c3.download_button("📄 Exporter en PDF", pdf_bytes, "Rapport_Carbone.pdf", "application/pdf")

        st.markdown("---")
        
        # Graphiques
        tab1, tab2 = st.tabs(["📊 Destinations", "✈️ Détail Vols"])
        with tab1:
            fig = px.bar(df_dest.sort_values("CO2_Total", ascending=False).head(10), 
                         x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                         title="Impact par destination (Air vs Terrestre)",
                         barmode="stack", color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#457B9D"})
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            st.dataframe(df_vols, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur : Le fichier ne correspond pas au template. {e}")
else:
    # Page de bienvenue (si pas de fichier)
    st.title("🚀 Outil de Reporting Carbone Universel")
    st.info("👈 Pour commencer, téléchargez le template à gauche, remplissez-le et importez-le.")
    st.markdown("""
    ### Pourquoi cet outil ?
    - **Confidentialité** : Vos données restent sur votre ordinateur, seule l'analyse est faite ici.
    - **Standardisation** : Utilise les colonnes nécessaires au reporting **CSRD (ESRS E1)**.
    - **Rapidité** : Générez vos graphiques et votre rapport PDF en 2 secondes.
    """)
