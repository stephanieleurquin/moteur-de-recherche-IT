import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
import hashlib

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Assistant IT Pro - MONÉTISATION",
    page_icon="💰",
    layout="wide"
)

DB = "assistant_it_ia.db"
LIMITE_GRATUITE = 3  # 3 recherches gratuites seulement !

# ==================================================
# SESSION
# ==================================================

def init_session():
    defaults = {
        "user": None,
        "recherches": 0,
        "premium": False,
        "plan": "gratuit",
        "moteur": None,
        "page": "accueil"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==================================================
# BASE DE DONNÉES
# ==================================================

@st.cache_resource
def connexion_db():
    try:
        conn = sqlite3.connect(DB, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except:
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
            titre TEXT, description TEXT, diagnostic TEXT,
            procedure TEXT, questions TEXT, categorie TEXT,
            niveau INTEGER, tags TEXT
        )
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE, password TEXT,
            plan TEXT DEFAULT 'gratuit',
            premium BOOLEAN DEFAULT 0
        )
        """)
        conn.commit()
    except:
        pass
    finally:
        if conn:
            conn.close()

def remplir_base():
    conn = connexion_db()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pannes")
        if cur.fetchone()[0] == 0:
            donnees = [
                ("PC très lent", "L'ordinateur est lent", "Manque de ressources", 
                 "1- Nettoyer le disque\n2- Désactiver les programmes", 
                 "Depuis quand ?", "Performance", 2, "lent,pc"),
                ("WiFi impossible", "Pas de connexion WiFi", "Problème réseau",
                 "1- Redémarrer la box\n2- Vérifier le WiFi",
                 "Autres appareils ?", "Réseau", 2, "wifi,internet"),
                ("Windows ne démarre pas", "Écran noir au démarrage", "Fichier système",
                 "1- Mode sans échec\n2- Réparation système",
                 "Message d'erreur ?", "Logiciel", 4, "windows,demarrage")
            ]
            cur.executemany("""
            INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags)
            VALUES (?,?,?,?,?,?,?,?)
            """, donnees)
            conn.commit()
    except:
        pass
    finally:
        if conn:
            conn.close()

# ==================================================
# MOTEUR DE RECHERCHE
# ==================================================

class RechercheIT:
    def __init__(self):
        self.df = None
    
    def charger(self):
        if self.df is None:
            conn = connexion_db()
            if conn:
                try:
                    self.df = pd.read_sql_query("SELECT * FROM pannes", conn)
                except:
                    self.df = pd.DataFrame()
                finally:
                    conn.close()
    
    def normaliser(self, texte):
        if not texte:
            return ""
        texte = texte.lower()
        corrections = {"ordi": "ordinateur", "pc": "ordinateur", "rame": "lent"}
        for old, new in corrections.items():
            texte = texte.replace(old, new)
        return texte
    
    def rechercher(self, question):
        self.charger()
        if self.df is None or self.df.empty:
            return []
        
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)
        resultats = []
        
        for _, panne in self.df.iterrows():
            score = 0
            texte = self.normaliser(f"{panne['titre']} {panne['tags']}")
            for mot in mots:
                if len(mot) > 1 and mot in texte:
                    score += 5
            if score > 0:
                resultats.append((dict(panne), score))
        
        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:10]

# ==================================================
# AUTHENTIFICATION
# ==================================================

def auth():
    st.sidebar.markdown("## 👤 Compte")
    
    if st.session_state.user:
        # AFFICHAGE DU PLAN AVEC COULEUR
        plan = st.session_state.get("plan", "gratuit")
        if plan == "premium":
            st.sidebar.success("⭐ PLAN PREMIUM ⭐")
            st.sidebar.balloons()
        else:
            st.sidebar.warning("🆓 PLAN GRATUIT")
        
        st.sidebar.success(f"✅ {st.session_state.user}")
        
        # BOUTON PREMIUM ÉVIDENT
        if plan != "premium":
            if st.sidebar.button("🚀 PASSER PREMIUM", type="primary", use_container_width=True):
                st.session_state.page = "premium"
                st.rerun()
        
        if st.sidebar.button("🚪 Déconnexion"):
            st.session_state.user = None
            st.session_state.recherches = 0
            st.session_state.plan = "gratuit"
            st.rerun()
        return
    
    with st.sidebar:
        email = st.text_input("Email")
        password = st.text_input("Mot de passe", type="password")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔐 Connexion", use_container_width=True):
                if email and password:
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            pwd = hashlib.sha256(password.encode()).hexdigest()
                            cur.execute(
                                "SELECT email, plan, premium FROM utilisateurs WHERE email = ? AND password = ?",
                                (email, pwd)
                            )
                            user = cur.fetchone()
                            if user:
                                st.session_state.user = user["email"]
                                st.session_state.plan = user["plan"] if user["plan"] else "gratuit"
                                st.session_state.premium = bool(user["premium"])
                                st.success("✅ Connecté !")
                                st.rerun()
                            else:
                                st.error("❌ Identifiants incorrects")
                        except:
                            st.error("Erreur")
                        finally:
                            conn.close()
        
        with col2:
            if st.button("📝 Créer", use_container_width=True):
                if email and password:
                    conn = connexion_db()
                    if conn:
                        try:
                            cur = conn.cursor()
                            pwd = hashlib.sha256(password.encode()).hexdigest()
                            cur.execute(
                                "INSERT INTO utilisateurs (email, password, plan) VALUES (?, ?, 'gratuit')",
                                (email, pwd)
                            )
                            conn.commit()
                            st.success("✅ Compte créé ! Connectez-vous")
                        except:
                            st.error("Email déjà utilisé")
                        finally:
                            conn.close()

# ==================================================
# PAGE PREMIUM (MONÉTISATION ÉVIDENTE)
# ==================================================

def page_premium():
    st.markdown("# 💰 PASSER À PREMIUM")
    st.markdown("## Profitez de fonctionnalités exclusives !")
    
    # BANNIÈRE ÉNORME
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 30px; border-radius: 20px; text-align: center; margin: 20px 0;'>
        <h1 style='color: white; font-size: 48px;'>🔥 OFFRE SPÉCIALE 🔥</h1>
        <h2 style='color: #FFD700; font-size: 36px;'>-50% sur Premium</h2>
        <p style='color: white; font-size: 24px;'>Seulement 4.95€/mois</p>
        <p style='color: #FFD700; font-size: 18px;'>Code: PREMIUM50</p>
    </div>
    """, unsafe_allow_html=True)
    
    # COMPARAISON ÉVIDENTE
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🆓 GRATUIT
        **0€**
        
        ❌ 3 recherches seulement  
        ❌ Pas d'export  
        ❌ Pas de support  
        ❌ Publicités  
        ❌ Réponses basiques
        """)
    
    with col2:
        st.markdown("""
        ### ⭐ PREMIUM
        **9.90€/mois**
        
        ✅ Recherches ILLIMITÉES  
        ✅ Export PDF  
        ✅ Support prioritaire  
        ✅ Pas de publicités  
        ✅ Diagnostics avancés  
        ✅ Historique complet
        """)
    
    # BOUTON D'ABONNEMENT ÉNORME
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⭐ PASSER À PREMIUM MAINTENANT ⭐", 
                    type="primary", 
                    use_container_width=True):
            if st.session_state.user:
                conn = connexion_db()
                if conn:
                    try:
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE utilisateurs SET plan = 'premium', premium = 1 WHERE email = ?",
                            (st.session_state.user,)
                        )
                        conn.commit()
                        st.session_state.plan = "premium"
                        st.session_state.premium = True
                        st.success("🎉 FÉLICITATIONS ! Vous êtes maintenant Premium !")
                        st.balloons()
                        st.rerun()
                    except:
                        st.error("Erreur")
                    finally:
                        conn.close()
            else:
                st.warning("Connectez-vous d'abord !")
    
    # AVANTAGES
    st.markdown("---")
    st.markdown("## ✨ Ce que vous gagnez avec Premium")
    
    cols = st.columns(4)
    avantages = [
        ("♾️", "Illimité", "Recherches sans limite"),
        ("📄", "Export PDF", "Sauvegardez vos solutions"),
        ("⚡", "Rapide", "Support prioritaire"),
        ("🎯", "Précis", "Diagnostics avancés")
    ]
    
    for i, (emoji, titre, desc) in enumerate(avantages):
        with cols[i]:
            st.markdown(f"""
            <div style='text-align: center; padding: 20px; border: 2px solid #667eea; border-radius: 10px;'>
                <h1 style='font-size: 48px;'>{emoji}</h1>
                <h3>{titre}</h3>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

