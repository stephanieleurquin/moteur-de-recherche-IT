# ==========================================================
# ASSISTANT IT PRO - MOTEUR DE RECHERCHE MONETISABLE
# BLOC 1/4
# ==========================================================

import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime


# ==========================================================
# CONFIGURATION STREAMLIT
# ==========================================================

st.set_page_config(
    page_title="Assistant IT Pro",
    page_icon="🤖",
    layout="wide"
)


DB = "assistant_it_pro.db"


# ==========================================================
# CONNEXION SUPABASE
# ==========================================================

try:

    from supabase import create_client


    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )


    SUPABASE_OK = True


except Exception as e:

    supabase = None
    SUPABASE_OK = False



# ==========================================================
# STYLE
# ==========================================================

st.markdown(
"""
<style>

.main-title {

font-size:45px;
font-weight:800;
text-align:center;

}


.box {

padding:20px;
border-radius:15px;
background:#111827;
color:white;
margin:10px;

}


</style>

""",
unsafe_allow_html=True
)



# ==========================================================
# BASE LOCALE
# ==========================================================


def db():

    return sqlite3.connect(DB)



def init_db():


    con = db()

    cur = con.cursor()



    cur.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs

    (

    email TEXT PRIMARY KEY,

    recherches INTEGER DEFAULT 0,

    premium INTEGER DEFAULT 0

    )

    """)



    cur.execute("""
    CREATE TABLE IF NOT EXISTS historique

    (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    email TEXT,

    question TEXT,

    date TEXT

    )

    """)



    con.commit()

    con.close()



# ==========================================================
# SESSION
# ==========================================================


def init_session():


    if "user" not in st.session_state:

        st.session_state.user = None



    if "recherches" not in st.session_state:

        st.session_state.recherches = 0



# ==========================================================
# AUTHENTIFICATION
# ==========================================================


def authentification():

    st.sidebar.markdown(
        "## 👤 Compte"
    )


    init_session()



    # utilisateur connecté

    if st.session_state.user:


        email = st.session_state.user.email


        st.sidebar.success(
            f"Connecté : {email}"
        )



        if st.sidebar.button(
            "🚪 Déconnexion"
        ):


            try:

                supabase.auth.sign_out()

            except:

                pass



            st.session_state.user = None

            st.session_state.recherches = 0

            st.rerun()



        return




    if not SUPABASE_OK:


        st.sidebar.error(
            "Supabase non connecté"
        )

        return




    choix = st.sidebar.radio(

        "Action",

        [
            "Connexion",
            "Créer un compte"
        ]

    )



    email = st.sidebar.text_input(
        "Email"
    )



    password = st.sidebar.text_input(

        "Mot de passe",

        type="password"

    )




    if choix == "Créer un compte":



        if st.sidebar.button(
            "Créer mon compte"
        ):


            try:


                supabase.auth.sign_up({

                    "email":email,

                    "password":password

                })



                st.sidebar.success(

                    "Compte créé ✅ Vérifiez votre email"

                )


            except Exception as e:


                st.sidebar.error(
                    str(e)
                )





    if choix == "Connexion":



        if st.sidebar.button(
            "Se connecter"
        ):



            try:


                resultat = supabase.auth.sign_in_with_password({

                    "email":email,

                    "password":password

                })



                st.session_state.user = resultat.user


                st.sidebar.success(
                    "Connexion réussie ✅"
                )


                st.rerun()



            except Exception as e:


                st.sidebar.error(
                    str(e)
                )



# ==========================================================
# DEMARRAGE
# ==========================================================


init_db()

authentification()


st.markdown(
"""
<div class="main-title">
🤖 Assistant Dépannage IT Pro
</div>
""",

unsafe_allow_html=True
)
# ==========================================================
# BLOC 2/4
# BASE DE CONNAISSANCES + MOTEUR DE RECHERCHE IT
# ==========================================================


def charger_base_it():

    return [

        {
            "titre": "PC très lent",

            "categorie": "Performance",

            "symptomes":
            "ordinateur lent rame bloque programmes longs",

            "diagnostic":
            "Le problème peut venir du disque, de la mémoire RAM ou de trop nombreux logiciels au démarrage.",

            "solution":
            """
