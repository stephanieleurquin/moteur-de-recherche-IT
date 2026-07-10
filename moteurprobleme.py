import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from supabase import create_client
from typing import List, Tuple, Optional
import hashlib

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Assistant IT Pro",
    page_icon="🤖",
    layout="wide"
)

DB = "assistant_it_ia.db"
LIMITE_GRATUITE = 10

# ==================================================
# SUPABASE
# ==================================================

try:
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    SUPABASE_OK = True
except Exception as e:
    supabase = None
    SUPABASE_OK = False
    st.error("⚠️ Connexion Supabase impossible")
    st.write(e)

# ==================================================
# SESSION UTILISATEUR
# ==================================================

def init_session():
    """Initialise les variables de session"""
    defaults = {
        "user": None,
        "recherches": 0,
        "premium": False,
        "historique": [],
        "moteur": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==================================================
# BASE SQLITE
# ==================================================

@st.cache_resource
def connexion_db():
    """Crée et retourne une connexion à la base de données"""
    try:
        conn = sqlite3.connect(DB, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        return None

def creer_base():
    """Crée les tables nécessaires si elles n'existent pas"""
    conn = connexion_db()
    if conn is None:
        return
    
    try:
        cur = conn.cursor()
        
        # Table des pannes
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pannes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titre TEXT NOT NULL,
            description TEXT NOT NULL,
            diagnostic TEXT NOT NULL,
            procedure TEXT NOT NULL,
            questions TEXT,
            categorie TEXT,
            niveau INTEGER DEFAULT 1,
            tags TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table des utilisateurs (pour suivi local)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            recherches_total INTEGER DEFAULT 0,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Table de l'historique des recherches
        cur.execute("""
        CREATE TABLE IF NOT EXISTS historique_recherches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            requete TEXT,
            resultats INTEGER,
            date_recherche TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Erreur lors de la création de la base: {e}")
    finally:
        conn.close()

# ==================================================
# AJOUT DES DONNEES DE BASE
# ==================================================

def remplir_base():
    """Remplit la base avec des données initiales"""
    conn = connexion_db()
    if conn is None:
        return
    
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pannes")
        total = cur.fetchone()[0]
        
        if total == 0:
            donnees = [
                (
                    "PC très lent",
                    "L'ordinateur est extrêmement lent et rame au moindre usage",
                    "Manque de ressources, disque dur fragmenté ou programmes inutiles en arrière-plan",
                    "1️⃣ Ouvrir le Gestionnaire des tâches (Ctrl+Alt+Suppr)\n2️⃣ Désactiver les programmes inutiles au démarrage\n3️⃣ Nettoyer le disque (nettoyage de disque)\n4️⃣ Augmenter la mémoire RAM si possible",
                    "Depuis quand le PC est-il lent ? Avez-vous installé un nouveau logiciel récemment ?",
                    "Performance",
                    2,
                    "lent,rame,ordinateur,performance,optimisation"
                ),
                (
                    "WiFi impossible",
                    "Impossible de se connecter au réseau WiFi, pas d'internet",
                    "Problème de réseau, box défaillante, pilote WiFi obsolète ou interférences",
                    "1️⃣ Redémarrer la box internet\n2️⃣ Vérifier les autres appareils\n3️⃣ Réinstaller le pilote WiFi\n4️⃣ Réinitialiser les paramètres réseau",
                    "Les autres appareils (smartphone, tablette) ont-ils internet ?",
                    "Réseau",
                    2,
                    "wifi,internet,réseau,connexion,box"
                ),
                (
                    "Windows ne démarre pas",
                    "L'ordinateur s'allume mais Windows ne démarre pas, écran noir ou erreur",
                    "Fichier système endommagé, disque dur défaillant, ou problème de mise à jour",
                    "1️⃣ Démarrer en Mode sans échec (F8)\n2️⃣ Utiliser l'outil de réparation Windows\n3️⃣ Vérifier l'intégrité du disque\n4️⃣ Restaurer le système",
                    "Quel message d'erreur s'affiche ? Avez-vous installé des mises à jour récemment ?",
                    "Logiciel",
                    4,
                    "windows,démarrage,erreur,ecran-noir,systeme"
                )
            ]
            
            cur.executemany("""
            INSERT INTO pannes 
            (titre, description, diagnostic, procedure, questions, categorie, niveau, tags)
            VALUES (?,?,?,?,?,?,?,?)
            """, donnees)
            conn.commit()
            
    except sqlite3.Error as e:
        st.error(f"Erreur lors du remplissage de la base: {e}")
    finally:
        conn.close()

# ==================================================
# MOTEUR DE RECHERCHE IT
# ==================================================

class RechercheIT:
    """Moteur de recherche amélioré pour les problèmes IT"""
    
    def __init__(self):
        self.df = None
        self.cache_recherche = {}
        
    def charger(self):
        """Charge les données depuis la base de données"""
        if self.df is None:
            conn = connexion_db()
            if conn is None:
                self.df = pd.DataFrame()
                return
            try:
                self.df = pd.read_sql_query("SELECT * FROM pannes", conn)
            except sqlite3.Error as e:
                st.error(f"Erreur de chargement des données: {e}")
                self.df = pd.DataFrame()
            finally:
                conn.close()
    
    def normaliser(self, texte: str) -> str:
        """Normalise le texte pour la recherche"""
        if not isinstance(texte, str):
            return ""
        
        texte = texte.lower()
        
        # Corrections courantes
        corrections = {
            "ordi": "ordinateur",
            "pc": "ordinateur",
            "rame": "lent",
            "wiffi": "wifi",
            "wify": "wifi",
            "bloqué": "bloque",
            "internet": "réseau",
            "connexion": "réseau",
            "plante": "crash",
            "freeze": "fige",
            "ecran noir": "noir",
            "demarre pas": "démarre"
        }
        
        for ancien, nouveau in corrections.items():
            texte = texte.replace(ancien, nouveau)
        
        return texte
    
    def recherche_avancee(self, question: str) -> List[Tuple[dict, int]]:
        """Recherche avancée avec pondération des termes"""
        self.charger()
        
        if self.df is None or self.df.empty:
            return []
        
        # Vérifier le cache
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        if cache_key in self.cache_recherche:
            return self.cache_recherche[cache_key]
        
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)
        
        resultats = []
        
        for _, panne in self.df.iterrows():
            score = 0
            
            # Champs à rechercher avec pondération
            champs = {
                "titre": 10,
                "tags": 8,
                "description": 5,
                "diagnostic": 3
            }
            
            for champ, poids in champs.items():
                texte_champ = self.normaliser(str(panne[champ]))
                
                for mot in mots:
                    if len(mot) < 2:
                        continue
                    
                    # Recherche exacte
                    if mot in texte_champ:
                        score += poids
                    
                    # Recherche partielle
                    if any(partie in texte_champ for partie in mot.split()):
                        score += poids // 2
            
            if score > 0:
                resultats.append((dict(panne), score))
        
        # Trier par score décroissant
        resultats.sort(key=lambda x: x[1], reverse=True)
        
        # Mettre en cache
        self.cache_recherche[cache_key] = resultats[:10]
        
        return resultats[:10]

# ==================================================
# AUTHENTIFICATION SUPABASE
# ==================================================

def authentification():
    """Gère l'authentification des utilisateurs"""
    st.sidebar.markdown("## 👤 Compte")
    
    if st.session_state.user:
        # Utilisateur connecté
        st.sidebar.success(f"✅ Connecté : {st.session_state.user.email}")
        st.sidebar.info(f"📊 Recherches utilisées : {st.session_state.recherches}")
        
        if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
            try:
                if supabase:
                    supabase.auth.sign_out()
            except:
                pass
            
            st.session_state.user = None
            st.session_state.recherches = 0
            st.rerun()
        
        return
    
    # Pas connecté
    if not SUPABASE_OK:
        st.sidebar.error("Supabase non disponible")
        return
    
    choix = st.sidebar.radio("Action", ["🔐 Connexion", "📝 Créer un compte"])
    
    with st.sidebar:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_password")
        
        if choix == "📝 Créer un compte":
            if st.button("Créer mon compte", use_container_width=True, type="primary"):
                if email and password:
                    try:
                        supabase.auth.sign_up({
                            "email": email,
                            "password": password
                        })
                        st.success("✅ Compte créé ! Vérifiez votre email.")
                    except Exception as e:
                        st.error(f"❌ Erreur : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs")
        
        else:  # Connexion
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email and password:
                    try:
                        resultat = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        st.session_state.user = resultat.user
                        st.success("✅ Connexion réussie !")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur de connexion : {str(e)}")
                else:
                    st.warning("Veuillez remplir tous les champs")

# ==================================================
# PROFIL / PREMIUM
# ==================================================

def afficher_profil():
    """Affiche les informations du profil utilisateur"""
    if not st.session_state.user:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 Statistiques")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Recherches", st.session_state.recherches)
    
    if st.session_state.premium:
        st.sidebar.success("⭐ Compte Premium")
        st.sidebar.progress(1.0, text="Débloqué")
    else:
        restant = max(0, LIMITE_GRATUITE - st.session_state.recherches)
        st.metric("Restant", restant)
        
        # Barre de progression
        progression = min(st.session_state.recherches / LIMITE_GRATUITE, 1.0)
        st.sidebar.progress(progression, text=f"{int(progression * 100)}%")
        
        if st.session_state.recherches >= LIMITE_GRATUITE:
            st.sidebar.warning("⚠️ Limite atteinte")
        
        if st.sidebar.button("🚀 Passer Premium", use_container_width=True):
            st.sidebar.info("Premium bientôt disponible")

# ==================================================
# INTERFACE PRINCIPALE
# ==================================================

def afficher_resultats(resultats: List[Tuple[dict, int]]):
    """Affiche les résultats de recherche avec filtres"""
    if not resultats:
        st.warning("Aucun diagnostic trouvé")
        return
    
    st.success(f"✅ {len(resultats)} résultat(s) trouvé(s)")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.selectbox("Filtrer par catégorie", ["Toutes"] + sorted(set(r[0]["categorie"] for r in resultats))) != "Toutes":
            # Filtrage des résultats
            pass
    with col2:
        st.selectbox("Trier par", ["Pertinence", "Niveau", "Date"])
    with col3:
        st.slider("Niveau minimum", 1, 5, 1)
    
    # Affichage des résultats
    for panne, score in resultats:
        niveau_emoji = "🟢" if panne["niveau"] <= 2 else "🟡" if panne["niveau"] <= 3 else "🔴"
        
        with st.expander(
            f"{niveau_emoji} **{panne['titre']}**  "
            f"*(Pertinence: {score} pts, Niveau: {panne['niveau']}/5)*"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📂 Catégorie :** {panne['categorie']}")
                st.markdown(f"**📋 Diagnostic :**\n{panne['diagnostic']}")
                st.markdown(f"**🔧 Procédure :**\n{panne['procedure']}")
                
                if panne.get("questions"):
                    with st.expander("❓ Questions d'aide"):
                        st.info(panne["questions"])
            
            with col2:
                # Tags
                tags = panne["tags"].split(",") if panne["tags"] else []
                for tag in tags[:3]:  # Afficher seulement les 3 premiers tags
                    st.chip(tag.strip())
                
                # Score de pertinence
                st.metric("Score", f"{score} pts")
                
                # Niveau
                if panne["niveau"] <= 2:
                    st.success("✅ Niveau: Débutant")
                elif panne["niveau"] <= 3:
                    st.warning("⚠️ Niveau: Intermédiaire")
                else:
                    st.error("🔴 Niveau: Avancé")
                
                # Bouton d'action
                if st.button("📋 Copier la procédure", key=f"copy_{panne['id']}"):
                    st.toast("Procédure copiée !")

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    init_session()
    creer_base()
    remplir_base()
    
    # Sidebar
    authentification()
    afficher_profil()
    
    # Corps principal
    st.markdown("# 🤖 Assistant Dépannage IT")
    st.markdown("""
    Décrivez votre problème informatique en détail, et je vous aiderai à le résoudre.
    
    **Exemples :**
    - Mon PC est très lent
    - La connexion WiFi ne fonctionne pas
    - L'ordinateur ne démarre pas
    - Un logiciel plante systématiquement
    """)
    
    # Initialiser le moteur de recherche
    if st.session_state.moteur is None:
        st.session_state.moteur = RechercheIT()
    
    # Zone de recherche
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            question = st.text_area(
                "Votre problème :",
                height=100,
                placeholder="Décrivez votre problème informatique en détail...",
                key="question_input"
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                if question.strip():
                    # Vérification de la limite
                    if (st.session_state.user and 
                        not st.session_state.premium and 
                        st.session_state.recherches >= LIMITE_GRATUITE):
                        st.error("⚠️ Limite gratuite atteinte. Passez Premium pour continuer.")
                    else:
                        with st.spinner("Recherche en cours..."):
                            resultats = st.session_state.moteur.recherche_avancee(question)
                            
                            if st.session_state.user:
                                st.session_state.recherches += 1
                            
                            st.session_state.resultats = resultats
                else:
                    st.warning("Veuillez décrire votre problème.")
    
    # Afficher les résultats s'ils existent
    if "resultats" in st.session_state and st.session_state.resultats:
        afficher_resultats(st.session_state.resultats)
    elif "resultats" in st.session_state:
        st.info("💡 Décrivez votre problème ci-dessus pour obtenir de l'aide.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>Assistant IT Pro v2.0 - Développé avec ❤️</small>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# DEMARRAGE
# ==================================================

if __name__ == "__main__":
    main()

      

               