# ==================================================
# COMPTEUR DE RECHERCHES (TRÈS VISIBLE)
# ==================================================

def afficher_compteur():
    if not st.session_state.user:
        st.info("🔑 Connectez-vous pour effectuer des recherches")
        return
    
    plan = st.session_state.get("plan", "gratuit")
    
    if plan == "premium":
        st.sidebar.success("⭐ PREMIUM - ILLIMITÉ ⭐")
        return
    
    # COMPTEUR TRÈS VISIBLE POUR GRATUIT
    restant = max(0, LIMITE_GRATUITE - st.session_state.recherches)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 VOTRE STATUT")
    
    # BARRE DE PROGRESSION COLORÉE
    progression = min(st.session_state.recherches / LIMITE_GRATUITE, 1.0)
    st.sidebar.progress(progression, text=f"Utilisé : {st.session_state.recherches}/{LIMITE_GRATUITE}")
    
    if restant > 0:
        st.sidebar.success(f"✅ {restant} recherches restantes")
    else:
        st.sidebar.error("❌ PLUS DE RECHERCHES GRATUITES !")
        st.sidebar.warning("Passez Premium pour continuer")
        
        # BOUTON PREMIUM ÉVIDENT
        if st.sidebar.button("🚀 PASSER PREMIUM", type="primary", use_container_width=True):
            st.session_state.page = "premium"
            st.rerun()