✅ Vérifier le gestionnaire des tâches
✅ Contrôler l'utilisation CPU et RAM
✅ Désactiver les programmes inutiles au démarrage
✅ Nettoyer le disque
✅ Vérifier l'état du disque dur
            """,

            "tags":
            "lent rame vitesse performance ordinateur pc"
        },


        {
            "titre": "Impossible de se connecter au Wi-Fi",

            "categorie": "Réseau",

            "symptomes":
            "wifi internet connexion réseau box",

            "diagnostic":
            "Le problème peut venir de la box, du pilote Wi-Fi ou de la carte réseau.",

            "solution":
            """
✅ Redémarrer la box internet
✅ Redémarrer l'ordinateur
✅ Vérifier le mode avion
✅ Réinstaller le pilote Wi-Fi
✅ Tester avec un autre appareil
            """,

            "tags":
            "wifi internet réseau connexion box"
        },


        {
            "titre": "Écran noir",

            "categorie": "Matériel",

            "symptomes":
            "écran noir aucun affichage pc démarre",

            "diagnostic":
            "Possible problème de câble vidéo, écran, RAM ou carte graphique.",

            "solution":
            """
✅ Vérifier câble HDMI ou DisplayPort
✅ Tester un autre écran
✅ Retirer et remettre la RAM
✅ Vérifier la carte graphique
            """,

            "tags":
            "écran noir image affichage hdmi gpu"
        },


        {
            "titre": "Windows ne démarre plus",

            "categorie": "Système",

            "symptomes":
            "windows démarrage erreur écran noir redémarrage",

            "diagnostic":
            "Fichiers système corrompus, disque défectueux ou problème de mise à jour.",

            "solution":
            """
✅ Démarrer en mode sans échec
✅ Utiliser la réparation Windows
✅ Vérifier le disque
✅ Restaurer le système
            """,

            "tags":
            "windows démarrage erreur réparation système"
        },


        {
            "titre": "Virus ou malware détecté",

            "categorie": "Sécurité",

            "symptomes":
            "virus malware publicité piratage ordinateur infecté",

            "diagnostic":
            "Présence possible d'un logiciel malveillant.",

            "solution":
            """
✅ Faire une analyse antivirus complète
✅ Supprimer les logiciels suspects
✅ Changer les mots de passe importants
✅ Activer la double authentification
            """,

            "tags":
            "virus malware sécurité antivirus piratage"
        },


        {
            "titre": "Imprimante impossible à utiliser",

            "categorie": "Périphérique",

            "symptomes":
            "imprimante hors ligne impression impossible",

            "diagnostic":
            "Pilote, câble, réseau ou file d'impression bloquée.",

            "solution":
            """
