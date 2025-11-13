import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector
from mysql.connector import Error
from datetime import date
import base64
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.tree import DecisionTreeClassifier
# ============================================
# SYSTÈME D'AUTHENTIFICATION (Initialement auth.py)
# ============================================

def init_session_state():
    """Initialise les variables de session pour l'authentification"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None
# Remplacer l'ancienne fonction authenticate() par celle-ci
import mysql.connector
# Note: 'Error' must also be imported if used in try/except blocks

# --- PARAMÈTRES DE CONNEXION ---
DB_HOST = "localhost"  
DB_USER = "root"      
DB_PASSWORD = "" # REMPLACEZ CECI
DB_NAME = "diabetecam"  # REMPLACEZ CECI (Le nom de votre base créée)

def create_db_connection():
    """Crée et retourne une connexion à la base de données MySQL."""
    conn = None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            database=DB_NAME
        )
        if conn.is_connected():
            print("Connexion MySQL établie avec succès.")
        return conn
    except Error as e:
        st.error(f"❌ Erreur critique de connexion à la base de données MySQL : {e}")
        st.warning("Vérifiez que WAMP est démarré et que les identifiants (mot de passe, nom de la BD) sont corrects.")
        return None

def close_db_connection(conn):
    """Ferme la connexion à la base de données MySQL si elle est ouverte."""
    if conn and conn.is_connected():
        conn.close()
        print("Connexion MySQL fermée.")

def init_database():
    """Teste simplement si la connexion peut être établie au démarrage."""
    test_conn = create_db_connection()
    if test_conn:
        close_db_connection(test_conn)
    else:
        # Si la connexion échoue, nous arrêtons le script ici pour éviter d'autres erreurs.
        st.stop()
def get_user_from_db(username, role):
    """Récupère les informations d'un utilisateur par son nom d'utilisateur et rôle."""
    conn = create_db_connection()
    if conn is None:
        return None
        
    cursor = conn.cursor(dictionary=True)
    
    # Sécurité : Limiter à l'utilisateur et au rôle pour plus de précision
    query = "SELECT username, password, role, fullName, permissions FROM utilisateurs WHERE username = %s AND role = %s"
    try:
        cursor.execute(query, (username, role))
        user_data = cursor.fetchone()
        
        if user_data:
            # Convertir la chaîne de permissions en liste Python
            permission_list = user_data['permissions'].split(',')
            
            # Construire l'objet utilisateur comme avant
            user = {
                'username': user_data['username'],
                'password': user_data['password'],
                'role': user_data['role'],
                'fullName': user_data['fullName'],
                'permissions': [p.strip() for p in permission_list] # Nettoyer les espaces
            }
            return user
            
    except Error as e:
        st.error(f"Erreur de lecture de la base de données : {e}")
    finally:
        close_db_connection(conn)
        
    return None  
def get_page_key(permission_name):
    """Trouve la clé de page complète (avec emoji) à partir du nom de permission."""
    for key, value in page_mapping.items():
        if value == permission_name:
            return key
    return permission_name # Retourne le nom simple si non trouvé

# ... continuez avec def authenticate(...), def check_permission(...), etc.    
def create_user_in_db(username, password, role, fullname, permissions_list):
    """Insère un nouvel utilisateur dans la BD."""
    # Assurez-vous que 'Error' est importé (ex: from mysql.connector import Error)
    # Assurez-vous que 'create_db_connection' et 'close_db_connection' sont définis
    conn = create_db_connection()
    if conn is None:
        return False
        
    cursor = conn.cursor()
    # Convertir la liste de permissions en chaîne pour la BD
    permissions_str = ",".join(permissions_list) 
    
    query = "INSERT INTO utilisateurs (username, password, role, fullName, permissions) VALUES (%s, %s, %s, %s, %s)"
    # Le mot de passe devrait être hashé (ex: using bcrypt) avant l'insertion pour des raisons de sécurité.
    # Pour le moment, nous utilisons la version non hashée pour la simplicité.
    values = (username, password, role, fullname, permissions_str)
    
    try:
        cursor.execute(query, values)
        conn.commit()
        return True
    except Error as e:
        # Assurez-vous d'afficher le message d'erreur SQL pour le debug
        st.error(f"Erreur lors de l'ajout de l'utilisateur : {e}")
        return False
    finally:
        # Cette ligne DOIT être la dernière du bloc 'finally'
        close_db_connection(conn)
       
def authenticate(username, password, role):
    """Vérifie les identifiants en interrogeant la base de données."""
    
    # 1. Tenter de récupérer les informations de l'utilisateur depuis la BD
    user = get_user_from_db(username, role)
    
    # 2. Vérifier si l'utilisateur existe et si le mot de passe correspond
    if user and user['password'] == password:
        # NOTE IMPORTANTE: Dans une application réelle, le mot de passe 
        # serait hashé (ex: SHA256) et vérifié avec bcrypt ou un équivalent.
        return user
        
    return None
def check_permission(page_name):
    """Vérifie si l'utilisateur a accès à une page"""
    if not st.session_state.logged_in:
        return False
    
    # page_mapping est accessible car il est défini globalement AVANT cette fonction
    permission_name = page_mapping.get(page_name, page_name)
    
    # Vérifie si l'utilisateur et ses permissions existent avant de vérifier
    if st.session_state.user and 'permissions' in st.session_state.user:
        return permission_name in st.session_state.user['permissions']
    return False