# ==================================================
# PAGE PRINCIPALE
# ==================================================

def main():
    init_session()
    creer_base()
    remplir_base()
    
    # SIDEBAR
    auth()
    afficher_compteur()
    
    # NAVIGATION AVEC BOUTON PREMIUM
    st.sidebar.markdown("---")
    menu = ["🏠 Accueil"]
    
    if st.session_state.get("plan") != "premium":
        menu.append("⭐ PASSER PREMIUM ⭐")
    
    choice = st.sidebar.radio("Navigation", menu)
    
    if choice == "⭐ PASSER PREMIUM ⭐":
        page_premium()
        return
    
    # PAGE D'ACCUEIL
    st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🤖 Assistant Dépannage IT</h1>
        <p>Décrivez votre problème, je vous aiderai à le résoudre</p>
    </div>
    """, unsafe_allow_html=True)
    
    # AFFICHAGE DU STATUT PREMIUM
    if st.session_state.get("plan") == "premium":
        st.success("⭐ Vous êtes Premium - Recherches ILLIMITÉES !")
        st.balloons()
    else:
        if st.session_state.user:
            restant = max(0, LIMITE_GRATUITE - st.session_state.recherches)
            if restant > 0:
                st.info(f"🆓 {restant} recherches gratuites restantes")
            else:
                st.error("🚨 PLUS DE RECHERCHES GRATUITES !")
                if st.button("⭐ PASSER PREMIUM MAINTENANT", type="primary"):
                    st.session_state.page = "premium"
                    st.rerun()
    
    # MOTEUR DE RECHERCHE
    if st.session_state.moteur is None:
        st.session_state.moteur = RechercheIT()
    
    question = st.text_area(
        "💬 Votre problème :",
        height=100,
        placeholder="Exemple : mon PC est lent, le wifi ne marche pas..."
    )
    
    if st.button("🔍 Rechercher", type="primary", use_container_width=True):
        if not st.session_state.user:
            st.warning("🔑 Connectez-vous pour effectuer une recherche")
        elif st.session_state.get("plan") != "premium" and st.session_state.recherches >= LIMITE_GRATUITE:
            st.error("🚨 LIMITE ATTEINTE !")
            st.info("Passez Premium pour continuer vos recherches")
            if st.button("⭐ PASSER PREMIUM", type="primary"):
                st.session_state.page = "premium"
                st.rerun()
        elif question.strip():
            with st.spinner("Recherche..."):
                resultats = st.session_state.moteur.rechercher(question)
                st.session_state.recherches += 1
                
                if resultats:
                    st.success(f"✅ {len(resultats)} résultat(s)")
                    for panne, score in resultats:
                        with st.expander(f"📌 {panne['titre']} (Pertinence: {score})"):
                            st.markdown(f"**Diagnostic:** {panne['diagnostic']}")
                            st.markdown(f"**Procédure:**\n{panne['procedure']}")
                            if panne.get('questions'):
                                st.info(f"❓ {panne['questions']}")
                else:
                    st.warning("Aucun résultat trouvé")
        else:
            st.warning("Décrivez votre problème")
    
    # FOOTER
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <small>Assistant IT Pro - Version Premium</small>
    </div>
    """, unsafe_allow_html=True)

# ==================================================
# LANCEMENT
# ==================================================

if __name__ == "__main__":
    main()
           
