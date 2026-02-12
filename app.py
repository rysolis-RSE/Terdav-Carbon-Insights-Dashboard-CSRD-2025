import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Dashboard Carbone Universel", layout="wide", page_icon="🌍")

# --- FONCTION 1 : GÉNÉRER LE TEMPLATE VIDE EN MÉMOIRE ---
def get_template_data():
    output = io.BytesIO()
    # On utilise xlsxwriter pour créer un fichier Excel sans le sauvegarder sur le disque
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Onglet 1 : KPI
        pd.DataFrame(columns=['Annee', 'Total_CO2', 'Nb_Pax_Total']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
        # Onglet 2 : Destinations
        pd.DataFrame(columns=['Pays', 'CO2_Aerien', 'CO2_Terrestre', 'CO2_Total']).to_excel(writer, sheet_name='Destinations', index=False)
        # Onglet 3 : Vols
        pd.DataFrame(columns=['Date', 'Trajet', 'Distance_Km', 'Kg_CO2']).to_excel(writer, sheet_name='Details_Vols', index=False)
    return output.getvalue()

# --- FONCTION 2 : GÉNÉRER LE PDF ---
def create_pdf(annee, total_co2, pax):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Rapport Carbone {annee}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(190, 10, f"Total Emissions : {total_co2/1000:,.1f} tCO2e", ln=True)
    pdf.cell(190, 10, f"Nombre de Voyageurs : {pax:,.0f}", ln=True)
    if pax > 0:
        pdf.cell(190, 10, f"Intensite : {total_co2/pax:.1f} kgCO2e/pax", ln=True)
    return pdf.output(dest="S").encode("latin-1")

# --- INTERFACE UTILISATEUR ---

# 1. Barre Latérale : Téléchargement & Upload
st.sidebar.header("1. Données")

# Bouton pour télécharger le template vide
st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=get_template_data(),
    file_name="Template_Carbone.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    help="Cliquez pour obtenir le fichier Excel vierge à remplir."
)

st.sidebar.markdown("---")

# Zone d'upload
uploaded_file = st.sidebar.file_uploader("📂 Importer votre fichier rempli", type=["xlsx"])

# 2. Page Principale
if uploaded_file:
    try:
        # Lecture des onglets
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        
        # Récupération des chiffres clés
        if not df_kpi.empty:
            annee = int(df_kpi['Annee'].iloc[0]) if 'Annee' in df_kpi.columns else 2025
            total_co2 = df_kpi['Total_CO2'].iloc[0]
            total_pax = df_kpi['Nb_Pax_Total'].iloc[0]
            
            # --- AFFICHAGE DASHBOARD ---
            st.title(f"🌍 Analyse Carbone {annee}")
            
            # KPIs
            c1, c2, c3 = st.columns(3)
            c1.metric("Émissions Totales", f"{total_co2/1000:,.0f} tCO2e")
            c2.metric("Voyageurs", f"{total_pax:,.0f}")
            c3.metric("Intensité", f"{total_co2/total_pax:.0f} kg/pax" if total_pax > 0 else "0")
            
            # Bouton PDF
            pdf_data = create_pdf(annee, total_co2, total_pax)
            st.download_button("📄 Télécharger le Rapport PDF", pdf_data, "Rapport_RSE.pdf", "application/pdf")
            
            st.markdown("---")
            
            # Graphique
            if not df_dest.empty and 'Pays' in df_dest.columns:
                st.subheader("Répartition Aérien vs Terrestre")
                df_dest_sorted = df_dest.sort_values("CO2_Total", ascending=False).head(15)
                fig = px.bar(
                    df_dest_sorted, 
                    x="Pays", 
                    y=["CO2_Aerien", "CO2_Terrestre"],
                    title="Top 15 Destinations (kgCO2e)",
                    color_discrete_map={"CO2_Aerien": "#E63946", "CO2_Terrestre": "#2A9D8F"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("L'onglet 'Destinations' est vide ou mal formaté.")
        else:
            st.error("L'onglet 'KPI_Globaux' est vide.")
            
    except Exception as e:
        st.error(f"Une erreur est survenue lors de la lecture du fichier : {e}")
        st.info("Assurez-vous d'utiliser le Template fourni via le bouton dans la barre latérale.")

else:
    # Page d'accueil (Mode "Attente")
    st.title("🚀 Outil de Pilotage Carbone")
    st.markdown("""
    ### Mode d'emploi :
    1. **Téléchargez** le modèle Excel vide via le bouton dans le menu de gauche.
    2. **Remplissez** les onglets avec vos données (KPIs, Destinations...).
    3. **Déposez** le fichier rempli dans la zone "Importer".
    
    *Aucune donnée n'est stockée sur le serveur. Tout est traité en mémoire.*
    """)
