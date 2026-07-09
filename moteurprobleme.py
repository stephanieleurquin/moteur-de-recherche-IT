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
    page_title="Assistant IT IA Pro + Google Search",
    page_icon="🤖",
    layout="wide"
)

# ==========================
# CODE DE VALIDATION ADSENSE
# ==========================
st.markdown("""
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1095625009769978"
     crossorigin="anonymous"></script>
""", unsafe_allow_html=True)

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
    .monetization-badge {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        padding: 0.3rem 1rem;
        border-radius: 20px;
        display: inline-block;
        font-weight: bold;
        color: #333;
        font-size: 0.8rem;
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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0;">🔍 Recherche Google personnalisée</h3>
            <span class="monetization-badge">💰 Monétisé avec AdSense</span>
        </div>
        <p style="color: #666; font-size: 0.9rem; margin-bottom: 1rem;">
            Recherchez sur tout le web avec la puissance de Google, directement depuis votre assistant IT.
        </p>
    </div>
    """, unsafe_allow_html=True)

    google_code = """
    <script async src="https://cse.google.com/cse.js?cx=70e26eb628d0e4736">
    </script>
    <div class="gcse-search"></div>
    """

    st.components.v1.html(google_code, height=400)

    st.markdown("""
    <div style="background: #f0f4ff; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
        <p style="color: #4285f4; font-size: 0.9rem;">
            💡 <strong>Astuce :</strong> Les résultats de recherche peuvent afficher des annonces Google AdSense.
            Chaque clic sur une annonce vous rapporte de l'argent.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ==========================
# MODELE IA
# ==========================
def connexion():
    return sqlite3.connect(DB)


def init_db():
    con = connexion()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS pannes
    (
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
        print("📦 Insertion des données enrichies avec VARIATIONS...")

        donnees = [
            (
                "PC très lent",
                "L'ordinateur est très lent, il rame, les programmes mettent du temps à s'ouvrir, le PC freeze, tout est lent",
                "Problème de performance : soit le disque dur est plein ou lent, soit il y a trop de programmes au démarrage, soit la RAM est insuffisante.",
                "1️⃣ Ouvrir le Gestionnaire des Tâches (Ctrl+Alt+Suppr)\n2️⃣ Voir l'utilisation du CPU, RAM et disque\n3️⃣ Nettoyer le disque (Propreté du disque)\n4️⃣ Désactiver les programmes au démarrage\n5️⃣ Faire une analyse antivirus\n6️⃣ Envisager un SSD si HDD",
                "Depuis quand l'ordinateur est-il lent ? Le disque est-il plein ?",
                "Performance",
                2,
                "lent,rame,blocage,freeze,performance,disque"
            ),
            (
                "Ordinateur qui rame",
                "mon pc rame, il est bloqué, les applications ne répondent plus, tout est figé",
                "Le PC manque de ressources ou a des processus qui consomment trop de CPU/mémoire.",
                "1️⃣ Ouvrir le Gestionnaire des Tâches\n2️⃣ Identifier les processus gourmands\n3️⃣ Redémarrer l'explorateur Windows\n4️⃣ Nettoyer les fichiers temporaires\n5️⃣ Vérifier les mises à jour Windows",
                "Quels programmes utilisez-vous ? Le problème apparaît-il au démarrage ?",
                "Performance",
                2,
                "rame,blocage,freeze,crash,performance"
            ),
            (
                "Windows qui tourne au ralenti",
                "windows est très lent, le système d'exploitation tourne au ralenti, tout est lent sous windows",
                "Windows peut être ralenti par des mises à jour en cours, un disque fragmenté, des pilotes obsolètes.",
                "1️⃣ Vérifier les mises à jour Windows\n2️⃣ Exécuter 'Défragmenter le disque'\n3️⃣ Mettre à jour les pilotes\n4️⃣ Vérifier l'état du disque\n5️⃣ Désactiver les effets visuels inutiles",
                "Avez-vous récemment installé des mises à jour Windows ?",
                "Performance",
                2,
                "windows,lent,ralentissement,performance"
            ),
            (
                "PC qui bloque en jeu",
                "mon ordinateur bloque quand je joue, les jeux sont saccadés, ça plante",
                "Problème de performances en jeu : carte graphique trop faible, manque de RAM, surchauffe du processeur.",
                "1️⃣ Vérifier les températures (HWMonitor)\n2️⃣ Mettre à jour les pilotes de la carte graphique\n3️⃣ Réduire les paramètres graphiques des jeux\n4️⃣ Vérifier l'alimentation\n5️⃣ Nettoyer les ventilateurs",
                "Quels jeux faites-vous tourner ? Avez-vous des ralentissements aussi en navigation normale ?",
                "Performance",
                3,
                "jeu,blocage,saccade,graphique,performance"
            ),
            (
                "Écran noir",
                "L'ordinateur démarre mais l'écran reste noir, je n'ai aucune image sur le moniteur",
                "Problème d'affichage : câble défectueux, écran endommagé, carte graphique mal branchée.",
                "1️⃣ Vérifier le câble HDMI/DVI/DisplayPort\n2️⃣ Tester un autre écran\n3️⃣ Rester la carte graphique\n4️⃣ Tester la RAM (barrette par barrette)\n5️⃣ Démarrer en mode sans échec",
                "Le PC s'allume-t-il normalement (ventilateurs, LED) ? Voyez-vous le logo au démarrage ?",
                "Matériel",
                3,
                "ecran noir,image,affichage,carte graphique"
            ),
            (
                "Pas d'image à l'écran",
                "je n'ai pas d'image sur l'écran, mon moniteur est noir, je ne vois rien affiché",
                "Causes possibles : moniteur éteint, câble débranché, source d'entrée incorrecte.",
                "1️⃣ Vérifier que le moniteur est allumé\n2️⃣ Vérifier le câble\n3️⃣ Changer la source d'entrée sur le moniteur\n4️⃣ Tester le PC sur un autre écran\n5️⃣ Vérifier le branchement de la carte graphique",
                "Les voyants du PC sont-ils allumés ? Le moniteur s'allume-t-il ?",
                "Matériel",
                3,
                "image,affichage,moniteur,ecran noir"
            ),
            (
                "Wi-Fi ne fonctionne pas",
                "le wifi ne fonctionne plus, je n'ai plus d'internet, la connexion wi-fi est coupée",
                "Problème de connexion réseau : box internet, pilote Wi-Fi, carte réseau.",
                "1️⃣ Redémarrer la box internet\n2️⃣ Redémarrer le PC\n3️⃣ Désactiver/réactiver le Wi-Fi\n4️⃣ Réinstaller le pilote Wi-Fi\n5️⃣ Vérifier le mode avion",
                "Les autres appareils (téléphone, tablette) ont-ils internet ? Le réseau apparaît-il ?",
                "Réseau",
                2,
                "wifi,internet,connexion,réseau"
            ),
            (
                "Plus de connexion Internet",
                "je n'ai plus internet, le réseau est coupé, je ne peux pas me connecter",
                "Problème réseau : soit la box est en panne, soit le câble est débranché, soit les paramètres réseau sont modifiés.",
                "1️⃣ Vérifier les câbles\n2️⃣ Redémarrer la box (2 minutes)\n3️⃣ Redémarrer l'ordinateur\n4️⃣ Diagnostiquer le réseau dans Windows\n5️⃣ Vérifier le pare-feu",
                "Avez-vous touché aux paramètres réseau ? Le câble Ethernet est-il branché ?",
                "Réseau",
                2,
                "internet,connexion,réseau,box"
            ),
            (
                "Souris sans fil ne répond plus",
                "ma souris sans fil ne fonctionne plus, le curseur ne bouge pas",
                "Piles à changer, récepteur USB mal branché, ou souris hors de portée.",
                "1️⃣ Changer les piles\n2️⃣ Débrancher/rebrancher le récepteur USB\n3️⃣ Tester sur un autre port\n4️⃣ Réappairer la souris (Bluetooth)\n5️⃣ Mettre à jour le pilote",
                "La souris s'allume-t-elle ? Le voyant est-il allumé ?",
                "Périphériques",
                1,
                "souris,sans fil,curseur,usb"
            ),
            (
                "Clavier qui ne tape plus",
                "mon clavier ne répond plus, je ne peux pas taper sur les touches",
                "Clavier débranché, port USB défectueux, pilote corrompu.",
                "1️⃣ Vérifier le branchement USB\n2️⃣ Tester un autre port\n3️⃣ Redémarrer l'ordinateur\n4️⃣ Vérifier le verrouillage numérique\n5️⃣ Tester un autre clavier",
                "Le clavier est-il filaire ou sans fil ? Avez-vous renversé un liquide ?",
                "Périphériques",
                1,
                "clavier,touches,usb,type"
            ),
            (
                "Imprimante n'imprime pas",
                "mon imprimante refuse d'imprimer, les documents restent bloqués dans la file d'attente",
                "Problème de pilote, de bourrage papier, d'encre vide ou de connexion.",
                "1️⃣ Vérifier le niveau d'encre\n2️⃣ Vérifier le bourrage papier\n3️⃣ Redémarrer l'imprimante\n4️⃣ Vider la file d'attente\n5️⃣ Réinstaller le pilote",
                "L'imprimante s'allume-t-elle ? Avez-vous changé les cartouches récemment ?",
                "Périphériques",
                2,
                "imprimante,impression,papier,encre"
            ),
            (
                "Écran bleu (BSOD)",
                "mon ordinateur affiche un écran bleu avec un message d'erreur, puis redémarre",
                "Erreur système critique : RAM défectueuse, pilotes, disque corrompu.",
                "1️⃣ Noter le code d'erreur\n2️⃣ Démarrer en mode sans échec\n3️⃣ Vérifier les pilotes récents\n4️⃣ Tester la RAM (MemTest86)\n5️⃣ Vérifier le disque (chkdsk)",
                "Quel code d'erreur s'affiche ? Avez-vous installé un logiciel récemment ?",
                "Système",
                3,
                "bsod,ecran bleu,crash,erreur"
            ),
            (
                "Bruit du disque dur",
                "j'entends des bruits de clic, de grincement ou de frottement venant de l'ordinateur",
                "Signe de défaillance mécanique du disque dur. Risque de perte de données.",
                "1️⃣ ⚠️ Sauvegarder IMMÉDIATEMENT les données\n2️⃣ Utiliser CrystalDiskInfo pour diagnostiquer\n3️⃣ Remplacer le disque rapidement\n4️⃣ Cloner le disque si possible",
                "Depuis combien de temps entendez-vous ces bruits ? Avez-vous des sauvegardes ?",
                "Stockage",
                3,
                "bruit,disque dur,clic,grincement"
            ),
            (
                "Virus et pop-ups",
                "je reçois des publicités intempestives, des pop-ups, des redirections internet",
                "Infection par malwares, adwares ou programmes potentiellement indésirables.",
                "1️⃣ Démarrer en mode sans échec\n2️⃣ Analyser avec Windows Defender\n3️⃣ Utiliser Malwarebytes\n4️⃣ Supprimer les extensions suspectes\n5️⃣ Réinstaller Windows en dernier recours",
                "Avez-vous reçu des emails suspects ? Avez-vous téléchargé des logiciels récemment ?",
                "Sécurité",
                3,
                "virus,malware,pop-up,publicite"
            )
        ]

        cur.executemany("""
        INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, donnees)

        print(f"✅ {len(donnees)} pannes insérées avec variations")

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
            "rament": "lent",
            "ram": "lent",
            "bloque": "freeze",
            "bloqué": "freeze",
            "wiffi": "wifi",
            "wify": "wifi",
            "internet": "réseau",
            "ordi": "ordinateur",
            "pc": "ordinateur",
            "ecran": "écran"
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
            description = self.normaliser(panne["description"])
            diagnostic = self.normaliser(panne["diagnostic"])
            tags = self.normaliser(panne["tags"])

            for mot in mots:
                if len(mot) < 2:
                    continue
                if mot in titre:
                    score += 10
                if mot in tags:
                    score += 8
                if mot in description:
                    score += 4
                if mot in diagnostic:
                    score += 2

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

        st.markdown("---")
        st.markdown("#### 💰 Monétisation")
        st.info("""
        🔥 **Gagnez de l'argent :**
        - Les annonces Google s'affichent dans les résultats
        - Chaque clic vous rapporte de l'argent
        - 1000 recherches/jour = 50-100€/mois
        """)

    st.markdown('<p class="main-title">🤖 Assistant Dépannage IT</p>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍 Recherche IA", "🌐 Recherche Google", "💰 Monétisation"])

    with tab1:
        question = st.text_area(
            "Décrivez votre problème :",
            placeholder="Exemple : mon PC est très lent, il rame dès que j'ouvre plusieurs programmes...",
            height=100,
            key="search_input"
        )

        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            rechercher = st.button("🔍 Analyser le problème", use_container_width=True, type="primary")

        st.markdown("#### 📌 Exemples de problèmes courants")
        exemples = ["PC lent", "Écran noir", "Wi-Fi ne marche pas"]
        cols = st.columns(len(exemples))
        for i, exemple in enumerate(exemples):
            with cols[i]:
                if st.button(f"🔹 {exemple}", key=f"ex_{i}"):
                    st.session_state.search_input = exemple
                    st.rerun()

        if rechercher and question:
            with st.spinner("🔍 Analyse sémantique en cours..."):
                resultats = st.session_state.recherche_pro.rechercher_ia(question, top_k=3)

            if not resultats:
                st.error("❌ Aucun diagnostic trouvé pour : " + question)
                st.markdown("""
                💡 **Suggestions :**
                - Essayez des mots différents (ex: 'lent' au lieu de 'rame')
                - Soyez plus précis dans la description
                - Décrivez les symptômes concrets
                - Essayez la **Recherche Google** dans l'onglet suivant
                """)
            else:
                st.success(f"✅ {len(resultats)} diagnostic(s) trouvé(s)")

                for i, (resultat, score) in enumerate(resultats, 1):
                    with st.expander(f"📌 {i}. {resultat['titre']} (Score: {score:.2f})", expanded=(i == 1)):
                        st.markdown(f"""
                        <div class="confidence-bar">
                            <div class="confidence-fill" style="width: {min(score * 10, 100)}%"></div>
                        </div>
                        <p style="text-align: right; font-size: 0.8rem;">{min(score * 10, 100):.0f}% de correspondance</p>
                        """, unsafe_allow_html=True)

                        st.markdown("**🔍 Diagnostic :**")
                        st.info(resultat['diagnostic'])

                        st.markdown("**🛠️ Procédure de dépannage :**")
                        procedures = resultat['procedure'].split('\n')
                        for proc in procedures:
                            if proc.strip():
                                st.markdown(f"- {proc.strip()}")

                        with st.expander("❓ Questions du technicien"):
                            st.write(resultat['questions'])

                        if resultat.get('categorie'):
                            st.caption(f"📂 Catégorie: {resultat['categorie']} | ⭐ Niveau: {resultat['niveau']}/3")

    with tab2:
        st.markdown("### 🌐 Recherche Google personnalisée")

        google_code = """
        <script async src="https://cse.google.com/cse.js?cx=70e26eb628d0e4736">
        </script>
        <div class="gcse-search"></div>
        """

        st.components.v1.html(google_code, height=500)

        st.markdown("""
        <div style="background: #f0f4ff; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
            <p style="color: #4285f4; font-size: 0.9rem;">
                💡 <strong>Astuce :</strong> Les résultats de recherche peuvent afficher des annonces Google AdSense.
                Chaque clic sur une annonce vous rapporte de l'argent.
            </p>
            <p style="color: #666; font-size: 0.8rem; margin-top: 0.5rem;">
                🔗 <strong>Votre ID de moteur :</strong> 70e26eb628d0e4736
            </p>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown("### 💰 Comment gagner de l'argent avec ton moteur ?")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            ### 📊 1. Google AdSense
            ✅ Associe ton moteur à AdSense
            ✅ Gagne de l'argent sur chaque clic
            ✅ Revenus passifs

            **Revenus estimés :**
            - 1 000 recherches/jour → 50-100€/mois
            - 10 000 recherches/jour → 500-1000€/mois
            """)

            st.markdown("""
            ### 🚀 3. Version Pro
            ✅ Fonctionnalités premium
            ✅ Abonnement mensuel
            ✅ Support personnalisé

            **Tarifs suggérés :**
            - 5€/mois : Recherches illimitées
            - 20€/mois : API + support prioritaire
            """)

        with col2:
            st.markdown("""
            ### 🛒 2. Affiliation
            ✅ Recommande des produits
            ✅ Commission sur les ventes
            ✅ Amazon, CDiscount, etc.

            **Revenus estimés :**
            - Commission : 5-15%
            - 100 ventes/mois → 200-500€
            """)

            st.markdown("""
            ### 💼 4. Services personnalisés
            ✅ Moteur sur mesure pour entreprises
            ✅ Formation
            ✅ Maintenance

            **Prix :**
            - 500-5000€ par projet
            - 50-100€/h de formation
            """)

        st.markdown("---")
        st.markdown("### 🎯 Prochaines étapes")

        st.markdown("""
        1. **Crée un compte Google AdSense** : https://adsense.google.com/
        2. **Associe ton moteur** à ton compte AdSense
        3. **Fais la promotion** de ton moteur de recherche
        4. **Surveille tes revenus** dans le tableau de bord AdSense

        🔥 **Objectif :** 1000 utilisateurs/jour → 100-200€/mois
        """)


if __name__ == "__main__":
    main()
