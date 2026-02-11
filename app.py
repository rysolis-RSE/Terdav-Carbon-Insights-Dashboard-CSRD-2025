import streamlit as st

# --- ÉTAPE 0 : VÉRIFICATION DES INSTALLATIONS (Pour débugger) ---
try:
    import pandas as pd
    import plotly.express as px
    from fpdf import FPDF
    import io
    import xlsxwriter
except ImportError as e:
    st.error(f"❌ Erreur de déploiement : La bibliothèque '{e.name}' est manquante.")
    st.info("Vérifiez que vous avez bien créé le fichier 'requirements.txt' sur GitHub avec : pandas, streamlit, plotly, openpyxl, xlsxwriter, fpdf2")
    st.stop()

# --- CONFIGURATION ---
st.set_page_config(page_title="Carbon Tool", layout="wide")

# --- FONCTION GÉNÉRATION TEMPLATE VIDE ---
def create_empty_template():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.DataFrame(columns=['Annee', 'Total_CO2', 'Part_Aerien', 'Part_Terrestre', 'Part_Salaries', 'Nb_Pax_Total']).to_excel(writer, sheet_name='KPI_Globaux', index=False)
        pd.DataFrame(columns=['Pays', 'CO2_Total', 'Nb_Pax_Total', 'CO2_Aerien', 'CO2_Terrestre', 'Nb_Pax_Aérien', 'Nb_Pax_Sans_Aérien']).to_excel(writer, sheet_name='Destinations', index=False)
        pd.DataFrame(columns=['Date Dep', 'Pays', 'Trajet', 'Type', 'Distance Km', 'Kg_CO2']).to_excel(writer, sheet_name='Details_Vols', index=False)
    return output.getvalue()

# --- BARRE LATÉRALE ---
st.sidebar.title("🛠️ Configuration")
st.sidebar.markdown("### 1. Préparer vos données")

template_bytes = create_empty_template()
st.sidebar.download_button(
    label="📥 Télécharger le Template Vide",
    data=template_bytes,
    file_name="Template_Carbone_Vide.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 2. Analyser")
uploaded_file = st.sidebar.file_uploader("Importer votre fichier Excel rempli", type=["xlsx"])

# --- CORPS DE L'APP ---
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        df_kpi = pd.read_excel(xls, 'KPI_Globaux')
        df_dest = pd.read_excel(xls, 'Destinations')
        
        kpi = df_kpi.iloc[0]
        st.title(f"🌍 Bilan Carbone - {int(kpi['Annee'])}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Total tCO2e", f"{kpi['Total_CO2']/1000:,.0f}")
        c2.metric("Passagers", f"{kpi['Nb_Pax_Total']:,.0f}")
        c3.metric("Intensité", f"{kpi['Total_CO2']/kpi['Nb_Pax_Total']:.1f} kg/pax")

        st.markdown("---")
        
        fig = px.bar(df_dest.sort_values("CO2_Total", ascending=False).head(10), 
                     x="Pays", y=["CO2_Aerien", "CO2_Terrestre"],
                     title="Répartition par Destination", barmode="stack")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse du fichier : {e}")
        st.info("Utilisez bien le template fourni sans changer le nom des colonnes.")
else:
    st.title("🚀 Outil de Reporting Carbone Universel")
    st.info("👈 Votre application est prête ! Utilisez le menu à gauche pour télécharger le template et importer vos données.")
    st.markdown("""
    ### Pourquoi c'est vide ?
    Comme vous ne souhaitez pas mettre vos données confidentielles sur GitHub, l'application attend que vous lui fournissiez votre fichier Excel localement.
    
    1. Téléchargez le **Template Vide** à gauche.
    2. Remplissez-le avec vos données Terdav.
    3. Importez-le : les graphiques apparaîtront instantanément.
    """)
