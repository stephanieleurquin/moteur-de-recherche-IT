import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
from supabase import create_client


# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Assistant IT Pro",
    page_icon="🤖",
    layout="wide"
)


DB = "assistant_it_ia.db"


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

    st.error(
        "Connexion Supabase impossible"
    )

    st.write(e)



# ==================================================
# SESSION UTILISATEUR
# ==================================================

def init_session():

    if "user" not in st.session_state:
        st.session_state.user = None


    if "recherches" not in st.session_state:
        st.session_state.recherches = 0


    if "premium" not in st.session_state:
        st.session_state.premium = False



# ==================================================
# BASE SQLITE
# ==================================================

def connexion_db():

    return sqlite3.connect(DB)



def creer_base():


    con = connexion_db()

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

        tags TEXT

    )
    """)


    con.commit()

    con.close()



# ==================================================
# AJOUT DES DONNEES DE BASE
# ==================================================

def remplir_base():


    con = connexion_db()

    cur = con.cursor()


    cur.execute(
        "SELECT COUNT(*) FROM pannes"
    )

    total = cur.fetchone()[0]


    if total == 0:


        donnees = [


        (
        "PC très lent",
        "ordinateur lent rame",
        "Manque de ressources, disque lent ou programmes inutiles.",
        "1 Vérifier le gestionnaire des tâches\n2 Nettoyer le disque\n3 Désactiver les programmes inutiles",
        "Depuis quand le PC est lent ?",
        "Performance",
        2,
        "lent,rame,ordinateur,performance"
        ),



        (
        "WiFi impossible",
        "wifi internet connexion impossible",
        "Problème réseau, box ou pilote wifi.",
        "1 Redémarrer la box\n2 Vérifier le wifi\n3 Réinstaller le pilote",
        "Les autres appareils ont-ils internet ?",
        "Réseau",
        2,
        "wifi,internet,réseau,connexion"
        ),



        (
        "Windows ne démarre pas",
        "ordinateur écran noir démarrage impossible",
        "Fichier système endommagé ou problème disque.",
        "1 Mode sans échec\n2 Réparation Windows\n3 Vérifier le disque",
        "Quel message apparaît ?",
        "Logiciel",
        4,
        "windows,démarrage,erreur"
        )

        ]


        cur.executemany(
        """
        INSERT INTO pannes
        (
        titre,
        description,
        diagnostic,
        procedure,
        questions,
        categorie,
        niveau,
        tags
        )
        VALUES (?,?,?,?,?,?,?,?)
        """,
        donnees
        )


    con.commit()
    # ==================================================
# MOTEUR DE RECHERCHE IT
# ==================================================

class RechercheIT:


    def __init__(self):

        self.df = None



    def charger(self):

        if self.df is None:

            con = connexion_db()

            self.df = pd.read_sql_query(
                "SELECT * FROM pannes",
                con
            )

            con.close()



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



    def rechercher(self, question):


        self.charger()


        question = self.normaliser(question)


        mots = re.findall(
            r"\w+",
            question
        )


        resultats = []


        for _, panne in self.df.iterrows():


            score = 0


            champs = [

                panne["titre"],
                panne["description"],
                panne["diagnostic"],
                panne["tags"]

            ]


            texte = self.normaliser(
                " ".join(champs)
            )


            for mot in mots:


                if len(mot) < 2:
                    continue


                if mot in texte:

                    score += 5



                if mot in self.normaliser(
                    panne["titre"]
                ):

                    score += 10



            if score > 0:

                resultats.append(
                    (
                        dict(panne),
                        score
                    )
                )



        resultats.sort(
            key=lambda x:x[1],
            reverse=True
        )


        return resultats[:10]





# ==================================================
# AUTHENTIFICATION SUPABASE
# ==================================================

def authentification():


    st.sidebar.markdown(
        "## 👤 Compte"
    )


    init_session()



    # ------------------------------
    # UTILISATEUR CONNECTE
    # ------------------------------

    if st.session_state.user:


        st.sidebar.success(
            "Connecté : "
            + st.session_state.user.email
        )


        st.sidebar.info(
            "Recherches utilisées : "
            + str(st.session_state.recherches)
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





    # ------------------------------
    # PAS CONNECTE
    # ------------------------------


    if not SUPABASE_OK:

        st.sidebar.error(
            "Supabase non disponible"
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




    # CREATION COMPTE

    if choix == "Créer un compte":



        if st.sidebar.button(
            "Créer mon compte"
        ):


            try:


                supabase.auth.sign_up(

                    {

                    "email": email,

                    "password": password

                    }

                )


                st.sidebar.success(
                    "Compte créé. Vérifiez votre email."
                )



            except Exception as e:


                st.sidebar.error(
                    str(e)
                )





    # CONNEXION

    if choix == "Connexion":



        if st.sidebar.button(
            "Se connecter"
        ):


            try:


                resultat = supabase.auth.sign_in_with_password(

                    {

                    "email": email,

                    "password": password

                    }

                )



                st.session_state.user = resultat.user



                st.sidebar.success(
                    "Connexion réussie"
                )


                st.rerun()



            except Exception as e:


                st.sidebar.error(
                    "Erreur connexion"
                )


                st.sidebar.write(e)

    # ==================================================
# PROFIL / PREMIUM
# ==================================================

LIMITE_GRATUITE = 10


def afficher_profil():


    if st.session_state.user:


        st.sidebar.markdown("---")

        st.sidebar.markdown(
            "### 👤 Profil"
        )


        st.sidebar.write(
            st.session_state.user.email
        )


        if st.session_state.premium:


            st.sidebar.success(
                "⭐ Compte Premium"
            )


        else:


            restant = LIMITE_GRATUITE - st.session_state.recherches


            if restant < 0:

                restant = 0


            st.sidebar.info(
                f"Recherches gratuites restantes : {restant}"
            )



            if st.sidebar.button(
                "🚀 Passer Premium"
            ):


                st.sidebar.success(
                    "Premium bientôt disponible"
                )



# ==================================================
# INTERFACE PRINCIPALE
# ==================================================

def main():


    creer_base()

    remplir_base()


    init_session()


    authentification()


    afficher_profil()



    if "moteur" not in st.session_state:


        st.session_state.moteur = RechercheIT()



    st.markdown(
        "# 🤖 Assistant Dépannage IT"
    )


    st.write(
        "Décrivez votre problème informatique."
    )



    question = st.text_area(

        "Votre problème :",

        placeholder=
        "Exemple : mon PC est très lent, le wifi ne marche plus..."

    )



    if st.button(
        "🔍 Rechercher",
        type="primary"
    ):



        if question.strip() == "":


            st.warning(
                "Décrivez un problème."
            )

            return




        # compteur gratuit

        if (
            st.session_state.user
            and not st.session_state.premium
            and st.session_state.recherches >= LIMITE_GRATUITE
        ):


            st.error(

                "Limite gratuite atteinte. Passez Premium."

            )

            return




        resultats = st.session_state.moteur.rechercher(
            question
        )



        if st.session_state.user:


            st.session_state.recherches += 1




        if not resultats:


            st.warning(
                "Aucun diagnostic trouvé."
            )



        else:


            st.success(

                f"{len(resultats)} résultat(s) trouvé(s)"

            )



            for panne, score in resultats:



                with st.expander(

                    panne["titre"]

                    +

                    f"  ({score} points)"

                ):



                    st.markdown(

                        "**Catégorie :** "
                        +
                        panne["categorie"]

                    )


                    st.markdown(

                        "**Diagnostic :**\n"

                        +

                        panne["diagnostic"]

                    )


                    st.markdown(

                        "**Procédure :**\n"

                        +

                        panne["procedure"]

                    )



                    st.info(

                        "Questions : "

                        +

                        panne["questions"]

                    )



                    st.caption(

                        "Tags : "

                        +

                        panne["tags"]

                    )



# ==================================================
# DEMARRAGE
# ==================================================

if __name__ == "__main__":

    main()

    

    con.close()
