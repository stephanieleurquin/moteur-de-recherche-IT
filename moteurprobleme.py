import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
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
# SESSION UTILISATEUR
# ==================================================

def init_session():
    """Initialise les variables de session"""
    defaults = {
        "user": None,
        "recherches": 0,
        "premium": False,
        "historique": [],
        "moteur": None,
        "users": {}  # Stockage local des utilisateurs
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
            password TEXT NOT NULL,
            premium BOOLEAN DEFAULT 0,
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
        if conn:
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
                ),
                (
                    "Imprimante ne fonctionne pas",
                    "L'imprimante ne répond pas, ne s'allume pas ou n'imprime pas",
                    "Problème de connexion, pilote obsolète, bourrage papier ou encre vide",
                    "1️⃣ Vérifier que l'imprimante est allumée et connectée\n2️⃣ Vérifier le niveau d'encre/toner\n3️⃣ Réinstaller les pilotes\n4️⃣ Vérifier les bourrages papier",
                    "L'imprimante est-elle connectée en USB ou WiFi ?",
                    "Périphériques",
                    3,
                    "imprimante,impression,encre,bourrage,driver"
                ),
                (
                    "Email ne s'envoie pas",
                    "Impossible d'envoyer des emails, erreur de serveur",
                    "Paramètres SMTP incorrects, connexion internet, ou serveur bloqué",
                    "1️⃣ Vérifier les paramètres SMTP\n2️⃣ Tester avec un autre client email\n3️⃣ Vérifier la connexion internet\n4️⃣ Contacter l'administrateur",
                    "Utilisez-vous Outlook, Gmail ou un autre client ?",
                    "Communication",
                    3,
                    "email,smtp,envoi,serveur,parametres"
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
        if conn:
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
                if conn:
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
            "demarre pas": "démarre",
            "imp": "imprimante",
            "mail": "email"
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
# AUTHENTIFICATION LOCALE
# ==================================================

def authentification_locale():
    """Gère l'authentification des utilisateurs en local"""
    st.sidebar.markdown("## 👤 Compte")
    
    if st.session_state.user:
        # Utilisateur connecté
        st.sidebar.success(f"✅ Connecté : {st.session_state.user}")
        st.sidebar.info(f"📊 Recherches utilisées : {st.session_state.recherches}")
        
        if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.recherches = 0
            st.rerun()
        
        return
    
    # Pas connecté
    choix = st.sidebar.radio("Action", ["🔐 Connexion", "📝 Créer un compte"])
    
    with st.sidebar:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Mot de passe", type="password", key="login_password")
        
        if choix == "📝 Créer un compte":
            if st.button("Créer mon compte", use_container_width=True, type="primary"):
                if email and password:
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            # Vérifier si l'utilisateur existe déjà
                            cur.execute("SELECT email FROM utilisateurs WHERE email = ?", (email,))
                            if cur.fetchone():
                                st.error("❌ Cet email est déjà utilisé")
                            else:
                                # Créer l'utilisateur
                                cur.execute(
                                    "INSERT INTO utilisateurs (email, password, premium) VALUES (?, ?, 0)",
                                    (email, hashlib.sha256(password.encode()).hexdigest())
                                )
                                conn.commit()
                                st.success("✅ Compte créé avec succès !")
                        except sqlite3.Error as e:
                            st.error(f"❌ Erreur : {str(e)}")
                        finally:
                            if conn:
                                conn.close()
                else:
                    st.warning("Veuillez remplir tous les champs")
        
        else:  # Connexion
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email and password:
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            password_hash = hashlib.sha256(password.encode()).hexdigest()
                            cur.execute(
                                "SELECT email, premium FROM utilisateurs WHERE email = ? AND password = ?",
                                (email, password_hash)
                            )
                            user = cur.fetchone()
                            if user:
                                st.session_state.user = user["email"]
                                st.session_state.premium = bool(user["premium"])
                                st.success("✅ Connexion réussie !")
                                st.rerun()
                            else:
                                st.error("❌ Email ou mot de passe incorrect")
                        except sqlite3.Error as e:
                            st.error(f"❌ Erreur : {str(e)}")
                        finally:
                            if conn:
                                conn.close()
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
            conn = connexion_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute(
                        "UPDATE utilisateurs SET premium = 1 WHERE email = ?",
                        (st.session_state.user,)
                    )
                    conn.commit()
                    st.session_state.premium = True
                    st.sidebar.success("✅ Premium activé !")
                    st.rerun()
                except sqlite3.Error as e:
                    st.sidebar.error(f"❌ Erreur : {str(e)}")
                finally:
                    if conn:
                        conn.close()

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
        categories = ["Toutes"] + sorted(set(r[0]["categorie"] for r in resultats if r[0].get("categorie")))
        categorie_filtre = st.selectbox("Filtrer par catégorie", categories)
    with col2:
        st.selectbox("Trier par", ["Pertinence", "Niveau", "Date"])
    with col3:
        niveau_min = st.slider("Niveau minimum", 1, 5, 1)
    
    # Filtrer les résultats
    resultats_filtres = resultats
    if categorie_filtre != "Toutes":
        resultats_filtres = [r for r in resultats if r[0].get("categorie") == categorie_filtre]
    
    resultats_filtres = [r for r in resultats_filtres if r[0].get("niveau", 1) >= niveau_min]
    
    # Affichage des résultats
    for panne, score in resultats_filtres:
        niveau_emoji = "🟢" if panne.get("niveau", 1) <= 2 else "🟡" if panne.get("niveau", 1) <= 3 else "🔴"
        
        with st.expander(
            f"{niveau_emoji} **{panne.get('titre', 'Sans titre')}**  "
            f"*(Pertinence: {score} pts, Niveau: {panne.get('niveau', 1)}/5)*"
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**📂 Catégorie :** {panne.get('categorie', 'Non catégorisé')}")
                st.markdown(f"**📋 Diagnostic :**\n{panne.get('diagnostic', 'Non disponible')}")
                st.markdown(f"**🔧 Procédure :**\n{panne.get('procedure', 'Non disponible')}")
                
                if panne.get("questions"):
                    with st.expander("❓ Questions d'aide"):
                        st.info(panne["questions"])
            
            with col2:
                # Tags
                if panne.get("tags"):
                    tags = panne["tags"].split(",") if isinstance(panne["tags"], str) else []
                    for tag in tags[:3]:  # Afficher seulement les 3 premiers tags
                        st.chip(tag.strip())
                
                # Score de pertinence
                st.metric("Score", f"{score} pts")
                
                # Niveau
                niveau = panne.get("niveau", 1)
                if niveau <= 2:
                    st.success("✅ Niveau: Débutant")
                elif niveau <= 3:
                    st.warning("⚠️ Niveau: Intermédiaire")
                else:
                    st.error("🔴 Niveau: Avancé")

def main():
    """Fonction principale de l'application"""
    
    # Initialisation
    init_session()
    creer_base()
    remplir_base()
    
    # Sidebar
    authentification_locale()
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
    - Mon imprimante ne fonctionne pas
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
    if "resultats" in st.session_state:
        if st.session_state.resultats:
            afficher_resultats(st.session_state.resultats)
        else:
            st.info("💡 Aucun résultat trouvé. Essayez de reformuler votre problème.")
    
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
