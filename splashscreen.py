# auth.py
import streamlit as st

def init_session_state():
    """Initialise les variables de session pour l'authentification"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user' not in st.session_state:
        st.session_state.user = None

def authenticate(username, password, role):
    """Vérifie les identifiants et retourne les infos utilisateur"""
    users = {
        'medecin': {
            'username': 'dr.kamga',
            'password': 'medecin123',
            'role': 'medecin',
            'fullName': 'Dr. Jean KAMGA',
            'permissions': ['Accueil', 'Visualisations', 'ML Model 1', 'ML Model 2', 
                          'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Centres Santé', 'Formation']
        },
        'infirmier': {
            'username': 'inf.ngono',
            'password': 'infirmier123',
            'role': 'infirmier',
            'fullName': 'Marie NGONO',
            'permissions': ['Accueil', 'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Formation']
        },
        'admin': {
            'username': 'admin',
            'password': 'admin123',
            'role': 'admin',
            'fullName': 'Administrateur Système',
            'permissions': ['Accueil', 'Visualisations', 'ML Model 1', 'ML Model 2', 
                          'Nouveau Patient', 'Suivi Patient', 'Nutrition', 'Centres Santé', 
                          'Formation', 'Gestion Utilisateurs', 'Statistiques']
        }
    }
    
    user = users.get(role)
    if user and user['username'] == username and user['password'] == password:
        return user
    return None

def show_login_page():
    """Affiche la page de connexion"""
    st.markdown("""
    <style>
        .login-container {
            max-width: 500px;
            margin: 50px auto;
            padding: 30px;
            background: white;
            border-radius: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .login-title {
            text-align: center;
            color: #006233;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .login-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<h1 class="login-title">🏥 DiabèteCam</h1>', unsafe_allow_html=True)
        st.markdown('<p class="login-subtitle">Connexion Sécurisée</p>', unsafe_allow_html=True)
        
        # Sélection du rôle
        st.markdown("### 👤 Sélectionnez votre profil")
        role = st.selectbox(
            "Rôle",
            ["medecin", "infirmier", "admin"],
            format_func=lambda x: {
                "medecin": "👨‍⚕️ Médecin",
                "infirmier": "👩‍⚕️ Infirmier(ère)",
                "admin": "🔐 Administrateur"
            }[x],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Formulaire de connexion
        username = st.text_input("📧 Nom d'utilisateur", placeholder="Entrez votre identifiant")
        password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
        
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
        
        st.markdown("---")
        
        # Aide
        with st.expander("🔐 Comptes de test"):
            st.markdown("""
            **Médecin:**  
            👤 `dr.kamga` / 🔑 `medecin123`
            
            **Infirmier:**  
            👤 `inf.ngono` / 🔑 `infirmier123`
            
            **Admin:**  
            👤 `admin` / 🔑 `admin123`
            """)

def logout():
    """Déconnecte l'utilisateur"""
    st.session_state.logged_in = False
    st.session_state.user = None
    st.rerun()

def check_permission(page_name):
    """Vérifie si l'utilisateur a accès à une page"""
    if not st.session_state.logged_in:
        return False
    
    # Mapping des noms de pages
    page_mapping = {
        "🏠 Accueil": "Accueil",
        "📊 Visualisations": "Visualisations",
        "🤖 ML Model 1 (Régression)": "ML Model 1",
        "🌳 ML Model 2 (Arbre)": "ML Model 2",
        "📝 Nouveau Patient": "Nouveau Patient",
        "📈 Suivi Patient": "Suivi Patient",
        "🥘 Conseils Nutrition": "Nutrition",
        "🏥 Centres de Santé": "Centres Santé",
        "📚 Formation Diabète": "Formation"
    }
    
    permission_name = page_mapping.get(page_name, page_name)
    return permission_name in st.session_state.user['permissions']