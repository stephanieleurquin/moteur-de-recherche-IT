import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import re
from datetime import datetime

from supabase import create_client

DB = "assistant_it_ia.db"
# ==========================
# CONNEXION SUPABASE
# ==========================

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ==========================
# CONFIGURATION
# ==========================
st.set_page_config(page_title="Assistant IT Pro", page_icon="🤖", layout="wide")

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
# BASE DE DONNÉES
# ==========================
def connexion():
    return sqlite3.connect(DB)

def init_db():
    con = connexion()
    cur = con.cursor()
    
    # Supprime et recrée la table
    cur.execute("DROP TABLE IF EXISTS pannes")
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
    
    donnees = [
        # 1. PÉRIPHÉRIQUES
        ("Souris qui ne fonctionne pas",
         "la souris ne répond plus, le curseur ne bouge pas",
         "Problème de souris : piles usées, récepteur USB mal branché, ou pilote corrompu.",
         "1️⃣ Changer les piles\n2️⃣ Rebrancher le récepteur USB\n3️⃣ Tester sur un autre port\n4️⃣ Réinstaller le pilote",
         "La souris s'allume-t-elle ? Le récepteur est-il branché ?",
         "Périphériques", 1, "souris,curseur,usb,souris sans fil"),
        
        ("Clavier qui ne répond pas",
         "les touches du clavier ne fonctionnent plus, impossible de taper",
         "Problème de clavier : câble débranché, pilote défectueux ou touche bloquée.",
         "1️⃣ Vérifier le câble USB\n2️⃣ Tester un autre port\n3️⃣ Redémarrer l'ordinateur\n4️⃣ Nettoyer le clavier",
         "Le clavier s'allume-t-il ? Avez-vous renversé un liquide ?",
         "Périphériques", 1, "clavier,touches,usb,écriture"),
        
        ("Imprimante ne fonctionne pas",
         "l'imprimante n'imprime pas, elle est hors ligne ou affiche une erreur",
         "Problème d'impression : pilote obsolète, papier coincé, connexion USB défectueuse, ou cartouche vide.",
         "1️⃣ Vérifier le papier et les cartouches\n2️⃣ Redémarrer l'imprimante\n3️⃣ Réinstaller le pilote\n4️⃣ Vérifier la connexion",
         "Le voyant de l'imprimante est-il allumé ? Y a-t-il du papier ?",
         "Périphériques", 2, "imprimante,impression,papier,cartouche"),
        
        ("Webcam ne fonctionne pas",
         "la webcam ne s'allume pas, l'image est noire ou pixelisée",
         "Problème de webcam : pilote manquant, autorisation non donnée, ou matériel défectueux.",
         "1️⃣ Vérifier les autorisations de l'application\n2️⃣ Réinstaller le pilote\n3️⃣ Tester avec une autre application\n4️⃣ Redémarrer",
         "La webcam est-elle branchée ? Avez-vous autorisé l'accès ?",
         "Périphériques", 2, "webcam,caméra,video,image"),
        
        ("Microphone ne fonctionne pas",
         "le micro ne capte pas le son, personne ne m'entend",
         "Problème de microphone : pilote corrompu, paramètres audio incorrects, ou matériel défectueux.",
         "1️⃣ Vérifier les paramètres audio\n2️⃣ Tester avec un autre logiciel\n3️⃣ Réinstaller le pilote\n4️⃣ Vérifier le branchement",
         "Le micro est-il branché ? Est-il activé dans les paramètres ?",
         "Périphériques", 2, "micro,son,audio,parler"),
        
        # 2. MATÉRIEL
        ("Ordinateur qui s'éteint tout seul",
         "le PC s'éteint soudainement, il redémarre sans raison",
         "Problème d'alimentation ou surchauffe : ventilateur bloqué, pâte thermique sèche, ou alimentation défectueuse.",
         "1️⃣ Vérifier la température avec un logiciel\n2️⃣ Nettoyer les ventilateurs\n3️⃣ Tester une autre prise\n4️⃣ Vérifier l'alimentation",
         "Le PC chauffe-t-il ? Les ventilateurs tournent-ils ?",
         "Matériel", 3, "extinction,surchauffe,alimentation,ventilateur"),
        
        ("Écran noir",
         "L'ordinateur démarre mais l'écran reste noir, aucun signal",
         "Problème d'affichage : câble défectueux, écran endommagé, ou carte graphique défaillante.",
         "1️⃣ Vérifier le câble HDMI ou DisplayPort\n2️⃣ Tester un autre écran\n3️⃣ Tester la RAM en la retirant et remettant\n4️⃣ Vérifier la carte graphique",
         "Le PC s'allume-t-il normalement ? Y a-t-il des bips ?",
         "Matériel", 3, "ecran noir,image,affichage,hdmi"),
        
        ("Ordinateur qui redémarre en boucle",
         "le PC redémarre sans arrêt, impossible d'accéder à Windows",
         "Problème de démarrage : disque dur défectueux, mémoire RAM défaillante, ou système corrompu.",
         "1️⃣ Démarrer en mode sans échec\n2️⃣ Vérifier les disques durs\n3️⃣ Tester la RAM\n4️⃣ Réparer le système",
         "Entendez-vous des bips au démarrage ?",
         "Matériel", 3, "redémarrage,boucle,démarrage,ram"),
        
        ("Ventilateur qui fait du bruit",
         "le ventilateur de l'ordinateur fait un bruit fort et continu",
         "Problème de ventilateur : accumulation de poussière, roulement usé, ou ventilation bloquée.",
         "1️⃣ Nettoyer le ventilateur avec de l'air comprimé\n2️⃣ Vérifier les obstacles\n3️⃣ Remplacer le ventilateur si nécessaire",
         "Depuis quand le bruit est-il apparu ?",
         "Matériel", 2, "ventilateur,bruit,nettoyage,poussière"),
        
        # 3. PERFORMANCE
        ("PC très lent",
         "L'ordinateur est très lent, il rame, les programmes mettent du temps à s'ouvrir",
         "Problème de performance : disque dur plein ou lent, trop de programmes au démarrage, ou RAM insuffisante.",
         "1️⃣ Ouvrir le Gestionnaire des Tâches\n2️⃣ Voir l'utilisation du CPU et de la RAM\n3️⃣ Désactiver les programmes inutiles au démarrage\n4️⃣ Nettoyer le disque\n5️⃣ Ajouter de la RAM",
         "Depuis quand l'ordinateur est-il lent ? Combien de RAM avez-vous ?",
         "Performance", 2, "lent,rame,performance,rapide"),
        
        ("Disque dur plein",
         "le disque dur est plein, impossible d'installer ou de sauvegarder des fichiers",
         "Problème de stockage : disque saturé, fichiers temporaires accumulés, ou téléchargements excessifs.",
         "1️⃣ Supprimer les fichiers inutiles\n2️⃣ Vider la corbeille\n3️⃣ Désinstaller les programmes inutilisés\n4️⃣ Défragmenter le disque\n5️⃣ Ajouter un disque externe",
         "Quelle est la capacité de votre disque ? Que stockez-vous ?",
         "Performance", 2, "disque,stockage,mémoire,plein"),
        
        ("Ordinateur qui freeze",
         "l'ordinateur se bloque complètement, plus rien ne répond",
         "Problème de freeze : RAM insuffisante, disque dur lent, ou logiciel en conflit.",
         "1️⃣ Forcer l'arrêt avec le bouton power\n2️⃣ Redémarrer en mode sans échec\n3️⃣ Vérifier les logiciels en conflit\n4️⃣ Augmenter la RAM",
         "Que faisiez-vous avant le blocage ?",
         "Performance", 3, "freeze,bloque,coincé,ram"),
        
        ("Écran qui clignote",
         "l'écran clignote, des lignes apparaissent et disparaissent",
         "Problème d'affichage : pilote graphique défectueux, câble endommagé, ou écran défaillant.",
         "1️⃣ Mettre à jour le pilote graphique\n2️⃣ Vérifier le câble\n3️⃣ Tester un autre écran\n4️⃣ Modifier la fréquence de rafraîchissement",
         "Le clignotement est-il constant ?",
         "Performance", 2, "clignote,écran,lignes,affichage"),
        
        # 4. RÉSEAU
        ("Wi-Fi ne fonctionne pas",
         "le wifi ne fonctionne plus, internet est coupé",
         "Problème réseau : box internet en panne, pilote Wi-Fi corrompu, ou mot de passe incorrect.",
         "1️⃣ Redémarrer la box\n2️⃣ Redémarrer le PC\n3️⃣ Réinstaller le pilote Wi-Fi\n4️⃣ Vérifier le mot de passe",
         "Les autres appareils ont-ils internet ?",
         "Réseau", 2, "wifi,internet,connexion,box"),
        
        ("Connexion Ethernet ne fonctionne pas",
         "le câble réseau est branché mais pas d'internet",
         "Problème Ethernet : câble défectueux, pilote réseau corrompu, ou paramètres IP incorrects.",
         "1️⃣ Vérifier le câble Ethernet\n2️⃣ Redémarrer le routeur\n3️⃣ Réinstaller le pilote réseau\n4️⃣ Vérifier les paramètres IP",
         "Le voyant du câble réseau est-il allumé ?",
         "Réseau", 2, "ethernet,cable,réseau,internet"),
        
        ("Internet très lent",
         "la connexion internet est très lente, les pages mettent du temps à charger",
         "Problème de bande passante : trop d'appareils connectés, box défectueuse, ou fournisseur d'accès limité.",
         "1️⃣ Redémarrer la box\n2️⃣ Vérifier le nombre d'appareils connectés\n3️⃣ Tester avec un câble\n4️⃣ Contacter le FAI",
         "Combien d'appareils sont connectés ?",
         "Réseau", 2, "lent,internet,connexion,debit"),
        
        ("Impossible de se connecter au VPN",
         "je n'arrive pas à me connecter au VPN du travail",
         "Problème VPN : identifiants incorrects, serveur VPN indisponible, ou pare-feu bloquant.",
         "1️⃣ Vérifier les identifiants\n2️⃣ Redémarrer le client VPN\n3️⃣ Vérifier le pare-feu\n4️⃣ Contacter le support IT",
         "Avez-vous changé votre mot de passe récemment ?",
         "Réseau", 3, "vpn,connexion,sécurité,travail"),
        
        # 5. LOGICIEL
        ("Windows ne démarre pas",
         "impossible de démarrer Windows, écran noir avec message d'erreur",
         "Problème de démarrage : fichier système corrompu, mise à jour échouée, ou disque dur défectueux.",
         "1️⃣ Démarrer en mode sans échec\n2️⃣ Utiliser la restauration du système\n3️⃣ Réparer avec une clé USB bootable\n4️⃣ Réinstaller Windows",
         "Quel message d'erreur s'affiche ?",
         "Logiciel", 4, "windows,démarrage,systeme,erreur"),
        
        ("Logiciel qui ne s'installe pas",
         "je n'arrive pas à installer un logiciel, message d'erreur",
         "Problème d'installation : espace insuffisant, antivirus bloquant, ou fichier corrompu.",
         "1️⃣ Vérifier l'espace disque\n2️⃣ Désactiver l'antivirus temporairement\n3️⃣ Télécharger à nouveau le fichier\n4️⃣ Lancer en tant qu'administrateur",
         "Quel message d'erreur s'affiche ?",
         "Logiciel", 3, "installation,logiciel,erreur,espace"),
        
        ("Oubli du mot de passe Windows",
         "je ne peux plus me connecter à mon ordinateur, mot de passe oublié",
         "Problème de connexion : mot de passe oublié ou compte bloqué après plusieurs tentatives.",
         "1️⃣ Utiliser le mode sans échec\n2️⃣ Réinitialiser le mot de passe avec le compte administrateur\n3️⃣ Utiliser une clé de réinitialisation\n4️⃣ Contacter l'administrateur",
         "Avez-vous un compte administrateur ?",
         "Sécurité", 3, "mot de passe,connexion,compte,oublie"),
        
        ("Virus ou malware détecté",
         "l'antivirus a détecté un virus, l'ordinateur est infecté",
         "Problème de sécurité : virus, malware, ou logiciel espion sur l'ordinateur.",
         "1️⃣ Lancer une analyse antivirus complète\n2️⃣ Utiliser un outil de suppression de malware\n3️⃣ Redémarrer en mode sans échec\n4️⃣ Réinstaller le système si nécessaire",
         "Depuis quand avez-vous ce problème ?",
         "Logiciel", 4, "virus,malware,sécurité,antivirus"),
        
        ("Impossible d'ouvrir un fichier",
         "je n'arrive pas à ouvrir un fichier, extension non reconnue",
         "Problème d'extension : logiciel manquant, fichier corrompu, ou erreur de compatibilité.",
         "1️⃣ Vérifier l'extension du fichier\n2️⃣ Installer le logiciel approprié\n3️⃣ Tester avec un autre programme\n4️⃣ Réparer le fichier",
         "Quelle est l'extension du fichier ?",
         "Logiciel", 1, "fichier,extension,ouvrir,compatibilité"),
        
        # 6. SÉCURITÉ
        ("Compte utilisateur bloqué",
         "mon compte est bloqué, impossible de me connecter",
         "Problème de compte : trop de tentatives échouées, mot de passe expiré, ou compte désactivé.",
         "1️⃣ Attendre 30 minutes\n2️⃣ Réinitialiser le mot de passe\n3️⃣ Contacter l'administrateur\n4️⃣ Vérifier les politiques de sécurité",
         "Avez-vous tenté de vous connecter plusieurs fois ?",
         "Sécurité", 3, "compte,bloqué,connexion,utilisateur"),
        
        ("Pare-feu bloquant",
         "le pare-feu bloque tout, impossible d'accéder à internet",
         "Problème de pare-feu : configuration incorrecte, règle bloquante, ou logiciel tiers.",
         "1️⃣ Vérifier les règles du pare-feu\n2️⃣ Désactiver temporairement\n3️⃣ Ajouter une exception\n4️⃣ Réinitialiser le pare-feu",
         "Quand avez-vous modifié le pare-feu ?",
         "Sécurité", 2, "parefeu,bloqué,sécurité,regle"),
        
        ("Email compromis",
         "j'ai reçu un email suspect, mon compte a peut-être été piraté",
         "Problème de sécurité : compte compromis, phishing, ou mot de passe faible.",
         "1️⃣ Changer immédiatement le mot de passe\n2️⃣ Activer la double authentification\n3️⃣ Vérifier l'historique de connexion\n4️⃣ Contacter le support",
         "Avez-vous cliqué sur un lien suspect ?",
         "Sécurité", 4, "email,compromis,piratage,sécurité"),
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
            "rame": "lent", "ram": "lent", "bloque": "freeze",
            "wiffi": "wifi", "wify": "wifi", "ordi": "ordinateur", "pc": "ordinateur"
        }
        for ancien, nouveau in corrections.items():
            texte = texte.replace(ancien, nouveau)
        return texte

    def rechercher_ia(self, question, top_k=15):
        self.charger_base()
        question = self.normaliser(question)
        mots = re.findall(r"\w+", question)

        resultats = []
        for _, panne in self.df.iterrows():
            score = 0
            titre = self.normaliser(panne["titre"])
            tags = self.normaliser(panne["tags"])
            description = self.normaliser(panne["description"])
            diagnostic = self.normaliser(panne["diagnostic"])

            for mot in mots:
                if len(mot) < 2:
                    continue
                if mot in titre:
                    score += 10
                if mot in tags:
                    score += 8
                if mot in description:
                    score += 5
                if mot in diagnostic:
                    score += 5

            if score > 0:
                resultats.append((dict(panne), score))

        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:top_k]

