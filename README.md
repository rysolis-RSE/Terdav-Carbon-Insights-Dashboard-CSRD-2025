# Terdav-Carbon-Insights-Dashboard-CSRD-2025
# 🌍 Dashboard Carbone CSRD - Terres d'Aventure

Ce projet est un outil d'analyse et de visualisation des émissions de Gaz à Effet de Serre (GES) pour le secteur du voyage. Il a été conçu pour automatiser le reporting carbone Scope 3 (ESRS E1) de Terres d'Aventure.

## 🚀 Fonctionnalités
- **Universalité** : Fonctionne avec n'importe quel jeu de données via un template Excel standardisé.
- **Analyse Mixte** : Distinction nette entre l'impact des vols (Air) et l'impact local (Terrestre).
- **Export PDF** : Génération d'un rapport de synthèse automatique.
- **Visualisations Interactives** : Analyse de l'intensité carbone et des segments de vols.

## 🛠️ Installation
1. Installez les dépendances : `pip install -r requirements.txt`
2. Lancez l'application : `streamlit run app.py`

## 📊 Pipeline de données (ETL)
L'outil suit une logique ETL (Extract, Transform, Load) :
1. **Extract** : Récupération des données ERP/Vols.
2. **Transform** : Nettoyage et fusion via le template.
3. **Load** : Visualisation dynamique sur Streamlit.



---
*Développé dans le cadre d'un stage RSE à Terres d'Aventure.*