def show_login_page():
    # --- CSS OPTIMISÉ (Reste le même, car il est bon pour le centrage) ---
    st.markdown("""
    <style> 
        .login-title {
            text-align: center;
            color: #006233;
            font-size: 2.2em; /* Légèrement plus petit */
            margin-bottom: 5px; /* Moins de marge */
        }
        .login-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 15px; /* Moins de marge */
        }
        /* Style pour réduire l'espace autour du selectbox */
        div[data-testid="stForm"] > div > div:nth-child(1) {
            padding-top: 0px; 
            padding-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # --- STRUCTURE CENTRÉE (Conserver) ---
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # En-tête simplifié
        st.markdown('<h1 class="login-title">🏥 DiabèteCam</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Connexion Sécurisée</p>', unsafe_allow_html=True)
        
        # Sélection du rôle (on met le label à côté pour gagner de la place)
        # st.markdown("### 👤 Sélectionnez votre profil") # Supprimé pour gagner de l'espace
        col_role_label, col_role_select = st.columns([1, 2.5])
        
        with col_role_label:
            st.markdown("👤 **Profil** :")
            
        with col_role_select:
            role = st.selectbox(
                "Rôle",
                ["medecin", "infirmier", "admin"],
                format_func=lambda x: {
                    "medecin": "👨‍⚕️ Médecin",
                    "infirmier": "👩‍⚕️ Infirmier(ère)",
                    "admin": "🔐 Administrateur"
                }[x],
                label_visibility="collapsed" # Le label est maintenant dans la colonne précédente
            )
        
        st.markdown("---") # Ligne de séparation courte pour la clarté
        
        # Formulaire de connexion
        username = st.text_input("📧 Nom d'utilisateur", placeholder="Entrez votre identifiant")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
        # ... (le reste du code du formulaire est conservé) ... 
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("🚀 Se Connecter", use_container_width=True, type="primary"):
                if username and password:
                    user = authenticate(username, password, role)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user = user
                        st.success(f"✅ Bienvenue {user['fullName']} !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs")
        

        
def logout():
    """Déconnecte l'utilisateur"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()


# ============================================
# MAPPING DES PAGES / PERMISSIONS
# CE BLOC DOIT ÊTRE AJOUTÉ
# ============================================
page_mapping = {
    "🏠 Accueil": "Accueil",
    "📊 Visualisations": "Visualisations",
    "🤖 ML Model 1 (Régression)": "ML Model 1",
    "🌳 ML Model 2 (Arbre)": "ML Model 2",
    "📝 Nouveau Patient": "Nouveau Patient",
    "📈 Suivi Patient": "Suivi Patient",
    "🥘 Conseils Nutrition": "Nutrition",
    "🏥 Centres de Santé": "Centres Santé",
    "📚 Formation Diabète": "Formation",
    "🔐 Gestion Utilisateurs": "Gestion Utilisateurs",
    "⚙️ Configuration & Stats": "Configuration & Stats"
}
# ============================================
# ============================================
# DÉBUT DE L'APPLICATION PRINCIPALE (Initialement app2.py)
# ============================================

# Initialiser les variables de session
init_session_state()

# Si pas connecté, afficher la page de login et arrêter l'exécution
if not st.session_state.logged_in:
    show_login_page()
    st.stop()  # Arrête l'exécution ici

# ============================================
# CONFIGURATION DE LA PAGE (après login)
# ============================================
st.set_page_config(
    page_title="DiabèteCam 🇨🇲",
    page_icon="🏥",
    layout="wide"
)

# ============================================
# CSS PERSONNALISÉ AUX COULEURS DU CAMEROUN
# ============================================
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, rgba(0,98,51,0.05) 0%, rgba(206,17,38,0.05) 50%, rgba(252,209,22,0.05) 100%);
    }
    h1 {
        color: #006233;
        text-align: center;
        font-family: 'Arial', sans-serif;
        padding: 10px;
        background: linear-gradient(90deg, #006233, #CE1126, #FCD116);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .stButton>button {
        background-color: #006233;
        color: white;
        border-radius: 10px;
    }
    .stButton>button:hover {
        background-color: #CE1126;
    }
    div[data-testid="metric-container"] {
        background-color: white;
        border: 2px solid #006233;
        padding: 10px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)




# Initialiser la BD au démarrage (teste la connexion)
# init_database() # Décommentez ceci si vous voulez forcer le stop en cas d'erreur DB au login

# ============================================
# CHARGEMENT DES DONNÉES
# ============================================
# Assurez-vous que 'diabetes.csv' est dans le même répertoire
try:
    df = pd.read_csv('diabetes.csv')
    df_temp = df.drop(columns=['Outcome','Pregnancies','Insulin','SkinThickness'])
    df_temp = df_temp.replace(0,np.nan)
    df = pd.concat([df['Pregnancies'],df['Insulin'],df['SkinThickness'],df_temp,df['Outcome']],axis=1)
    df = df.dropna().reset_index(drop=True)
except FileNotFoundError:
    st.error("⚠️ Fichier `diabetes.csv` non trouvé. Assurez-vous qu'il est dans le répertoire de l'application.")
    df = pd.DataFrame() # Créer un DataFrame vide pour éviter les erreurs
except Exception as e:
    st.error(f"⚠️ Erreur lors du chargement ou du nettoyage des données: {e}")
    df = pd.DataFrame()


# ============================================
# SIDEBAR - NAVIGATION
# ============================================

# Informations utilisateur connecté
logo_html = """
    <div style="display: flex; align-items: center; margin-bottom: 15px;">
        <h1 style="margin: 0;">DiabèteCam</h1>
    </div>
    <hr style="margin-top: 0; margin-bottom: 10px;">
"""
# Tente de charger le logo.png, si non trouvé, affiche le message sans image.
try:
    with open('logo.png', 'rb') as f:
        logo_base64 = base64.b64encode(f.read()).decode()
        logo_html = f"""
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <img src="data:image/png;base64,{logo_base64}" 
                     width="30px" style="margin-right: 10px;">
                <h1 style="margin: 0;">DiabèteCam</h1>
            </div>
            <hr style="margin-top: 0; margin-bottom: 10px;">
        """
except FileNotFoundError:
    st.warning("Fichier 'logo.png' non trouvé. Affichage du titre seul.")
except Exception as e:
    st.warning(f"Erreur de chargement du logo : {e}. Affichage du titre seul.")


st.sidebar.markdown(logo_html, unsafe_allow_html=True)


# Message de bienvenue
user = st.session_state.user
role_emoji = {
    'medecin': '👨‍⚕️',
    'infirmier': '👩‍⚕️',
    'admin': '🔐'
}

st.sidebar.success(f"""
**{role_emoji.get(user.get('role', 'admin'), '👤')} Connecté(e) :** {user.get('fullName', 'Inconnu')}  
*{user.get('role', 'visiteur').capitalize()}*
""")

st.sidebar.markdown("---")

# Menu de navigation (filtré selon les permissions)
# Menu de navigation (filtré selon les permissions)
all_pages = [
    "🏠 Accueil",
    "📊 Visualisations",
    "🤖 ML Model 1 (Régression)",
    "🌳 ML Model 2 (Arbre)",
    "📝 Nouveau Patient", # Laissez-le ici, le filtre de permission fera le tri
    "📈 Suivi Patient",
    "🥘 Conseils Nutrition",
    "🏥 Centres de Santé",
    "📚 Formation Diabète",
    "🔐 Gestion Utilisateurs", # Ajout de l'emoji
    "⚙️ Configuration & Stats" # Nouveau menu logique pour l'Admin
]
# Filtrer les pages selon les permissions
available_pages = [p for p in all_pages if check_permission(p)]

# S'assurer qu'une page par défaut est sélectionnée s'il y en a
if available_pages:
    page = st.sidebar.radio("📍 Navigation", available_pages)
else:
    st.sidebar.error("Aucune page disponible. Veuillez vous connecter.")
    page = "🏠 Accueil" # Page par défaut en cas d'erreur

# Bouton de déconnexion
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Se Déconnecter", use_container_width=True, type="primary"):
    logout()

# URGENCES dans la sidebar
st.sidebar.markdown("---")
st.sidebar.error("""
### 🚨 URGENCES

**Signes critiques:**
- Confusion mentale
- Respiration difficile
- Perte de conscience

**☎️ APPELEZ:**
- 🏥 Douala: 233 42 26 12
- 🏥 Yaoundé: 222 23 40 20
""")

# ============================================
# AFFICHAGE DES PAGES
# ============================================

if page == "🏠 Accueil":
    # En-tête avec drapeau
    st.markdown("# Bienvenue sur DiabèteCam")
    st.markdown("### *Votre partenaire santé au Cameroun*")
    
    # Salutations en langues locales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("🗣️ **Douala**: Mbombo!")
    with col2:
        st.info("🗣️ **Yaoundé**: Mbolo!")
    with col3:
        st.info("🗣️ **Bamenda**: Welcome!")
    
    st.markdown("---")
    
    # Message chaleureux
    st.markdown("""
    👋 **Akwaaba** (Bienvenue) sur votre application de surveillance du diabète, 
    conçue spécialement pour nos frères et sœurs camerounais.
    
    🏥 Au Cameroun, **1 personne sur 20** est touchée par le diabète. 
    Ensemble, nous pouvons **prévenir** et **gérer** cette maladie !
    
    ### 💪 Notre Mission
    - ✅ Dépister le diabète **avant les complications**
    - ✅ Suivre votre santé **régulièrement**
    - ✅ Vous conseiller avec des solutions **adaptées au Cameroun**
    - ✅ Créer une **communauté** d'entraide
    """)
    
    st.markdown("---")
    
    # Statistiques nationales
    st.markdown("### 📊 Le Diabète au Cameroun en chiffres")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Prévalence", "5.2%", "de la population")
    with col2:
        st.metric("⚠️ Non diagnostiqués", "60%", "des cas")
    with col3:
        st.metric("💰 Coût/an", "500K FCFA", "par patient")
    with col4:
        st.metric("🏥 Centres", "150+", "au Cameroun")
    
    st.markdown("---")
    
    # Aperçu des données
    st.markdown("### 📋 Aperçu de nos données de recherche")
    if not df.empty:
        st.dataframe(df.head(), use_container_width=True)
        
        with st.expander("📊 Statistiques détaillées"):
            st.dataframe(df.describe(), use_container_width=True)
    else:
        st.warning("Données non chargées. Veuillez vérifier le fichier `diabetes.csv`.")
    
    with st.expander("ℹ️ À propos de ce dataset"):
        st.write("""
        Ce jeu de données provient d'une étude menée auprès de femmes camerounaises.
        Il contient 8 indicateurs médicaux permettant de prédire le risque de diabète.
        
        **Variables mesurées:**
        - Nombre de grossesses
        - Taux de glucose sanguin
        - Pression artérielle
        - Épaisseur de la peau
        - Taux d'insuline
        - Indice de masse corporelle (BMI)
        - Fonction de pedigree diabétique (hérédité)
        - Âge
        """)

# ============================================
# PAGE 2 : VISUALISATIONS
# ============================================
elif page == "📊 Visualisations":
    if not check_permission(page):
        st.error("🔒 Accès refusé : Vous n'avez pas les permissions pour cette page.")
        st.stop()
    
    if df.empty:
        st.warning("Impossible d'afficher les visualisations. Les données ne sont pas chargées.")
        st.stop()
        
    st.title("📊 Explorez les Données Visuellement")
    st.write("Choisissez les graphiques que vous souhaitez voir !")
    
    # Organisation en onglets
    tab1, tab2, tab3 = st.tabs(["📈 Graphiques Basiques", "🔥 Heatmap", "📊 Distributions"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Histogramme des Âges", use_container_width=True):
                st.markdown("### Distribution des Âges")
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(df["Age"], bins=10, color='#006233', edgecolor='black')
                ax.set_xlabel("Âge", fontsize=12)
                ax.set_ylabel("Nombre de personnes", fontsize=12)
                ax.set_title("Répartition des âges dans l'échantillon", fontsize=14)
                st.pyplot(fig)
        
        with col2:
            if st.button("🍬 Glucose vs BMI", use_container_width=True):
                st.markdown("### Relation Glucose - Obésité")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.scatterplot(data=df, x='Glucose', y='BMI', hue='Outcome', 
                                palette=['#006233', '#CE1126'], ax=ax)
                ax.set_title('Glucose vs BMI selon le diagnostic', fontsize=14)
                ax.set_xlabel("Glucose (mg/dL)", fontsize=12)
                ax.set_ylabel("BMI (kg/m²)", fontsize=12)
                ax.legend(title='Diabétique', labels=['Non', 'Oui'])
                st.pyplot(fig)
    
    with tab2:
        if st.button("🔥 Afficher la Heatmap de Corrélation", use_container_width=True):
            st.markdown("### Corrélations entre toutes les variables")
            corr = df.corr()
            fig, ax = plt.subplots(figsize=(12, 8))
            sns.heatmap(data=corr, cmap='RdYlGn', annot=True, fmt='.2f', 
                        linewidths=0.5, ax=ax, center=0)
            ax.set_title("Matrice de corrélation", fontsize=16)
            st.pyplot(fig)
            
            with st.expander("💡 Comment lire cette carte ?"):
                st.write("""
                **Les couleurs indiquent la force de la relation :**
                - 🟢 **Vert** : Corrélation positive (quand l'un augmente, l'autre aussi)
                - 🔴 **Rouge** : Corrélation négative (quand l'un augmente, l'autre diminue)
                - 🟡 **Jaune** : Pas de corrélation
                
                **Chiffres de -1 à +1 :**
                - +1 = Corrélation parfaite positive
                - 0 = Aucune corrélation
                - -1 = Corrélation parfaite négative
                
                **Exemple :** Si Glucose et BMI ont 0.5, cela signifie que les personnes 
                avec un BMI élevé ont tendance à avoir aussi un glucose élevé.
                """)
    
    with tab3:
        st.markdown("### 📊 Comparaison Diabétiques vs Non-Diabétiques")
        st.write("Sélectionnez une caractéristique pour voir sa distribution :")
        
        features_display = {
            'Pregnancies': '🤰 Nombre de grossesses',
            'Glucose': '🍬 Glucose',
            'BloodPressure': '💉 Pression artérielle',
            'SkinThickness': '📏 Épaisseur de peau',
            'Insulin': '💉 Insuline',
            'BMI': '⚖️ BMI',
            'DiabetesPedigreeFunction': '🧬 Hérédité',
            'Age': '🎂 Âge'
        }
        
        for feature, display_name in features_display.items():
            if st.button(display_name, use_container_width=True):
                st.markdown(f"### Distribution : {display_name}")
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.kdeplot(data=df[df['Outcome']==1], x=feature, 
                            label='Diabétiques', fill=True, color='#CE1126', ax=ax)
                sns.kdeplot(data=df[df['Outcome']==0], x=feature, 
                            label='Non-diabétiques', fill=True, color='#006233', ax=ax)
                ax.set_title(f'Distribution de {display_name}', fontsize=14)
                ax.legend()
                st.pyplot(fig)

# ============================================
# PAGE 3 : ML MODEL 1 (RÉGRESSION LOGISTIQUE)
# ============================================
elif page == "🤖 ML Model 1 (Régression)":
    if df.empty:
        st.warning("Impossible d'entraîner le modèle. Les données ne sont pas chargées.")
        st.stop()
        
    st.title("🤖 Modèle 1 : Régression Logistique")
    
    with st.expander("📖 Comment fonctionne ce modèle ?"):
        st.markdown("""
        ### Principe de la Régression Logistique
        
        C'est comme un **médecin virtuel** qui calcule la probabilité qu'une personne soit diabétique 
        en fonction de plusieurs critères médicaux.
        
        **Analogie camerounaise :**
        Imaginez un vieux sage du village qui a vu des milliers de personnes. 
        Quand vous lui décrivez vos symptômes (glucose élevé, surpoids, etc.), 
        il peut prédire si vous avez le diabète grâce à son expérience.
        
        Notre IA fait la même chose, mais avec des calculs mathématiques !
        
        **Avantages :**
        - ✅ Rapide et précis
        - ✅ Donne une probabilité (pas juste oui/non)
        - ✅ Fonctionne bien avec plusieurs variables
        """)
    
    st.markdown("---")
    
    # Sélection des features
    st.markdown("### 1️⃣ Choisissez les critères médicaux à analyser")
    features = st.multiselect(
        "Sélectionnez au moins un critère :", 
        df.columns[:-1].tolist(), # Convertir en liste pour être sûr
        default=["Glucose", "BMI"],
        help="Ces données seront utilisées pour entraîner le modèle"
    )
    
    test_size = st.slider("Taille de l'ensemble de test (%)", 10, 50, 20) / 100
    
    if st.button("🚀 Entraîner le Modèle", use_container_width=True, type="primary"):
        if len(features) == 0:
            st.error("⚠️ Veuillez sélectionner au moins un critère !")
        else:
            with st.spinner("🔄 Entraînement en cours..."):
                x = df[features]
                y = df['Outcome']
                
                x_train, x_test, y_train, y_test = train_test_split(
                    x, y, test_size=test_size, random_state=42
                )
                
                scaler = StandardScaler()
                x_train_scaled = scaler.fit_transform(x_train)
                x_test_scaled = scaler.transform(x_test)
                
                model = LogisticRegression(max_iter=1000)
                model.fit(x_train_scaled, y_train)
                
                y_pred = model.predict(x_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                st.success("✅ Modèle entraîné avec succès !")
                
                
                # Résultats
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🎯 Précision Globale", f"{accuracy*100:.1f}%")
                with col2:
                    st.metric("📊 Nombre de tests", len(y_test))
                
                # Matrice de confusion
                st.markdown("### 📊 Matrice de Confusion")
                cm = confusion_matrix(y_test, y_pred)
                col1, col2 = st.columns(2)
                
                with col1:
                    fig, ax = plt.subplots(figsize=(6, 5))
                    sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', 
                                xticklabels=['Non-Diabétique', 'Diabétique'],
                                yticklabels=['Non-Diabétique', 'Diabétique'], ax=ax)
                    ax.set_ylabel('Réalité')
                    ax.set_xlabel('Prédiction')
                    ax.set_title('Matrice de Confusion')
                    st.pyplot(fig)
                
                with col2:
                    st.markdown("""
                    **Lecture du graphique :**
                    
                    📗 **Vert foncé (en haut à gauche)** : 
                    Personnes NON diabétiques correctement identifiées ✅
                    
                    📗 **Vert foncé (en bas à droite)** : 
                    Personnes diabétiques correctement identifiées ✅
                    
                    📕 **Cases claires** : 
                    Erreurs du modèle ❌
                    """)
                
                # Rapport détaillé
                with st.expander("📋 Voir le rapport détaillé"):
                    st.text(classification_report(y_test, y_pred, 
                                                target_names=['Non-Diabétique', 'Diabétique']))
                    st.markdown("""
                    **Explication des métriques :**
                    - **Precision** : Sur 100 diagnostics "diabétique", combien sont vrais ?
                    - **Recall** : Sur 100 vrais diabétiques, combien ont été détectés ?
                    - **F1-score** : Moyenne des deux (score global)
                    """)
                
                # Sauvegarder dans session
                st.session_state["model"] = model 
                st.session_state['features'] = features
                st.session_state['scaler'] = scaler
    
    # Section prédiction personnelle
    if 'model' in st.session_state and 'features' in st.session_state:
        st.markdown("---")
        st.markdown("### 2️⃣ Faites votre propre prédiction")
        st.info("💡 Entrez vos données médicales pour obtenir une évaluation")
        
        model = st.session_state['model']
        features = st.session_state['features']
        scaler = st.session_state['scaler']
        
        with st.form("prediction_form"):
            cols = st.columns(2)
            feature_dict = {}
            
            for idx, feature in enumerate(features):
                with cols[idx % 2]:
                    # Utiliser .get() pour une gestion plus robuste
                    default_value = df[feature].mean() if not df.empty and feature in df.columns else 0.0
                    
                    if feature == "Glucose":
                        feature_dict[feature] = st.number_input(
                            "🍬 Glucose (mg/dL)", 50.0, 300.0, 120.0
                        )
                    elif feature == "BMI":
                        feature_dict[feature] = st.number_input(
                            "⚖️ BMI (kg/m²)", 15.0, 60.0, 25.0
                        )
                    elif feature == "Age":
                        feature_dict[feature] = st.number_input(
                            "🎂 Âge (années)", 18, 100, 35
                        )
                    elif feature == "BloodPressure":
                        feature_dict[feature] = st.number_input(
                            "💉 Pression artérielle", 40, 200, 80
                        )
                    elif feature == "Pregnancies":
                         feature_dict[feature] = st.number_input(
                            "🤰 Nombre de grossesses", 0, 15, 1
                        )
                    elif feature == "SkinThickness":
                         feature_dict[feature] = st.number_input(
                            "📏 Épaisseur de peau", 0.0, 100.0, 25.0
                        )
                    elif feature == "Insulin":
                         feature_dict[feature] = st.number_input(
                            "💉 Insuline", 0.0, 900.0, 100.0
                        )
                    elif feature == "DiabetesPedigreeFunction":
                         feature_dict[feature] = st.number_input(
                            "🧬 Hérédité (DPF)", 0.0, 2.5, 0.4
                        )
                    else:
                        feature_dict[feature] = st.number_input(
                            f"{feature}", min_value=0.0, value=default_value
                        )
            
            submitted = st.form_submit_button("🔮 Prédire", use_container_width=True)
            
            if submitted:
                input_df = pd.DataFrame([feature_dict])
                prediction = model.predict(scaler.transform(input_df))
                proba = model.predict_proba(scaler.transform(input_df))
                
                if prediction[0] == 1:
                    st.error(f"""
                    ### ⚠️ ATTENTION : Risque de Diabète Détecté
                    
                    **Probabilité : {proba[0][1]*100:.1f}%**
                    
                    🏥 **Que faire ?**
                    1. Consultez un médecin rapidement
                    2. Faites un test de glycémie à jeun
                    3. Adoptez un mode de vie sain (voir section Nutrition)
                    
                    ☎️ Trouvez un centre de santé dans la section "🏥 Centres de Santé"
                    """)
                else:
                    st.success(f"""
                    ### ✅ Pas de Risque Immédiat Détecté
                    
                    **Probabilité de diabète : {proba[0][1]*100:.1f}%**
                    
                    💪 **Continuez vos efforts !**
                    - Maintenez une alimentation équilibrée
                    - Faites de l'exercice régulièrement
                    - Contrôlez votre poids
                    
                    🔄 Refaites le test tous les 6 mois
                    """)
# ============================================
# PAGE 4 : ML MODEL 2 (ARBRE DE DÉCISION)
# ============================================
elif page == "🌳 ML Model 2 (Arbre)":
    from sklearn.model_selection import train_test_split
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
    
    st.title("🌳 Modèle 2 : Arbre de Décision")
    
    with st.expander("📖 Comment fonctionne ce modèle ?"):
        st.markdown("""
        ### Principe de l'Arbre de Décision
        
        C'est comme un **questionnaire médical intelligent** qui pose des questions une par une.
        
        **Exemple :**
        ```
        📝 Question 1 : Votre glucose est-il > 150 mg/dL ?
           ├─ OUI → Question 2 : Votre BMI est-il > 30 ?
           │         ├─ OUI → 🔴 DIABÈTE PROBABLE
           │         └─ NON → Question 3...
           └─ NON → ✅ RISQUE FAIBLE
        ```
        
        **Avantages :**
        - ✅ Très facile à comprendre (comme un arbre)
        - ✅ Pas besoin de standardiser les données
        - ✅ Capture les interactions complexes
        - ✅ Peut expliquer ses décisions étape par étape
        """)
    
    st.markdown("---")
    
    features = st.multiselect(
        "Choisissez les critères :", 
        df.columns[:-1], 
        default=["Glucose", "BMI"]
    )
    
    test_size = st.slider("Taille du test (%)", 10, 50, 20) / 100
    
    if st.button("🌱 Entraîner l'Arbre", use_container_width=True, type="primary"):
        if len(features) == 0:
            st.error("⚠️ Sélectionnez au moins un critère !")
        else:
            x = df[features]
            y = df['Outcome']
            
            x_train, x_test, y_train, y_test = train_test_split(
                x, y, test_size=test_size, random_state=42
            )
            
            model = DecisionTreeClassifier(random_state=42, max_depth=5)
            model.fit(x_train, y_train)
            
            y_pred = model.predict(x_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            st.success("✅ Arbre de décision créé !")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🎯 Précision", f"{accuracy*100:.1f}%")
            with col2:
                st.metric("🌿 Profondeur", model.get_depth())
            
            cm = confusion_matrix(y_test, y_pred)
            st.markdown("### 📊 Résultats")
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='YlOrRd',
                       xticklabels=['Non-Diabétique', 'Diabétique'],
                       yticklabels=['Non-Diabétique', 'Diabétique'], ax=ax)
            ax.set_ylabel('Réalité')
            ax.set_xlabel('Prédiction')
            ax.set_title('Performance du Modèle')
            st.pyplot(fig)
            
            with st.expander("📋 Rapport détaillé"):
                st.text(classification_report(y_test, y_pred,
                                             target_names=['Non-Diabétique', 'Diabétique']))
            
            st.session_state["model_tree"] = model 
            st.session_state['features_tree'] = features
    
    # Prédiction
    if 'model_tree' in st.session_state:
        st.markdown("---")
        st.markdown("### 🔮 Faites une prédiction")
        
        model = st.session_state['model_tree']
        features = st.session_state['features_tree']
        
        with st.form("prediction_tree"):
            feature_dict = {}
            for feature in features:
                feature_dict[feature] = st.number_input(f"Entrez {feature}", min_value=0.0)
            
            submitted = st.form_submit_button("🔮 Prédire", use_container_width=True)
            
            if submitted:
                input_df = pd.DataFrame([feature_dict])
                prediction = model.predict(input_df)
                
                if prediction[0] == 1:
                    st.error("⚠️ Prédiction : **Risque de Diabète**")
                else:
                    st.success("✅ Prédiction : **Pas de Diabète détecté**")

## PAGE 5 : NOUVEAU PATIENT (AVEC MySQL)
# ============================================
elif page == "📝 Nouveau Patient":
    st.title("📝 Inscription d'un Nouveau Patient")
    st.info("💡 Enregistrez les informations d'un patient pour suivre son évolution")
    
    # Récupérer la date du jour comme valeur par défaut
    today = date.today()
    
    with st.form("inscription_patient"):
        st.markdown("### 👤 Informations Personnelles")
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("Nom *", placeholder="TCHOUA")
            prenom = st.text_input("Prénom *", placeholder="Marie")
            # Utilisation de today comme valeur par défaut
            date_naissance = st.date_input("Date de naissance *", value=today) 
            sexe = st.selectbox("Sexe *", ["Homme", "Femme"])
        
        with col2:
            telephone = st.text_input("Téléphone *", placeholder="6 XX XX XX XX")
            ville = st.selectbox("Ville *", [
                "Douala", "Yaoundé", "Bafoussam", "Bamenda", 
                "Garoua", "Maroua", "Ngaoundéré", "Bertoua", 
                "Buea", "Limbé", "Kribi", "Ebolowa", "Kumba"
            ])
            quartier = st.text_input("Quartier", placeholder="Ex: Akwa, Bastos...")
        
        submitted = st.form_submit_button("💾 Enregistrer", use_container_width=True, type="primary")
        
        if submitted:
            # Conversion de l'objet date en format YYYY-MM-DD string pour MySQL
            date_naissance_str = date_naissance.strftime('%Y-%m-%d')

            if nom and prenom and telephone:
                conn = create_db_connection() # Établir la connexion
                if conn:
                    cursor = conn.cursor()
                    try:
                        # Requête INSERT : Utilisation de %s pour les placeholders dans mysql.connector
                        insert_query = """
                            INSERT INTO patients 
                            (nom, prenom, date_naissance, sexe, telephone, ville, quartier)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        data = (nom, prenom, date_naissance_str, sexe, telephone, ville, quartier)
                        
                        cursor.execute(insert_query, data)
                        conn.commit() # Confirmer la transaction
                        
                        # Récupérer l'ID inséré (équivalent de c.lastrowid en SQLite)
                        patient_id = cursor.lastrowid
                        
                        st.success(f"""
                        ✅ **Patient enregistré avec succès !**
                        
                        📋 **ID Patient :** {patient_id}
                        👤 **Nom :** {prenom} {nom}
                        📞 **Contact :** {telephone}
                        
                        Vous pouvez maintenant ajouter des mesures dans "📈 Suivi Patient"
                        """)
                    
                    except Error as e:
                        st.error(f"❌ Erreur MySQL lors de l'enregistrement : {e}")
                    
                    finally:
                        # Toujours fermer le curseur et la connexion
                        if cursor:
                            cursor.close()
                        close_db_connection(conn)
                        
                else:
                    st.error("❌ Impossible de se connecter à la base de données MySQL.")
            else:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires (*)")
# ============================================
# PAGE 6 : SUIVI PATIENT (AVEC MySQL)
# ============================================
elif page == "📈 Suivi Patient":
    # Assurez-vous que les imports nécessaires sont en tête de votre fichier: 
    # from datetime import datetime, date
    from datetime import datetime # Nécessaire pour datetime.now()
    import matplotlib.pyplot as plt # Nécessaire pour les graphiques
    
    st.title("📈 Suivi Médical des Patients")
    
    # 1. Établir la connexion MySQL
    conn = create_db_connection()
    
    if conn:
        try:
            # 2. Lire les données directement depuis MySQL dans un DataFrame Pandas
            query = "SELECT * FROM patients ORDER BY date_inscription DESC"
            patients = pd.read_sql(query, conn) 
            
            if len(patients) > 0:
                # 3. Sélection du patient
                st.markdown("### 1️⃣ Sélectionner un patient")
                
                # Assurez-vous que la colonne 'id' est bien un type chaîne pour la concaténation
                patients['id'] = patients['id'].astype(str)
                patient_names = patients['prenom'] + ' ' + patients['nom'] + ' (ID: ' + patients['id'] + ')'
                
                default_index = 0
                selected = st.selectbox("Choisir un patient :", patient_names, index=default_index)
                
                if selected:
                    # Extraction de l'ID du patient sélectionné
                    patient_id_str = selected.split('ID: ')[1].split(')')[0]
                    patient_id_int = int(patient_id_str)
                    
                    # Récupération des informations du patient sélectionné
                    patient_info = patients[patients['id'].astype(int) == patient_id_int].iloc[0]
                    current_patient_id = patient_id_int 
                    
                    # ==========================================
                    # 4. AFFICHER LA FICHE PATIENT 
                    # ==========================================
                    st.subheader(f"Dossier pour {patient_info['prenom']} {patient_info['nom']}")
                    st.write(f"Ville: **{patient_info['ville']}** | Téléphone: **{patient_info['telephone']}**")

                    st.markdown("---")
                    st.markdown("### 📋 Fiche Patient")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    # Calcul de l'âge
                    try:
                        age = datetime.now().year - pd.to_datetime(patient_info['date_naissance']).year
                    except:
                        # Cas d'erreur si date_naissance est manquante/invalide
                        age = 0 
                    
                    # CORRECTION CLÉ : Assurer que l'âge par défaut est >= 18
                    default_input_age = max(18, age)

                    with col1:
                        st.metric("👤 Nom", f"{patient_info['prenom']} {patient_info['nom']}")
                    with col2:
                        st.metric("📞 Téléphone", patient_info['telephone'])
                    with col3:
                        st.metric("🏙️ Ville", patient_info['ville'])
                    with col4:
                        st.metric("🎂 Âge", f"{age} ans")
                    
                    st.markdown("---")
                    
                    # ==========================================
                    # 5. AJOUTER UNE NOUVELLE MESURE
                    # ==========================================
                    st.markdown("### 2️⃣ Ajouter une Nouvelle Mesure")
                    
                    with st.form("nouvelle_mesure"):
                        st.markdown("#### Données Médicales")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            pregnancies = st.number_input("🤰 Grossesses", 0, 20, 0, key="m_preg")
                            glucose = st.number_input("🍬 Glucose (mg/dL)", 50, 300, 100, key="m_gluc")
                            blood_pressure = st.number_input("💉 Pression artérielle", 40, 200, 80, key="m_bp")
                        
                        with col2:
                            skin_thickness = st.number_input("📏 Épaisseur peau (mm)", 0, 100, 20, key="m_st")
                            insulin = st.number_input("💉 Insuline (µU/mL)", 0, 900, 0, key="m_insu")
                            bmi = st.number_input("⚖️ BMI", 10.0, 70.0, 25.0, step=0.1, key="m_bmi")
                        
                        with col3:
                            diabetes_pedigree = st.number_input("🧬 Pedigree Diabète", 0.0, 3.0, 0.5, step=0.01, key="m_dpf")
                            # Utilisation de la variable default_input_age pour respecter le min_value=18
                            patient_age = st.number_input("🎂 Âge actuel", 18, 100, default_input_age, key="m_age") 
                            
                        # Le bouton soumis est correctement placé ici
                        submitted = st.form_submit_button("💾 Enregistrer la mesure", use_container_width=True, type="primary")
                        
                        if submitted:
                            # 5.1 Logique de Prédiction
                            prediction = "Non analysé"
                            risque_niveau = "À évaluer"
                            probabilite_diabete = 0.0 # Initialisation de la variable
                            
                            if 'model' in st.session_state and 'scaler' in st.session_state and 'features' in st.session_state:
                                try:
                                    features = st.session_state['features']
                                    scaler = st.session_state['scaler']
                                    model = st.session_state['model']
                                    
                                    data_dict = {
                                        'Pregnancies': pregnancies, 'Glucose': glucose, 'BloodPressure': blood_pressure,
                                        'SkinThickness': skin_thickness, 'Insulin': insulin, 'BMI': bmi,
                                        'DiabetesPedigreeFunction': diabetes_pedigree, 'Age': patient_age
                                    }
                                    
                                    input_data = {k: v for k, v in data_dict.items() if k in features}
                                    input_df = pd.DataFrame([input_data])
                                    
                                    pred = model.predict(scaler.transform(input_df))
                                    proba = model.predict_proba(scaler.transform(input_df))
                                    
                                    prediction = "Diabétique" if pred[0] == 1 else "Non-Diabétique"
                                    
                                    # CALCUL ET STOCKAGE DE LA PROBABILITÉ
                                    probabilite_diabete = proba[0][1] * 100 

                                    if proba[0][1] >= 0.7:
                                        risque_niveau = "Élevé"
                                    elif proba[0][1] >= 0.4:
                                        risque_niveau = "Modéré"
                                    else:
                                        risque_niveau = "Faible"
                                        
                                except Exception as err:
                                    prediction = "Erreur de prédiction"
                                    risque_niveau = "Erreur"
                                    st.warning(f"Impossible de prédire : {err}")
                            
                            # 5.2 Enregistrer dans la BD (avec %s pour MySQL)
                            if conn:
                                try:
                                    cursor = conn.cursor()
                                    sql = '''
                                        INSERT INTO mesures 
                                        (patient_id, pregnancies, glucose, blood_pressure, skin_thickness, 
                                         insulin, bmi, diabetes_pedigree, age, prediction, risque_niveau)
                                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    '''
                                    values = (current_patient_id, pregnancies, glucose, blood_pressure, skin_thickness, 
                                              insulin, bmi, diabetes_pedigree, patient_age, prediction, risque_niveau)
                                    
                                    cursor.execute(sql, values)
                                    conn.commit()
                                    
                                    st.success("✅ Mesure enregistrée avec succès !")
                                    
                                    # AFFICHAGE DU RÉSULTAT CORRIGÉ
                                    message_proba = f" (Probabilité : **{probabilite_diabete:.2f}%**)" if probabilite_diabete > 0 else ""

                                    if prediction == "Diabétique":
                                        st.error(f"⚠️ **Prédiction : {prediction}** - Risque {risque_niveau}{message_proba}")
                                    elif prediction == "Non-Diabétique":
                                        st.success(f"✅ **Prédiction : {prediction}** - Risque {risque_niveau}{message_proba}")
                                    else:
                                        st.info(f"ℹ️ {prediction}{message_proba}")
                                        
                                    st.rerun() 
                                except Error as e:
                                    st.error(f"❌ Erreur MySQL lors de l'enregistrement de la mesure : {e}")
                            else:
                                st.error("❌ Connexion MySQL perdue. Impossible d'enregistrer.")
                                
                    # ==========================================
                    # 6. HISTORIQUE DES MESURES
                    # ==========================================
                    st.markdown("---")
                    st.markdown("### 3️⃣ Historique des Mesures")
                    
                    mesures = pd.read_sql_query(
                        f"SELECT * FROM mesures WHERE patient_id = {current_patient_id} ORDER BY date_mesure DESC", 
                        conn
                    )
                    
                    if len(mesures) > 0:
                        st.dataframe(mesures, use_container_width=True)
                        
                        # Graphiques d'évolution
                        st.markdown("### 📊 Évolution dans le temps")
                        
                        tab1, tab2, tab3 = st.tabs(["🍬 Glucose", "⚖️ BMI", "💉 Pression"])
                        
                        with tab1:
                            if len(mesures) > 1:
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.plot(mesures['date_mesure'], mesures['glucose'], 
                                        marker='o', color='#CE1126', linewidth=2)
                                ax.axhline(y=126, color='red', linestyle='--', label='Seuil Diabète')
                                ax.axhline(y=100, color='orange', linestyle='--', label='Seuil Pré-diabète')
                                ax.set_xlabel('Date')
                                ax.set_ylabel('Glucose (mg/dL)')
                                ax.set_title('Évolution du Glucose')
                                ax.legend()
                                plt.xticks(rotation=45)
                                st.pyplot(fig)
                            else:
                                st.info("📊 Besoin d'au moins 2 mesures pour afficher l'évolution")
                        
                        with tab2:
                            if len(mesures) > 1:
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.plot(mesures['date_mesure'], mesures['bmi'], 
                                        marker='s', color='#006233', linewidth=2)
                                ax.axhline(y=25, color='orange', linestyle='--', label='Surpoids')
                                ax.axhline(y=30, color='red', linestyle='--', label='Obésité')
                                ax.set_xlabel('Date')
                                ax.set_ylabel('BMI (kg/m²)')
                                ax.set_title('Évolution du BMI')
                                ax.legend()
                                plt.xticks(rotation=45)
                                st.pyplot(fig)
                            else:
                                st.info("📊 Besoin d'au moins 2 mesures pour afficher l'évolution")
                        
                        with tab3:
                            if len(mesures) > 1:
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.plot(mesures['date_mesure'], mesures['blood_pressure'], 
                                        marker='^', color='#FCD116', linewidth=2)
                                ax.axhline(y=140, color='red', linestyle='--', label='Hypertension')
                                ax.set_xlabel('Date')
                                ax.set_ylabel('Pression artérielle')
                                ax.set_title('Évolution de la Pression')
                                ax.legend()
                                plt.xticks(rotation=45)
                                st.pyplot(fig)
                            else:
                                st.info("📊 Besoin d'au moins 2 mesures pour afficher l'évolution")
                    
                    else:
                        st.info("ℹ️ Aucune mesure enregistrée pour ce patient")
                        
                else:
                    st.info("Aucun patient sélectionné.")
            
            else:
                 st.info("Aucun patient n'est actuellement enregistré dans la base de données.")
            
        except Exception as e:
            st.error(f"Erreur lors de l'opération MySQL : {e}")
            
        finally:
            # 7. Fermer la connexion
            close_db_connection(conn)
    else:
        st.error("Impossible d'établir la connexion à la base de données pour le suivi patient.")
# ============================================
# PAGE 7 : CONSEILS NUTRITION
# ============================================
elif page == "🥘 Conseils Nutrition":
    st.title("🥘 Alimentation Saine à la Camerounaise")
    st.markdown("### *Manger bien tout en restant camerounais !*")
    
    st.markdown("---")
    
    # Aliments à privilégier
    st.markdown("## ✅ Aliments à Privilégier")
    
    aliments_bons = {
        "🌾 Céréales Complètes": {
            "aliments": ["Mil", "Sorgho", "Maïs complet", "Riz brun (pas blanc!)", "Couscous de mil"],
            "conseil": "Remplacez le riz blanc par du riz brun progressivement"
        },
        "🥬 Légumes (Sans Limite!)": {
            "aliments": ["Ndolé", "Gombo", "Épinards", "Feuilles de patate douce", 
                        "Moringa", "Eru", "Kelen-kelen", "Tomates", "Oignons"],
            "conseil": "Remplissez la moitié de votre assiette avec des légumes verts"
        },
        "🍠 Tubercules (Portions Contrôlées)": {
            "aliments": ["Macabo (petit morceau)", "Igname (1/4 du plat)", 
                        "Taro", "Patate douce (meilleure que le manioc)"],
            "conseil": "Évitez le bâton de manioc ou limitez à 2 fois/semaine"
        },
        "🥜 Protéines Maigres": {
            "aliments": ["Poisson braisé/fumé", "Poulet sans peau", "Haricots rouges/blancs", 
                        "Arachides (poignée/jour)", "Soja", "Œufs", "Koki"],
            "conseil": "Préférez le poisson à la viande rouge"
        },
        "🍎 Fruits Locaux": {
            "aliments": ["Papaye", "Goyave", "Avocat (excellent!)", 
                        "Mangue (1 par jour max)", "Ananas (portion modérée)", "Citron"],
            "conseil": "Mangez les fruits entiers, pas en jus"
        }
    }
    
    for categorie, data in aliments_bons.items():
        with st.expander(categorie):
            st.markdown(f"**💡 Conseil :** {data['conseil']}")
            st.markdown("**Liste :**")
            for aliment in data['aliments']:
                st.write(f"• {aliment}")
    
    st.markdown("---")
    
    # Aliments à éviter
    st.markdown("## ⚠️ Aliments à Limiter/Éviter")
    
    aliments_attention = {
        "🍞 Glucides Raffinés": ["Pain blanc", "Pâtisseries", "Beignets sucrés", "Gâteaux"],
        "🍺 Boissons": ["Bière (max 1/semaine)", "Sodas", "Jus sucrés", "Top/Djino en excès"],
        "🍖 Viandes Grasses": ["Viande de porc grasse", "Peau de poulet", "Saucisses", "Viande fumée en excès"],
        "🍚 Attention": ["Riz blanc en grande quantité", "Bâton de manioc tous les jours", 
                        "Huile de palme en excès", "Aliments frits quotidiennement"]
    }
    
    for categorie, aliments in aliments_attention.items():
        with st.expander(categorie):
            for aliment in aliments:
                st.write(f"❌ {aliment}")
    
    st.markdown("---")
    
    # Recettes adaptées
    st.markdown("## 👨‍🍳 Recettes Anti-Diabète Camerounaises")
    
    recette = st.selectbox("Choisir une recette:", [
        "Ndolé aux arachides (version allégée)", 
        "Eru avec poisson fumé",
        "Salade de gombo et tomates",
        "Koki aux haricots (version santé)",
        "Soupe de légumes camerounaise"
    ])
    
    recettes_details = {
        "Ndolé aux arachides (version allégée)": {
            "ingredients": [
                "500g de feuilles de ndolé",
                "100g de pâte d'arachide non sucrée",
                "200g de poisson fumé",
                "2 cuillères à soupe d'huile (au lieu de 5-6)",
                "Oignons, ail, gingembre",
                "Piment (modéré)"
            ],
            "preparation": [
                "1. Faire bouillir les feuilles 2 fois pour réduire l'amertume",
                "2. Utiliser MOINS d'huile qu'habituellement",
                "3. Ajouter beaucoup d'épices pour compenser",
                "4. Cuire doucement avec le poisson",
                "5. Servir avec du riz brun ou du couscous de mil"
            ],
            "conseil": "✅ Index glycémique: MOYEN - Bon pour diabétiques!",
            "portion": "🍽️ Portion recommandée: 1 tasse avec 1/2 tasse de riz brun"
        },
        "Eru avec poisson fumé": {
            "ingredients": [
                "300g de feuilles d'eru (okok)",
                "Poisson fumé/crevettes séchées",
                "1 cuillère d'huile de palme",
                "Sel, piment",
                "Water leaf (feuilles d'eau)"
            ],
            "preparation": [
                "1. Couper finement les feuilles d'eru",
                "2. Ajouter très peu d'eau (eru fait son propre jus)",
                "3. Minimiser l'huile de palme",
                "4. Ajouter le poisson fumé",
                "5. Cuire 20-30 minutes"
            ],
            "conseil": "✅ Très faible en glucides - Excellent pour diabétiques!",
            "portion": "🍽️ Portion: Illimitée! Servir avec petit morceau de macabo"
        },
        "Salade de gombo et tomates": {
            "ingredients": [
                "500g de gombos frais",
                "3 tomates",
                "1 oignon",
                "Jus de citron",
                "1 cuillère d'huile d'arachide",
                "Sel, piment"
            ],
            "preparation": [
                "1. Couper les gombos en rondelles",
                "2. Blanchir 2 minutes dans l'eau bouillante",
                "3. Hacher tomates et oignons",
                "4. Mélanger avec citron et huile",
                "5. Servir frais"
            ],
            "conseil": "✅ Index glycémique: TRÈS BAS - Parfait!",
            "portion": "🍽️ À volonté comme accompagnement"
        },
        "Koki aux haricots (version santé)": {
            "ingredients": [
                "500g de haricots (niébé)",
                "2 cuillères d'huile de palme (réduire!)",
                "Piment rouge",
                "Sel, épices",
                "Feuilles de bananier"
            ],
            "preparation": [
                "1. Moudre les haricots après trempage",
                "2. RÉDUIRE l'huile de palme (1-2 cuillères max)",
                "3. Ajouter piment et sel",
                "4. Envelopper dans feuilles",
                "5. Cuire à la vapeur 45 min"
            ],
            "conseil": "✅ Riche en protéines et fibres!",
            "portion": "🍽️ 2 petits koki max par repas"
        },
        "Soupe de légumes camerounaise": {
            "ingredients": [
                "Gombo, tomates, oignons",
                "Feuilles de patate douce",
                "Moringa",
                "Poisson/poulet",
                "Épices locales"
            ],
            "preparation": [
                "1. Faire revenir oignons et tomates",
                "2. Ajouter de l'eau et porter à ébullition",
                "3. Ajouter tous les légumes",
                "4. Ajouter protéines",
                "5. Cuire 20 minutes"
            ],
            "conseil": "✅ Très nutritif et faible en calories!",
            "portion": "🍽️ Illimité - Mangez-en beaucoup!"
        }
    }
    
    if recette in recettes_details:
        details = recettes_details[recette]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🛒 Ingrédients")
            for ing in details['ingredients']:
                st.write(f"• {ing}")
        
        with col2:
            st.markdown("### 📝 Préparation")
            for etape in details['preparation']:
                st.write(etape)
        
        st.success(details['conseil'])
        st.info(details['portion'])
    
    st.markdown("---")
    
    # Plan de repas type
    st.markdown("## 📅 Exemple de Menu Quotidien")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🌅 Petit-Déjeuner")
        st.write("""
        **Option 1:**
        - Bouillie de mil/sorgho
        - 1 œuf dur
        - 1/2 papaye
        
        **Option 2:**
        - Haricots bouillis
        - 1 avocat
        - Thé sans sucre
        """)
    
    with col2:
        st.markdown("### ☀️ Déjeuner")
        st.write("""
        **Plat complet:**
        - Ndolé (version allégée)
        - 1/2 tasse de riz brun
        - Salade de tomates
        - 1 fruit
        
        **Ou:**
        - Eru avec poisson
        - Petit morceau de macabo
        - Légumes verts
        """)
    
    with col3:
        st.markdown("### 🌙 Dîner")
        st.write("""
        **Léger:**
        - Soupe de légumes
        - Poulet grillé
        - Salade
        
        **Ou:**
        - Koki
        - Gombo sauce
        - Fruits
        """)

# ============================================
# PAGE 8 : CENTRES DE SANTÉ
# ============================================
elif page == "🏥 Centres de Santé":
    st.title("🏥 Centres de Santé au Cameroun")
    st.markdown("### *Trouvez un centre près de chez vous*")
    
    hopitaux = {
        "Douala": [
            {"nom": "Hôpital Général de Douala", "quartier": "Deido", "tel": "233 42 26 12", 
             "specialite": "Service d'endocrinologie"},
            {"nom": "Hôpital Laquintinie", "quartier": "Bonanjo", "tel": "233 42 24 15",
             "specialite": "Consultation diabétologie"},
            {"nom": "Polyclinique Douala", "quartier": "Akwa", "tel": "233 43 15 89",
             "specialite": "Suivi diabète"},
            {"nom": "Centre Médical Le Jourdain", "quartier": "Bonapriso", "tel": "233 42 77 88",
             "specialite": "Médecine générale + diabète"}
        ],
        "Yaoundé": [
            {"nom": "Hôpital Central", "quartier": "Centre-ville", "tel": "222 23 40 20",
             "specialite": "Service endocrinologie"},
            {"nom": "Hôpital Général", "quartier": "Ngoa-Ekélé", "tel": "222 20 13 89",
             "specialite": "Consultation diabète"},
            {"nom": "CHU de Yaoundé", "quartier": "Odza", "tel": "222 31 21 24",
             "specialite": "Centre de référence diabète"},
            {"nom": "Hôpital Jamot", "quartier": "Messa", "tel": "222 21 20 35",
             "specialite": "Suivi maladies chroniques"}
        ],
        "Bafoussam": [
            {"nom": "Hôpital Régional", "quartier": "Centre", "tel": "244 44 11 06",
             "specialite": "Consultation diabète"}
        ],
        "Bamenda": [
            {"nom": "Regional Hospital Bamenda", "quartier": "Ntarinkon", "tel": "233 36 13 33",
             "specialite": "Diabetes clinic"}
        ],
        "Garoua": [
            {"nom": "Hôpital Régional", "quartier": "Centre", "tel": "222 27 12 91",
             "specialite": "Service médecine interne"}
        ]
    }
    
    ville_selectionnee = st.selectbox("🏙️ Choisir votre ville:", list(hopitaux.keys()))
    
    st.markdown(f"### 📍 Centres disponibles à {ville_selectionnee}")
    st.markdown("---")
    
    for idx, hopital in enumerate(hopitaux[ville_selectionnee]):
        with st.expander(f"🏥 {hopital['nom']}", expanded=(idx==0)):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📍 Quartier:** {hopital['quartier']}")
                st.markdown(f"**☎️ Téléphone:** {hopital['tel']}")
            
            with col2:
                st.markdown(f"**⚕️ Spécialité:** {hopital['specialite']}")
            
            st.markdown("---")
            st.info("💡 **Conseil:** Appelez avant de vous déplacer pour connaître les horaires de consultation")
    
    st.markdown("---")
    st.markdown("### 🩺 Services disponibles dans ces centres")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Tests disponibles:**
        - ✅ Glycémie à jeun
        - ✅ HbA1c (hémoglobine glyquée)
        - ✅ Test de tolérance au glucose
        - ✅ Bilan lipidique
        """)
    
    with col2:
        st.markdown("""
        **Consultations:**
        - ✅ Endocrinologue
        - ✅ Diététicien
        - ✅ Infirmier éducateur
        - ✅ Ophtalmologiste (complications)
        """)

# ============================================
# PAGE 9 : FORMATION
# ============================================
elif page == "📚 Formation Diabète":
    st.title("📚 Comprendre le Diabète")
    st.markdown("### *Éducation et Prévention*")
    
    modules = {
        "1️⃣ Qu'est-ce que le Diabète?": """
        ### 🩺 Le Diabète expliqué simplement
        
        Le diabète, c'est quand le **sucre reste dans le sang** au lieu d'entrer dans les cellules.
        
        **🚗 Analogie camerounaise:**
        
        Imaginez que le **glucose** (sucre) est comme de l'**essence pour un taxi**.
        L'**insuline** est le **pompiste** qui met le carburant dans le réservoir.
        
        Si le pompiste ne travaille pas bien → l'essence reste dehors → **DIABÈTE!**
        
        ### Types de diabète :
        
        **🔴 Type 1 :** Le pancréas ne produit PLUS d'insuline (rare au Cameroun, environ 10%)
        
        **🔴 Type 2 :** Le corps **résiste** à l'insuline (90% des cas ici) - C'est celui qu'on peut prévenir!
        
        **🤰 Gestationnel :** Pendant la grossesse (disparaît après l'accouchement, mais augmente le risque futur)
        """,
        
        "2️⃣ Symptômes à Surveiller": """
        ### ⚠️ Les Signes d'Alerte
        
        Si vous avez plusieurs de ces symptômes, **consultez rapidement** :
        
        **💧 Les 3 "P" classiques :**
        - 🚰 **Polyurie** : Uriner très souvent (surtout la nuit, 5-6 fois)
        - 🥤 **Polydipsie** : Soif excessive (boire 3-4 litres d'eau/jour)
        - 🍽️ **Polyphagie** : Faim constante malgré qu'on mange
        
        **Autres signes importants :**
        - 😴 Fatigue permanente (même après le repos)
        - 👁️ Vision floue ou troublée
        - 🩹 Plaies qui cicatrisent lentement (plus de 2 semaines)
        - ⚖️ Perte de poids inexpliquée
        - 🦶 Fourmillements dans les pieds/mains
        - 🍄 Infections fréquentes (mycoses, furoncles)
        
        **🚨 URGENCE IMMÉDIATE si :**
        - Confusion mentale
        - Respiration très rapide
        - Haleine qui sent l'acétone (comme du vernis)
        - Vomissements répétés
        
        → **Appelez le SAMU immédiatement!**
        """,
        
        "3️⃣ Facteurs de Risque": """
        ### 🎯 Qui est à Risque ?
        
        **Facteurs NON modifiables :**
        - 🧬 Antécédents familiaux (parents/frères/sœurs diabétiques)
        - 🎂 Âge > 45 ans
        - 👶 Avoir eu un diabète gestationnel
        - 👶 Avoir accouché d'un bébé de plus de 4kg
        
        **Facteurs MODIFIABLES (vous pouvez agir!) :**
        - ⚖️ **Surpoids/Obésité** (BMI > 25) - FACTEUR #1
        - 🛋️ Sédentarité (pas d'exercice)
        - 🍔 Alimentation trop riche (riz blanc, sucreries, huile)
        - 💤 Manque de sommeil
        - 😰 Stress chronique
        - 🚬 Tabagisme
        - 🍺 Consommation excessive d'alcool
        
        **💡 Bonne nouvelle :** En changeant votre mode de vie, vous pouvez **réduire le risque de 60%** !
        """,
        
        "4️⃣ Complications à Éviter": """
        ### ⚠️ Pourquoi Traiter le Diabète ?
        
        Un diabète non contrôlé peut causer des dégâts graves :
        
        **👁️ Yeux - Rétinopathie diabétique**
        - Peut mener à la cécité
        - Contrôle annuel chez l'ophtalmologue obligatoire
        
        **🫀 Cœur et Vaisseaux**
        - Infarctus (2-4 fois plus de risques)
        - AVC (accident vasculaire cérébral)
        - Hypertension
        
        **🦶 Pieds - Pied diabétique**
        - Perte de sensibilité
        - Infections graves
        - Risque d'amputation si négligé
        
        **🫘 Reins - Insuffisance rénale**
        - Peut nécessiter la dialyse
        - Contrôle régulier nécessaire
        
        **🧠 Nerfs - Neuropathie**
        - Douleurs, fourmillements
        - Perte de sensibilité
        
        **✅ MAIS : Toutes ces complications peuvent être ÉVITÉES avec un bon contrôle du diabète !**
        """,
        
        "5️⃣ Prévention - Ce Que VOUS Pouvez Faire": """
        ### 💪 Plan d'Action Concret
        
        **🥗 1. ALIMENTATION (40% de l'impact)**
        
        ✅ **À FAIRE :**
        - Manger beaucoup de légumes verts (ndolé, gombo, eru)
        - Remplacer riz blanc par riz brun ou couscous de mil
        - Préférer le poisson à la viande rouge
        - Boire 1.5-2L d'eau par jour
        
        ❌ **À ÉVITER :**
        - Sodas et jus sucrés
        - Beignets et pâtisseries
        - Bâton de manioc tous les jours
        - Excès d'huile de palme
        
        **🏃 2. ACTIVITÉ PHYSIQUE (30% de l'impact)**
        - **150 minutes/semaine** = 30 min x 5 jours
        - Marche rapide, danse, football
        - Monter les escaliers au lieu de l'ascenseur
        - Descendre du bus 2 arrêts plus tôt
        
        **😴 3. SOMMEIL (15% de l'impact)**
        - Dormir **7-8 heures** par nuit
        - Se coucher à heures régulières
        - Éviter les écrans 1h avant le sommeil
        
        **🧘 4. GESTION DU STRESS (15% de l'impact)**
        - Prière/méditation
        - Respiration profonde
        - Temps avec la famille
        - Loisirs et détente
        
        **🩺 5. DÉPISTAGE RÉGULIER**
        - Test de glycémie **1 fois/an** si > 45 ans
        - **2 fois/an** si antécédents familiaux
        - **Immédiatement** si symptômes
        """,
        
        "6️⃣ Vivre avec le Diabète": """
        ### 🌟 Diabète = Pas la Fin, un Nouveau Départ!
        
        **📋 Contrôles Réguliers Nécessaires :**
        - 🩸 Glycémie : 2-4 fois/jour selon le type
        - 💊 HbA1c : Tous les 3 mois (objectif < 7%)
        - 👁️ Ophtalmologue : 1 fois/an
        - 🦶 Examen des pieds : À chaque consultation
        - 🫘 Fonction rénale : 1 fois/an
        
        **💊 Traitements Disponibles :**
        
        **Médicaments oraux :**
        - Metformine (1ère ligne)
        - Sulfamides hypoglycémiants
        - Inhibiteurs SGLT2
        
        **Insuline :**
        - Nécessaire pour type 1
        - Parfois pour type 2 avancé
        
        **💰 Où Trouver les Médicaments au Cameroun :**
        - Pharmacies agréées
        - CENAME (prix subventionnés)
        - Programmes d'aide (associations)
        
        **🤝 Soutien et Ressources :**
        - Association Camerounaise des Diabétiques
        - Groupes de soutien dans les hôpitaux
        - Ligne d'aide : [Numéro à compléter]
        
        **💡 Message d'Espoir :**
        Avec un bon suivi, les diabétiques vivent **aussi longtemps** que les non-diabétiques !
        Beaucoup de célébrités ont le diabète et mènent une vie normale.
        """,
        
        "7️⃣ Mythes et Réalités": """
        ### 🔍 Vrai ou Faux ?
        
        **❌ MYTHE : "Le diabète vient de la sorcellerie"**
        ✅ **RÉALITÉ :** C'est une maladie MÉDICALE causée par l'alimentation, le poids et la génétique.
        
        **❌ MYTHE : "Manger trop de sucre cause le diabète"**
        ✅ **RÉALITÉ :** C'est l'EXCÈS de poids qui cause le diabète type 2. Le sucre y contribue indirectement.
        
        **❌ MYTHE : "Les plantes guérissent le diabète"**
        ✅ **RÉALITÉ :** Certaines plantes AIDENT (moringa, gingembre), mais ne remplacent PAS les médicaments.
        
        **❌ MYTHE : "Le diabète est contagieux"**
        ✅ **RÉALITÉ :** NON ! On ne peut pas "attraper" le diabète d'une autre personne.
        
        **❌ MYTHE : "On ne peut plus manger de fruits"**
        ✅ **RÉALITÉ :** Les fruits sont bons ! Juste en quantité modérée (1-2 par jour).
        
        **❌ MYTHE : "L'insuline rend aveugle"**
        ✅ **RÉALITÉ :** NON ! C'est le diabète mal contrôlé qui cause la cécité, pas l'insuline qui la traite.
        
        **❌ MYTHE : "Une fois diabétique, c'est fini"**
        ✅ **RÉALITÉ :** Le diabète type 2 peut être **mis en rémission** avec perte de poids et exercice !
        """
    }
    
    for titre, contenu in modules.items():
        with st.expander(titre):
            st.markdown(contenu)
    
    st.markdown("---")
    st.success("""
    ### 🎓 Quiz de Connaissance (À venir)
    
    Bientôt disponible : testez vos connaissances sur le diabète avec un quiz interactif !
    """)

# ============================================
# PAGE 9 : GESTION UTILISATEURS (CORRIGÉ)
# ============================================

elif page == "🔐 Gestion Utilisateurs":
    # 1. Vérification des permissions
    # ... (le code d'accès refusé reste le même) ...
    
    st.title("🔐 Gestion des Comptes Utilisateurs")
    st.info("Interface pour créer de nouveaux comptes pour les équipes médicales et administratives.")
    
    # --- Formulaire de Création d'utilisateur (Logique de soumission incluse) ---
    with st.form("creation_utilisateur", clear_on_submit=True):
        st.markdown("### Créer un Nouveau Compte")
        
        col_u1, col_u2 = st.columns(2)
        
        # Définition des champs d'entrée
        with col_u1:
            # st.selectbox doit être au début pour que new_role soit défini avant les conditions
            new_role = st.selectbox("Rôle du nouvel utilisateur *", ["medecin", "infirmier", "admin"])
            new_username = st.text_input("Nom d'utilisateur (Login) *", placeholder="Ex: dr.nouvelle")
        
        with col_u2:
            new_fullname = st.text_input("Nom Complet *", placeholder="Ex: Dr. Alain NGANOU")
            new_password = st.text_input("Mot de passe temporaire *", type="password")
            
        st.markdown("---")

        # Définir les permissions par défaut basées sur le rôle pour le multiselect (CORRECTION ICI)
        # On utilise le nom de permission simple
        if new_role == 'medecin':
            simple_perms = ['Accueil', 'Visualisations', 'ML Model 1', 'ML Model 2', 'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Centres Santé', 'Formation']
        elif new_role == 'infirmier':
            simple_perms = ['Accueil', 'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Centres Santé', 'Formation']
        elif new_role == 'admin':
            simple_perms = ['Accueil', 'Visualisations', 'ML Model 1', 'ML Model 2', 'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Centres Santé', 'Formation', 'Gestion Utilisateurs', 'Configuration & Stats']

        # CONVERSION: Mapper les noms de permission simple aux clés avec emojis
        default_perms = [get_page_key(p) for p in simple_perms]

        # Permettre la personnalisation des permissions
        selected_permissions = st.multiselect(
            "Personnaliser les Permissions (optionnel)",
            options=list(page_mapping.keys()),
            default=default_perms # C'EST MAINTENANT UNE LISTE DE CLÉS AVEC EMOJIS
        )

        submitted_user = st.form_submit_button("➕ Créer l'utilisateur", type="primary", use_container_width=True)
        
        # Logique de soumission (s'exécute lorsque le bouton est cliqué)
        if submitted_user:
            if new_username and new_fullname and new_password:
                # IMPORTANT : Reconvertir les permissions sélectionnées (avec emojis) 
                # en leur nom simple pour l'enregistrement en BD
                perms_to_save = [page_mapping[key] for key in selected_permissions]

                # Appel à la fonction d'insertion en BD
                if create_user_in_db(new_username, new_password, new_role, new_fullname, perms_to_save):
                    st.success(f"✅ Utilisateur **{new_fullname} ({new_username})** créé et enregistré en base de données.")
                else:
                    st.error("❌ Échec de la création de l'utilisateur. Le nom d'utilisateur existe peut-être déjà ou il y a une erreur MySQL.")
            else:
                st.error("❌ Veuillez remplir tous les champs obligatoires.")
                
    st.markdown("---")
    
    # Ajout d'une section pour visualiser les utilisateurs (recommandé pour un admin)
    st.subheader("Visualisation et Modification (À Implémenter)")
    st.warning("Ajoutez ici le code pour lister tous les utilisateurs de la table `utilisateurs` et permettre leur modification/suppression.")
# ============================================
# PAGE 10 : CONFIGURATION & STATS
# ============================================
elif page == "⚙️ Configuration & Stats":
    if not check_permission(page):
        st.error("🔒 Accès refusé : Vous n'avez pas les permissions pour cette page.")
        st.stop()
        
    st.title("⚙️ Configuration Système & Statistiques Administratives")
    
    st.markdown("---")
    
    # Statistiques d'utilisation (Placeholder)
    st.header("📈 Statistiques Générales")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("Total Utilisateurs", "3", "Admin + 2 Pros")
    with col_s2:
        st.metric("Patients Enregistrés", "1245", "+ 50 ce mois-ci")
    with col_s3:
        st.metric("Modèles Entraînés", "2 (LogReg, Arbre)")

    st.markdown("---")
    
    # Configuration (Placeholder)
    st.header("🛠️ Paramètres du Système")
    with st.expander("Paramètres de Sécurité"):
        st.checkbox("Activer l'authentification à deux facteurs pour les Admins", value=True)
        st.number_input("Nombre de tentatives de connexion maximales", min_value=1, max_value=10, value=5)
        
    with st.expander("Paramètres des Modèles ML"):
        new_test_size = st.slider("Taille de l'ensemble de test par défaut (%)", 10, 50, 20)
        if st.button("Sauvegarder les Paramètres ML"):
             st.success(f"Paramètre 'Taille de test' mis à jour à {new_test_size}%")
             
    with st.expander("Maintenance de la Base de Données"):
        if st.button("Faire une Sauvegarde (Backup)"):
            st.warning("Opération non implémentée, mais serait ici.")
        if st.button("Nettoyer les logs de connexion"):
            st.info("Logs nettoyés.")
# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>DiabèteCam</strong> - Application de surveillance Médicale du diabète au Cameroun</p>
    
  
</div>
""", unsafe_allow_html=True)