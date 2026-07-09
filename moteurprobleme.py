import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import urllib.parse
import hashlib
import time
import re
from datetime import datetime
from typing import List, Dict, Tuple

DB = "assistant_it_ia.db"

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(
    page_title="Assistant IT Pro",
    page_icon="🤖",
    layout="wide"
)

# ==========================
# STYLES CSS
# ==========================
st.markdown("""
<style>
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
    }
    .confidence-bar {
        height: 8px;
        background: #2d2d44;
        border-radius: 10px;
        overflow: hidden;
        margin: 0.5rem 0;
    }
    .confidence-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    .result-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    .google-search-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ==========================
# FONCTION POUR AFFICHER GOOGLE SEARCH
# ==========================
def afficher_google_search():
    """Affiche la barre de recherche Google personnalisée"""

    st.markdown("""
    <div class="google-search-container">
        <h3 style="margin: 0;">🔍 Recherche Google</h3>
        <p style="color: #666; font-size: 0.9rem;">
            Recherchez sur tout le web depuis votre assistant IT.
        </p>
    </div>
    """, unsafe_allow_html=True)

    google_code = """
    <script async src="https://cse.google.com/cse.js?cx=70e26eb628d0e4736">
    </script>
    <div class="gcse-search"></div>
    """

    st.components.v1.html(google_code, height=400)


# ==========================
# MODELE IA
# ==========================
def connexion():
    return sqlite3.connect(DB)


def init_db():
    con = connexion()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pannes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT,
        description TEXT,
        diagnostic TEXT,
        procedure TEXT,
        questions TEXT,
        categorie TEXT,
        niveau INTEGER,
        tags TEXT,
        date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("SELECT COUNT(*) FROM pannes")
    if cur.fetchone()[0] == 0:
        donnees = [
            (
    "Souris qui ne fonctionne pas",
    "la souris ne répond plus, le curseur ne bouge pas",
    "Problème de souris : piles usées, récepteur USB mal branché.",
    "1️⃣ Changer les piles\n2️⃣ Rebrancher le récepteur USB\n3️⃣ Tester sur un autre port",
    "La souris s'allume-t-elle ?",
    "Périphériques",
    1,
    "souris,curseur,usb"
),
(
    "Ordinateur qui s'éteint tout seul",
    "le PC s'éteint soudainement, il redémarre sans raison",
    "Problème d'alimentation ou surchauffe.",
    "1️⃣ Vérifier la température\n2️⃣ Nettoyer les ventilateurs\n3️⃣ Tester une autre prise",
    "Le PC chauffe-t-il ?",
    "Matériel",
    3,
    "extinction,surchauffe,alimentation"
),
            (
                "PC très lent",
                "L'ordinateur est très lent, il rame, les programmes mettent du temps à s'ouvrir",
                "Problème de performance : disque dur plein ou lent, trop de programmes au démarrage.",
                "1️⃣ Ouvrir le Gestionnaire des Tâches\n2️⃣ Voir l'utilisation du CPU\n3️⃣ Nettoyer le disque",
                "Depuis quand l'ordinateur est-il lent ?",
                "Performance",
                2,
                "lent,rame,performance"
            ),
            (
                "Écran noir",
                "L'ordinateur démarre mais l'écran reste noir",
                "Problème d'affichage : câble défectueux, écran endommagé.",
                "1️⃣ Vérifier le câble HDMI\n2️⃣ Tester un autre écran\n3️⃣ Tester la RAM",
                "Le PC s'allume-t-il normalement ?",
                "Matériel",
                3,
                "ecran noir,image,affichage"
            ),
            (
                "Wi-Fi ne fonctionne pas",
                "le wifi ne fonctionne plus, internet est coupé",
                "Problème réseau : box internet en panne, pilote Wi-Fi corrompu.",
                "1️⃣ Redémarrer la box\n2️⃣ Redémarrer le PC\n3️⃣ Réinstaller le pilote Wi-Fi",
                "Les autres appareils ont-ils internet ?",
                "Réseau",
                2,
                "wifi,internet,connexion"
            )
        ]

        cur.executemany("""
        INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, donnees)

    con.commit()
    con.close()


# ==========================
# MOTEUR DE RECHERCHE
# ==========================
class RechercheIAPro:
    def __init__(self):
        self.cache = {}
        self.df = None

    @st.cache_data
    def charger_base_cache(_self):
        con = connexion()
        df = pd.read_sql_query("SELECT * FROM pannes", con)
        con.close()
        return df

    def charger_base(self):
        if self.df is None:
            self.df = self.charger_base_cache()

    def normaliser(self, texte):
        texte = str(texte).lower()
        corrections = {
            "rame": "lent",
            "ram": "lent",
            "bloque": "freeze",
            "wiffi": "wifi",
            "wify": "wifi",
            "ordi": "ordinateur",
            "pc": "ordinateur"
        }
        for ancien, nouveau in corrections.items():
            texte = texte.replace(ancien, nouveau)
        return texte

    def rechercher_ia(self, question, top_k=3):
        self.charger_base()
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)

        resultats = []
        for _, panne in self.df.iterrows():
            score = 0
            titre = self.normaliser(panne["titre"])
            tags = self.normaliser(panne["tags"])

            for mot in mots:
                if len(mot) < 2:
                    continue
                if mot in titre:
                    score += 10
                if mot in tags:
                    score += 8

            if score > 0:
                resultats.append((dict(panne), score))

        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:top_k]


# ==========================
# INTERFACE
# ==========================
def main():
    init_db()

    if 'recherche_pro' not in st.session_state:
        st.session_state.recherche_pro = RechercheIAPro()

    with st.sidebar:
        st.markdown("### 🤖 Assistant IT Pro")
        st.markdown("---")

        con = connexion()
        total = pd.read_sql_query("SELECT COUNT(*) as total FROM pannes", con).iloc[0]['total']
        con.close()
        st.metric("📚 Diagnostics disponibles", total)

        st.markdown("---")
        st.markdown("#### 💡 Conseils")
        st.info("""
        Pour un meilleur diagnostic :
        - Décrivez précisément le problème
        - Mentionnez les symptômes
        - Précisez le contexte
        """)

    st.markdown('<p class="main-title">🤖 Assistant Dépannage IT</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔍 Recherche IA", "🌐 Recherche Google"])

    with tab1:
        question = st.text_area(
            "Décrivez votre problème :",
            placeholder="Exemple : mon PC est très lent...",
            height=100,
            key="search_input"
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            rechercher = st.button("🔍 Analyser", use_container_width=True, type="primary")

        if rechercher and question:
            resultats = st.session_state.recherche_pro.rechercher_ia(question)
            if not resultats:
                st.error("❌ Aucun diagnostic trouvé")
            else:
                for i, (r, s) in enumerate(resultats, 1):
                    with st.expander(f"{i}. {r['titre']} (Score: {s})"):
                        st.write(r['diagnostic'])

    with tab2:
        afficher_google_search()


if __name__ == "__main__":
    main()
