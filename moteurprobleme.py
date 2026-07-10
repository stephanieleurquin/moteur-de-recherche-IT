import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime, timedelta
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
LIMITE_GRATUITE = 5  # 5 recherches gratuites par jour

# ==================================================
# PRIX ET OFFRES
# ==================================================

OFFRES = {
    "gratuit": {
        "nom": "Gratuit",
        "prix": "0€",
        "recherches": 5,
        "couleur": "🆓",
        "features": [
            "✅ 5 recherches/jour",
            "✅ Diagnostics basiques",
            "✅ Procédures standards",
            "❌ Export PDF",
            "❌ Support prioritaire"
        ]
    },
    "pro": {
        "nom": "Pro",
        "prix": "9.90€/mois",
        "prix_an": "79€/an",
        "recherches": float('inf'),
        "couleur": "🚀",
        "features": [
            "✅ Recherches illimitées",
            "✅ Diagnostics avancés",
            "✅ Procédures détaillées",
            "✅ Export PDF",
            "✅ Support prioritaire",
            "✅ Pas de publicité"
        ]
    },
    "business": {
        "nom": "Business",
        "prix": "29.90€/mois",
        "prix_an": "249€/an",
        "recherches": float('inf'),
        "couleur": "🏢",
        "features": [
            "✅ Tout Pro inclus",
            "✅ Accès API",
            "✅ 5 comptes utilisateurs",
            "✅ Statistiques détaillées",
            "✅ Support 24/7"
        ]
    }
}

# ==================================================
# SESSION UTILISATEUR
# ==================================================

