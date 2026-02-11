import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal Carbon Dashboard", layout="wide", page_icon="🌍")

# --- FONCTION EXPORT PDF ---
def generate_pdf(kpi, df_dest):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Rapport d'Analyse Carbone Automatique", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"Bilan de la Periode", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(190, 8, f"- Emissions Totales : {kpi['Total_CO2']/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 8, f"- Nombre de Voyageurs : {kpi['Nb_Pax_Total']:,.0f}", ln=True)
    pdf.cell(190, 8, f"- Intensite : {kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f} kgCO2e/pax", ln=True)
    
    return pdf.output(dest="S").encode("latin-1")

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Outil Universel")

# Option 1 : Télécharger le template vide (on crée l'excel à la volée s'il n'existe pas)
st.sidebar.subheader("1. Préparer les données")
# Création d'un template vide en mémoire pour le téléchargement
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
    pd.DataFrame(columns=['Annee', 'Total_CO2', 'Part_Aerien', 'Part_Terrestre', 'Part_Salaries', 'Nb_Pax_Total']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
    pd.DataFrame(columns=['Pays', 'CO2_Total', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre', 'Nb_Pax_Aérien', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='Destinations', index=False)
    pd.DataFrame(columns=['Date Dep', 'Pays', 'Trajet', 'Type', 'Distance Km', 'Kg_CO2']).to_excel(writer, sheet_name='Details_Vols', index=False)
    writer.close()

st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=buffer.getvalue(),
    file_name="Template_Carbone_Vide.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.markdown("---")

# Option 2 : Importer les données
st.sidebar.subheader("2. Importer vos données")
uploaded_file = st.sidebar.file_uploader("Glissez votre fichier Excel ici", type=["xlsx"])

# --- AFFICHAGE PRINCIPAL ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        df_vols = pd.read_excel(xls, 'Details_Vols')

        kpi = df_kpi.iloc[0]

        st.title(f"📊 Dashboard d'Analyse - {int(kpi['Annee'])}")

        # KPIS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total tCO2e", f"{kpi['Total_CO2']/1000:,.1f}")
        c2.metric("Passagers", f"{kpi['Nb_Pax_Total']:,.0f}")
        c3.metric("kgCO2 / Pax", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f}")
        
        # Export PDF
        pdf_bytes = generate_pdf(kpi, df_dest)
        c4.download_button("📄 Rapport PDF", pdf_bytes, "Rapport_Analytique.pdf", "application/pdf")

        st.markdown("---")

        # Graphiques
        t1, t2 = st.tabs(["🗺️ Analyse Géographique", "✈️ Détails Aérien"])
        
        with t1:
            st.subheader("Répartition de l'impact par destination")
            fig = px.bar(df_dest.sort_values("CO2_Total", ascending=False).head(15), 
                         x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                         title="Comparaison Vol vs Terrestre", barmode="stack",
                         color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#457B9D"})
            st.plotly_chart(fig, use_container_width=True)

        with t2:
            st.subheader("Analyse des segments de vols")
            st.dataframe(df_vols, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur de format : {e}")
        st.info("Assurez-vous d'utiliser le template fourni sans modifier le nom des colonnes.")

else:
    # PAGE D'ACCUEIL (Quand l'app est vide)
    st.title("🚀 Outil de Reporting Carbone Universel")
    st.markdown("""
    Bienvenue dans votre outil d'analyse carbone. Cette application est conçue pour fonctionner avec **n'importe quel jeu de données**.
    
    ### Comment ça marche ?
    1. **Téléchargez le template** vide depuis la barre latérale.
    2. **Remplissez-le** avec vos propres données (Excel).
    3. **Ré-importez-le** ici pour générer instantanément vos graphiques et votre rapport PDF.
    
    *Idéal pour les bilans carbone annuels, le suivi CSRD et les présentations stratégiques.*
    """)
    st.info("👈 Commencez par télécharger le template à gauche.")