✅ Vérifier l'alimentation
✅ Vérifier le papier
✅ Redémarrer l'imprimante
✅ Réinstaller le pilote
            """,

            "tags":
            "imprimante impression pilote papier usb"
        }

    ]



# ==========================================================
# CLASSE MOTEUR IA
# ==========================================================


class RechercheIT:


    def __init__(self):

        self.base = charger_base_it()



    def normaliser(self, texte):

        texte = str(texte).lower()


        corrections = {

            "ordi": "ordinateur",

            "pc": "ordinateur",

            "rame": "lent",

            "wiffi": "wifi",

            "wify": "wifi",

            "bloqué": "bloque"

        }


        for ancien, nouveau in corrections.items():

            texte = texte.replace(
                ancien,
                nouveau
            )


        return texte




    def chercher(self, question):


        question = self.normaliser(question)


        mots = re.findall(
            r"\w+",
            question
        )


        resultats = []



        for panne in self.base:


            score = 0



            texte = self.normaliser(

                panne["titre"]
                + " "
                + panne["symptomes"]
                + " "
                + panne["tags"]

            )



            for mot in mots:


                if len(mot) < 2:

                    continue



                if mot in texte:

                    score += 10



            if score > 0:


                resultats.append(

                    (
                        panne,
                        score
                    )

                )



        resultats.sort(

            key=lambda x:x[1],

            reverse=True

        )


        return resultats

# ==========================================================
# BLOC 3/4
# PROFIL UTILISATEUR + COMPTEUR GRATUIT + PREMIUM
# ==========================================================


RECHERCHES_GRATUITES = 10



# ==========================================================
# CREER / CHARGER UTILISATEUR
# ==========================================================


def creer_utilisateur(email):

    con = db()

    cur = con.cursor()


    cur.execute(
        """
        INSERT OR IGNORE INTO utilisateurs(email)
        VALUES (?)
        """,
        (email,)
    )


    con.commit()

    con.close()





def obtenir_utilisateur(email):


    con = db()

    cur = con.cursor()



    cur.execute(

        """
        SELECT email,recherches,premium
        FROM utilisateurs
        WHERE email=?
        """,

        (email,)

    )



    resultat = cur.fetchone()



    con.close()



    return resultat





# ==========================================================
# COMPTEUR DE RECHERCHES
# ==========================================================


def peut_rechercher(email):


    utilisateur = obtenir_utilisateur(email)



    if utilisateur is None:

        creer_utilisateur(email)

        return True



    recherches = utilisateur[1]

    premium = utilisateur[2]



    # Premium = illimité

    if premium == 1:

        return True



    # Version gratuite

    return recherches < RECHERCHES_GRATUITES





def ajouter_recherche(email, question):


    con = db()

    cur = con.cursor()



    cur.execute(

        """
        INSERT INTO historique
        (
        email,
        question,
        date
        )

        VALUES (?,?,?)

        """,

        (
            email,
            question,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
        )

    )



    cur.execute(

        """
        UPDATE utilisateurs

        SET recherches = recherches + 1

        WHERE email=?

        """,

        (email,)

    )



    con.commit()

    con.close()





# ==========================================================
# PROFIL UTILISATEUR
# ==========================================================


def afficher_profil():


    if not st.session_state.user:

        return



    email = st.session_state.user.email



    creer_utilisateur(email)



    infos = obtenir_utilisateur(email)



    if infos:


        st.sidebar.markdown("---")

        st.sidebar.markdown(
            "## 📊 Profil"
        )



        st.sidebar.write(
            f"👤 {infos[0]}"
        )


        if infos[2] == 1:


            st.sidebar.success(
                "⭐ Compte Premium"
            )


        else:


            restant = RECHERCHES_GRATUITES - infos[1]


            st.sidebar.info(

                f"Recherches restantes : {restant}"

            )





# ==========================================================
# BOUTON PREMIUM
# ==========================================================


def afficher_premium():


    st.sidebar.markdown("---")

    st.sidebar.markdown(
        "## ⭐ Premium"
    )


    st.sidebar.write(

        """
        Débloquez :

        ✅ recherches illimitées

        ✅ historique complet

        ✅ outils IT avancés

        ✅ support prioritaire

        """

    )


    if st.sidebar.button(
        "🚀 Passer Premium"
    ):


        st.sidebar.success(

            "Paiement bientôt disponible"

        )

# ==========================================================
# BLOC 4/4
# INTERFACE FINALE
# ==========================================================


def afficher_resultats(resultats):


    if not resultats:


        st.warning(
            "❌ Aucun diagnostic trouvé. Essayez avec plus de détails."
        )

        return



    st.success(

        f"🔎 {len(resultats)} solution(s) trouvée(s)"

    )



    for panne, score in resultats:


        with st.expander(

            f"🛠️ {panne['titre']}  | Pertinence : {score}"

        ):



            st.markdown(

                f"""
### 📂 Catégorie
{panne['categorie']}


### 🔎 Diagnostic

{panne['diagnostic']}


### 🔧 Procédure

{panne['solution']}

"""

            )





# ==========================================================
# PROGRAMME PRINCIPAL
# ==========================================================


def main():


    moteur = RechercheIT()



    afficher_profil()

    afficher_premium()



    st.markdown(

    """
    <div class="box">

    Bienvenue dans votre assistant de dépannage informatique.

    Décrivez votre problème comme à un technicien.

    Exemple :
    "Mon PC est lent depuis hier"
    
    </div>
    """,

    unsafe_allow_html=True

    )



    question = st.text_area(

        "🔍 Quel est votre problème informatique ?",

        height=120,

        placeholder=
        "Exemple : mon wifi ne fonctionne plus..."

    )



    bouton = st.button(

        "🚀 Lancer le diagnostic",

        type="primary"

    )



    if bouton and question:



        # utilisateur obligatoire pour compteur

        if not st.session_state.user:


            st.warning(

                "Créez un compte gratuit pour utiliser le moteur."

            )

            return



        email = st.session_state.user.email



        if not peut_rechercher(email):


            st.error(

                """
                Limite gratuite atteinte.

                Passez Premium pour continuer.
                """

            )

            return




        ajouter_recherche(

            email,

            question

        )



        resultats = moteur.chercher(

            question

        )



        afficher_resultats(

            resultats

        )





# ==========================================================
# LANCEMENT
# ==========================================================


if __name__ == "__main__":

    main()
        
        