# ==========================
# FONCTION POUR AFFICHER GOOGLE SEARCH
# ==========================
def afficher_google_search():
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
# AUTHENTIFICATION UTILISATEUR
# ==========================

def afficher_auth():

    st.sidebar.markdown("## 👤 Compte utilisateur")

    if "user" not in st.session_state:
        st.session_state.user = None

    choix = st.sidebar.radio(
        "Choisir une action",
        ["Connexion", "Créer un compte"]
    )

    email = st.sidebar.text_input("Email")

    password = st.sidebar.text_input(
        "Mot de passe",
        type="password"
    )


    if choix == "Créer un compte":

        if st.sidebar.button("Créer mon compte"):

            try:
                supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })

                st.sidebar.success(
                    "Compte créé ! Vérifiez votre email."
                )

            except Exception as e:
                st.sidebar.error(str(e))


    if choix == "Connexion":

        if st.sidebar.button("Se connecter"):

            try:
                resultat = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                st.session_state.user = resultat.user

                st.sidebar.success(
                    "Connexion réussie ✅"
                )

            except Exception as e:
                st.sidebar.error(
                    "Erreur de connexion : " + str(e)
                )

# ==========================
# INTERFACE PRINCIPALE
# ==========================
def main():
    init_db()
    
   

    afficher_auth()
    
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
        - Décrivez précisément le problème
        - Mentionnez les symptômes
        - Précisez le contexte
        """)

        st.markdown("---")
        if st.button("🔄 Réinitialiser la base", type="secondary"):
            init_db()
            st.cache_data.clear()
            st.success(f"✅ Base réinitialisée avec {total} pannes")
            st.rerun()

        with st.expander("⚙️ Administration (ajouter une panne)"):
            with st.form("ajout_panne"):
                titre = st.text_input("Titre")
                description = st.text_area("Description")
                diagnostic = st.text_area("Diagnostic")
                procedure = st.text_area("Procédure")
                questions = st.text_input("Questions à poser")
                categorie = st.selectbox("Catégorie", ["Matériel", "Logiciel", "Réseau", "Performance", "Périphériques", "Sécurité", "Autre"])
                niveau = st.slider("Niveau de difficulté", 1, 5, 2)
                tags = st.text_input("Tags (séparés par des virgules)")
                soumettre = st.form_submit_button("Ajouter")
                if soumettre:
                    if titre and description:
                        con = connexion()
                        cur = con.cursor()
                        cur.execute("""
                        INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (titre, description, diagnostic, procedure, questions, categorie, niveau, tags))
                        con.commit()
                        con.close()
                        st.success("✅ Panne ajoutée avec succès !")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Le titre et la description sont obligatoires.")

    st.markdown('<p class="main-title">🤖 Assistant Dépannage IT</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔍 Recherche IA", "🌐 Recherche Google"])

    with tab1:
        question = st.text_area(
            "Décrivez votre problème :",
            placeholder="Exemple : mon PC est très lent...",
            height=100
        )
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            rechercher = st.button("🔍 Analyser", use_container_width=True, type="primary")

        if rechercher and question:
            resultats = st.session_state.recherche_pro.rechercher_ia(question, top_k=15)
            if not resultats:
                st.error("❌ Aucun diagnostic trouvé. Essayez de reformuler.")
            else:
                st.success(f"🔎 {len(resultats)} diagnostic(s) trouvé(s)")
                for i, (r, s) in enumerate(resultats, 1):
                    with st.expander(f"{i}. {r['titre']} (Pertinence : {s} points)", expanded=(i==1)):
                        st.markdown(f"**Catégorie :** {r['categorie']}  |  **Niveau :** {'⭐'*r['niveau']}")
                        st.markdown(f"**Diagnostic :**\n{r['diagnostic']}")
                        st.markdown(f"**Procédure :**\n{r['procedure']}")
                        if r['questions']:
                            st.info(f"**Questions à poser :** {r['questions']}")
                        st.caption(f"Tags : {r['tags']}")

    with tab2:
        afficher_google_search()
        st.sidebar.markdown("---")
with st.sidebar.expander("📜 Licence"):
    st.markdown("""
    **Assistant IT Pro**  
    © 2026 Stéphanie Vanschoor 
    Sous licence MIT - Utilisation libre  
    [Voir la licence complète](https://github.com/stephanieleurquin/moteur-de-recherche-IT/blob/main/LICENSE)
    """)
            # ===== AJOUT DU DISCLAIMER =====
    st.warning("""
        **⚠️ Avertissement**
        Les diagnostics fournis par cet outil sont fournis à titre indicatif.
        Ils ne remplacent pas l'avis d'un professionnel. L'utilisateur est seul responsable de l'application des procédures.
        """)

if __name__ == "__main__":
    main()
