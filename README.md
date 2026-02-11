# Terdav-Carbon-Insights-Dashboard-CSRD-2025
🌍 Dashboard de Pilotage Carbone & CSRD - Terres d'Aventure
📌 Présentation du Projet
Ce projet a été développé dans le cadre de mon stage au département RSE de Terres d'Aventure. L'objectif est d'automatiser le suivi de l'empreinte carbone (Scope 3) pour répondre aux exigences de la directive européenne CSRD, plus précisément la norme ESRS E1 (Changement Climatique).

L'application transforme des données complexes issues de multiples sources (Aérien, Terrestre, Salariés) en un outil d'aide à la décision interactif.

🚀 Fonctionnalités Clés
Fusion Multidimensionnelle : Consolidation automatique des données de vols (VVA) et des prestations terrestres par pays.

Indicateurs d'Intensité : Calcul dynamique du ratio kgCO2e / Passager pour identifier les destinations prioritaires pour la décarbonation.

Suivi du Report Modal : Analyse de la part des voyageurs optant pour des solutions "Sans Aérien".

Explorateur de Vols : Détail granulaire des segments de vols pour optimiser les plans de transport.

Reporting Collaborateurs : Suivi des émissions liées aux déplacements professionnels internes.

🛠️ Stack Technique
Langage : Python 3.x

Traitement de données : Pandas (Nettoyage, ETL, Fusion de fichiers complexes).

Visualisation : Plotly (Graphiques interactifs) & Streamlit (Interface Web).

Source de données : Fichiers Excel/CSV multi-sources (Bilan Global, Segments Vols, Pax Terrestre).

📊 Pipeline de Données (ETL)
Le projet repose sur un pipeline automatisé qui assure la fiabilité des chiffres :

Extraction : Récupération des données brutes (extraits ERP/Comptabilité).

Transformation : Standardisation des noms de pays, conversion des unités, et intégration des facteurs d'émission ADEME 2025.

Chargement : Génération d'une base de données maîtresse (Bilan_Carbone_Database.xlsx) optimisée pour le dashboard.

💻 Installation et Utilisation
Cloner le dépôt :

Bash
git clone https://github.com/ton-username/terdav-carbon-dashboard.git
Installer les dépendances :

Bash
pip install -r requirements.txt
Lancer l'application :

Bash
streamlit run app.py
📈 Impact RSE
Cet outil permet à Terres d'Aventure de :

Réduire le temps de production du bilan carbone annuel de plusieurs jours à quelques minutes.

Visualiser précisément l'impact du séjour sur place vs le vol international.

Piloter la stratégie de décarbonation avec des données fiables et auditables.