def init_session():
    defaults = {
        "user": None,
        "recherches": 0,
        "premium": False,
        "plan": "gratuit",
        "historique": [],
        "moteur": None,
        "users": {},
        "page": "accueil",
        "date_recherche": datetime.now().date().isoformat()
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==================================================
# BASE SQLITE
# ==================================================

@st.cache_resource
def connexion_db():
    try:
        conn = sqlite3.connect(DB, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        st.error(f"Erreur de connexion à la base de données: {e}")
        return None

def creer_base():
    conn = connexion_db()
    if conn is None:
        return
    
    try:
        cur = conn.cursor()
        
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
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            plan TEXT DEFAULT 'gratuit',
            premium BOOLEAN DEFAULT 0,
            recherches_total INTEGER DEFAULT 0,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    "1️⃣ Ouvrir le Gestionnaire des tâches (Ctrl+Alt+Suppr)\n2️⃣ Désactiver les programmes inutiles au démarrage\n3️⃣ Nettoyer le disque\n4️⃣ Augmenter la mémoire RAM si possible",
                    "Depuis quand le PC est-il lent ? Avez-vous installé un nouveau logiciel ?",
                    "Performance",
                    2,
                    "lent,rame,ordinateur,performance"
                ),
                (
                    "WiFi impossible",
                    "Impossible de se connecter au réseau WiFi, pas d'internet",
                    "Problème de réseau, box défaillante, pilote WiFi obsolète",
                    "1️⃣ Redémarrer la box internet\n2️⃣ Vérifier les autres appareils\n3️⃣ Réinstaller le pilote WiFi\n4️⃣ Réinitialiser les paramètres réseau",
                    "Les autres appareils ont-ils internet ?",
                    "Réseau",
                    2,
                    "wifi,internet,réseau,connexion"
                ),
                (
                    "Windows ne démarre pas",
                    "L'ordinateur s'allume mais Windows ne démarre pas, écran noir",
                    "Fichier système endommagé, disque dur défaillant",
                    "1️⃣ Démarrer en Mode sans échec (F8)\n2️⃣ Utiliser l'outil de réparation Windows\n3️⃣ Vérifier l'intégrité du disque",
                    "Quel message d'erreur s'affiche ?",
                    "Logiciel",
                    4,
                    "windows,démarrage,erreur"
                ),
                (
                    "Imprimante ne fonctionne pas",
                    "L'imprimante ne répond pas, n'imprime pas",
                    "Problème de connexion, pilote obsolète, bourrage papier",
                    "1️⃣ Vérifier que l'imprimante est allumée\n2️⃣ Vérifier le niveau d'encre\n3️⃣ Réinstaller les pilotes\n4️⃣ Vérifier les bourrages",
                    "L'imprimante est-elle connectée en USB ou WiFi ?",
                    "Périphériques",
                    3,
                    "imprimante,impression,encre"
                ),
                (
                    "Email ne s'envoie pas",
                    "Impossible d'envoyer des emails, erreur de serveur",
                    "Paramètres SMTP incorrects, connexion internet",
                    "1️⃣ Vérifier les paramètres SMTP\n2️⃣ Tester avec un autre client\n3️⃣ Vérifier la connexion internet",
                    "Utilisez-vous Outlook, Gmail ou autre ?",
                    "Communication",
                    3,
                    "email,smtp,envoi"
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
# MOTEUR DE RECHERCHE
# ==================================================

class RechercheIT:
    def __init__(self):
        self.df = None
        self.cache_recherche = {}
        
    def charger(self):
        if self.df is None:
            conn = connexion_db()
            if conn is None:
                self.df = pd.DataFrame()
                return
            try:
                self.df = pd.read_sql_query("SELECT * FROM pannes", conn)
            except sqlite3.Error as e:
                st.error(f"Erreur de chargement: {e}")
                self.df = pd.DataFrame()
            finally:
                if conn:
                    conn.close()
    
    def normaliser(self, texte: str) -> str:
        if not isinstance(texte, str):
            return ""
        texte = texte.lower()
        corrections = {
            "ordi": "ordinateur",
            "pc": "ordinateur",
            "rame": "lent",
            "wiffi": "wifi",
            "bloqué": "bloque",
            "plante": "crash"
        }
        for ancien, nouveau in corrections.items():
            texte = texte.replace(ancien, nouveau)
        return texte
    
    def recherche_avancee(self, question: str):
        self.charger()
        if self.df is None or self.df.empty:
            return []
        
        cache_key = hashlib.md5(question.lower().encode()).hexdigest()
        if cache_key in self.cache_recherche:
            return self.cache_recherche[cache_key]
        
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)
        resultats = []
        
        for _, panne in self.df.iterrows():
            score = 0
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
                    if mot in texte_champ:
                        score += poids
            
            if score > 0:
                resultats.append((dict(panne), score))
        
        resultats.sort(key=lambda x: x[1], reverse=True)
        self.cache_recherche[cache_key] = resultats[:10]
        return resultats[:10]

# ==================================================
# AUTHENTIFICATION
# ==================================================

def authentification():
    st.sidebar.markdown("## 👤 Compte")
    
    if st.session_state.user:
        st.sidebar.success(f"✅ {st.session_state.user}")
        
        # Afficher le plan
        plan = st.session_state.get("plan", "gratuit")
        if plan == "pro":
            st.sidebar.success("🚀 Plan Pro")
        elif plan == "business":
            st.sidebar.success("🏢 Plan Business")
        else:
            st.sidebar.info("🆓 Plan Gratuit")
        
        if st.sidebar.button("🚪 Déconnexion", use_container_width=True):
            st.session_state.user = None
            st.session_state.recherches = 0
            st.session_state.plan = "gratuit"
            st.rerun()
        return
    
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
                            cur.execute("SELECT email FROM utilisateurs WHERE email = ?", (email,))
                            if cur.fetchone():
                                st.error("❌ Email déjà utilisé")
                            else:
                                cur.execute(
                                    "INSERT INTO utilisateurs (email, password, plan) VALUES (?, ?, 'gratuit')",
                                    (email, hashlib.sha256(password.encode()).hexdigest())
                                )
                                conn.commit()
                                st.success("✅ Compte créé !")
                                st.session_state.user = email
                                st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"❌ Erreur : {str(e)}")
                        finally:
                            if conn:
                                conn.close()
                else:
                    st.warning("Veuillez remplir tous les champs")
        
        else:
            if st.button("Se connecter", use_container_width=True, type="primary"):
                if email and password:
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            password_hash = hashlib.sha256(password.encode()).hexdigest()
                            cur.execute(
                                "SELECT email, plan, premium FROM utilisateurs WHERE email = ? AND password = ?",
                                (email, password_hash)
                            )
                            user = cur.fetchone()
                            if user:
                                st.session_state.user = user["email"]
                                st.session_state.plan = user["plan"] if user["plan"] else "gratuit"
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
# PAGE DES OFFRES (MONÉTISATION)
# ==================================================

def page_offres():
    st.markdown("# 💰 Offres et Tarifs")
    st.markdown("Choisissez l'offre qui vous convient le mieux")
    
    # Afficher les offres
    col1, col2, col3 = st.columns(3)
    
    # Offre Gratuite
    with col1:
        with st.container():
            st.markdown("### 🆓 Gratuit")
            st.markdown("**0€ / mois**")
            st.markdown("---")
            for feature in OFFRES["gratuit"]["features"]:
                st.markdown(feature)
            st.button("🔄 Actuel", disabled=True, use_container_width=True)
    
    # Offre Pro
    with col2:
        with st.container(border=True):
            st.markdown("### 🚀 Pro")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**9.90€ / mois**")
            with col_b:
                st.markdown("**79€ / an**")
            st.markdown("---")
            for feature in OFFRES["pro"]["features"]:
                st.markdown(feature)
            
            if st.session_state.user:
                if st.button("⭐ Passer à Pro", use_container_width=True, type="primary"):
                    # Simuler un paiement
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE utilisateurs SET plan = 'pro', premium = 1 WHERE email = ?",
                                (st.session_state.user,)
                            )
                            conn.commit()
                            st.session_state.plan = "pro"
                            st.session_state.premium = True
                            st.success("🎉 Vous êtes maintenant Pro !")
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Erreur: {e}")
                        finally:
                            if conn:
                                conn.close()
            else:
                st.info("Connectez-vous pour souscrire")
    
    # Offre Business
    with col3:
        with st.container():
            st.markdown("### 🏢 Business")
            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("**29.90€ / mois**")
            with col_d:
                st.markdown("**249€ / an**")
            st.markdown("---")
            for feature in OFFRES["business"]["features"]:
                st.markdown(feature)
            
            if st.session_state.user:
                if st.button("⭐ Passer à Business", use_container_width=True, type="primary"):
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            cur.execute(
                                "UPDATE utilisateurs SET plan = 'business', premium = 1 WHERE email = ?",
                                (st.session_state.user,)
                            )
                            conn.commit()
                            st.session_state.plan = "business"
                            st.session_state.premium = True
                            st.success("🎉 Vous êtes maintenant Business !")
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Erreur: {e}")
                        finally:
                            if conn:
                                conn.close()
            else:
                st.info("Connectez-vous pour souscrire")
    
    # Offres spéciales
    st.markdown("---")
    st.markdown("## 🎁 Offres Spéciales")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    
    with col_s1:
        st.info("""
        #### 🔥 Offre Launch
        -50% sur Pro
        
        **4.95€/mois**
        
        Code : `LAUNCH50`
        """)
    
    with col_s2:
        st.success("""
        #### 🎓 Offre Étudiant
        Pro à prix réduit
        
        **5.90€/mois**
        
        Justificatif requis
        """)
    
    with col_s3:
        st.warning("""
        #### 💼 Packs à la demande
        - 50 recherches : 15€
        - 100 recherches : 25€
        """)

# ==================================================
# AFFICHAGE DU COMPTEUR
# ==================================================

def afficher_compteur():
    if not st.session_state.user:
        return
    
    plan = st.session_state.get("plan", "gratuit")
    limite = OFFRES[plan]["recherches"]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 Statistiques")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Recherches", st.session_state.recherches)
    
    if limite == float('inf'):
        st.sidebar.success("♾️ Illimité")
    else:
        restant = max(0, limite - st.session_state.recherches)
        st.metric("Restant", restant)
        
        # Barre de progression
        progression = min(st.session_state.recherches / limite, 1.0)
        st.sidebar.progress(progression, text=f"{int(progression * 100)}%")
        
        if restant <= 2 and restant > 0:
            st.sidebar.warning("⚠️ Plus que quelques recherches !")
        
        if restant == 0:
            st.sidebar.error("❌ Limite atteinte !")
            if st.sidebar.button("🚀 Passer Pro"):
                st.session_state.page = "offres"
                st.rerun()

# ==================================================
# PAGE PRINCIPALE
# ==================================================

def afficher_resultats(resultats):
    if not resultats:
        st.warning("Aucun diagnostic trouvé")
        return
    
    st.success(f"✅ {len(resultats)} résultat(s) trouvé(s)")
    
    for panne, score in resultats:
        niveau_emoji = "🟢" if panne.get("niveau", 1) <= 2 else "🟡" if panne.get("niveau", 1) <= 3 else "🔴"
        
        with st.expander(
            f"{niveau_emoji} **{panne.get('titre', 'Sans titre')}** (Score: {score})"
        ):
            st.markdown(f"**📂 Catégorie :** {panne.get('categorie', 'Non catégorisé')}")
            st.markdown(f"**📋 Diagnostic :**\n{panne.get('diagnostic', 'Non disponible')}")
            st.markdown(f"**🔧 Procédure :**\n{panne.get('procedure', 'Non disponible')}")
            
            if panne.get("questions"):
                with st.expander("❓ Questions d'aide"):
                    st.info(panne["questions"])
            
            # Export PDF (uniquement pour Pro et Business)
            if st.session_state.get("plan") in ["pro", "business"]:
                if st.button(f"📄 Exporter en PDF", key=f"pdf_{panne['id']}"):
                    st.info("📄 PDF exporté (simulation)")

# ==================================================
# MAIN
# ==================================================

def main():
    init_session()
    creer_base()
    remplir_base()
    
    # Sidebar
    authentification()
    afficher_compteur()
    
    # Navigation
    menu = ["🏠 Accueil", "💰 Tarifs"]
    if st.session_state.user:
        menu.append("👤 Mon Compte")
    
    choice = st.sidebar.radio("📱 Navigation", menu)
    
    if choice == "💰 Tarifs":
        page_offres()
        return
    
    if choice == "👤 Mon Compte" and st.session_state.user:
        st.markdown("# 👤 Mon Compte")
        st.markdown(f"**Email :** {st.session_state.user}")
        st.markdown(f"**Plan :** {st.session_state.get('plan', 'gratuit')}")
        st.markdown(f"**Recherches :** {st.session_state.recherches}")
        
        if st.button("🗑️ Supprimer mon compte"):
            conn = connexion_db()
            if conn:
                try:
                    cur = conn.cursor()
                    cur.execute("DELETE FROM utilisateurs WHERE email = ?", (st.session_state.user,))
                    conn.commit()
                    st.session_state.user = None
                    st.success("Compte supprimé")
                    st.rerun()
                except sqlite3.Error as e:
                    st.error(f"Erreur: {e}")
                finally:
                    if conn:
                        conn.close()
        return
    
    # Page principale
    st.markdown("# 🤖 Assistant Dépannage IT")
    st.markdown("""
    Décrivez votre problème informatique, je vous aiderai à le résoudre !
    
    **Exemples :**
    - Mon PC est très lent
    - La connexion WiFi ne fonctionne pas
    - L'ordinateur ne démarre pas
    """)
    
    if st.session_state.moteur is None:
        st.session_state.moteur = RechercheIT()
    
    # Zone de recherche
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            question = st.text_area(
                "Votre problème :",
                height=100,
                placeholder="Décrivez votre problème en détail...",
                key="question_input"
            )
        with col2:
            st.write("")
            st.write("")
            if st.button("🔍 Rechercher", type="primary", use_container_width=True):
                if question.strip():
                    # Vérifier la limite
                    plan = st.session_state.get("plan", "gratuit")
                    limite = OFFRES[plan]["recherches"]
                    
                    if limite != float('inf') and st.session_state.recherches >= limite:
                        st.error("⚠️ Limite atteinte ! Passez Pro pour continuer.")
                        if st.button("🚀 Passer Pro"):
                            st.session_state.page = "offres"
                            st.rerun()
                    else:
                        with st.spinner("Recherche en cours..."):
                            resultats = st.session_state.moteur.recherche_avancee(question)
                            
                            if st.session_state.user:
                                st.session_state.recherches += 1
                            
                            st.session_state.resultats = resultats
                else:
                    st.warning("Veuillez décrire votre problème.")
    
    # Afficher les résultats
    if "resultats" in st.session_state:
        if st.session_state.resultats:
            afficher_resultats(st.session_state.resultats)
        else:
            st.info("💡 Aucun résultat trouvé. Essayez de reformuler.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>Assistant IT Pro - Version 2.0</small>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# LANCEMENT
# ==================================================

if __name__ == "__main__":
    main()
