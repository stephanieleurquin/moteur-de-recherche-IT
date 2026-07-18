import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime, date
import hashlib
import random
import string
from io import BytesIO
import textwrap
import os

# ==================================================
# CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Assistant IT Pro - Premium",
    page_icon="💻",
    layout="wide"
)

DB = "assistant_it_pro.db"

# ==================================================
# CSS
# ==================================================

st.markdown("""
<style>
    .stApp { background-color: #0a0a0f; }
    h1, h2, h3 { color: #00d4ff !important; }
    p, li, label { color: #ffffff !important; }

    .stButton > button {
        background: linear-gradient(135deg, #00d4ff 0%, #0077be 100%) !important;
        color: #0a0a0f !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 12px 30px !important;
    }
    .stButton > button:hover {
        transform: scale(1.05) !important;
        box-shadow: 0 0 30px #00d4ff40 !important;
    }

    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: #1a1a2e !important;
        border: 2px solid #2a2a4a !important;
        border-radius: 12px !important;
        color: white !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #00d4ff !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================================================
# SESSION STATE
# ==================================================

if "user" not in st.session_state:
    st.session_state.user = None
if "premium" not in st.session_state:
    st.session_state.premium = False
if "plan" not in st.session_state:
    st.session_state.plan = "gratuit"
if "recherches" not in st.session_state:
    st.session_state.recherches = 0
if "recherches_jour" not in st.session_state:
    st.session_state.recherches_jour = 0
if "date_recherche" not in st.session_state:
    st.session_state.date_recherche = date.today()
if "page" not in st.session_state:
    st.session_state.page = "accueil"
if "moteur" not in st.session_state:
    st.session_state.moteur = None
if "montant_virement" not in st.session_state:
    st.session_state.montant_virement = 0
if "offre_virement" not in st.session_state:
    st.session_state.offre_virement = ""
if "plan_virement" not in st.session_state:
    st.session_state.plan_virement = ""
if "ref_virement" not in st.session_state:
    st.session_state.ref_virement = ""

# ==================================================
# OFFRES
# ==================================================

OFFRES = {
    "gratuit": {
        "nom": "Gratuit",
        "prix": "0€",
        "recherches": 3,
        "features": ["3 recherches par jour", "70+ diagnostics", "Diagnostics basiques"]
    },
    "pro": {
        "nom": "Pro",
        "prix": "9.90€/mois",
        "recherches": 999,
        "features": ["Recherches illimitées", "150+ diagnostics", "Diagnostics avancés", "Export PDF",
                     "Support prioritaire"]
    },
    "business": {
        "nom": "Business",
        "prix": "29.90€/mois",
        "recherches": 9999,
        "features": ["Recherches illimitées", "150+ diagnostics", "Diagnostics experts", "Export PDF/Word",
                     "Support 24/7", "Accès API", "5 comptes inclus"]
    }
}

# ==================================================
# BASE DE DONNEES
# ==================================================

def connexion_db():
    return sqlite3.connect(DB)

def creer_base():
    conn = connexion_db()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS pannes
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    titre
                    TEXT,
                    description
                    TEXT,
                    diagnostic
                    TEXT,
                    procedure
                    TEXT,
                    questions
                    TEXT,
                    categorie
                    TEXT,
                    niveau
                    INTEGER,
                    tags
                    TEXT
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS utilisateurs
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    email
                    TEXT
                    UNIQUE,
                    password
                    TEXT,
                    plan
                    TEXT
                    DEFAULT
                    'gratuit',
                    premium
                    INTEGER
                    DEFAULT
                    0,
                    recherches
                    INTEGER
                    DEFAULT
                    0,
                    date_inscription
                    TEXT
                )
                """)
    conn.commit()
    conn.close()

def remplir_base():
    conn = connexion_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM pannes")
    if cur.fetchone()[0] == 0:
        # Vos données ici (je les ai tronquées pour la lisibilité, mais gardez tout votre contenu)
        donnees = [
             # Windows - Installation
            ("Windows ne s'installe pas", "L'installation de Windows échoue",
             "Problème de clé USB ou de pilote manquant",
             "1- Vérifier la clé USB\n2- Désactiver Secure Boot\n3- Installer les pilotes manuellement",
             "Quelle version de Windows ?", "Windows", 4, "installation,windows"),
            ("Windows demande une clé", "Windows demande une clé d'activation", "Clé manquante ou invalide",
             "1- Vérifier la clé\n2- Contacter Microsoft\n3- Utiliser une clé générique", "Avez-vous une clé valide ?",
             "Windows", 2, "cle,activation,windows"),
            ("Windows Update échoue", "Les mises à jour Windows ne s'installent pas", "Problème de cache ou de service",
             "1- Arrêter le service Update\n2- Vider le cache\n3- Redémarrer le service", "Quelle est l'erreur ?",
             "Windows", 3, "update,windows"),
            ("Windows Update tourne en boucle", "Windows Update se bloque", "Mise à jour bloquée",
             "1- Forcer l'arrêt\n2- Vider le cache\n3- Désinstaller la mise à jour", "Depuis quand ?", "Windows", 3,
             "update,windows"),
            ("C:\ plein", "Le disque C: est saturé", "Fichiers temporaires ou applications",
             "1- Nettoyer le disque\n2- Vider la corbeille\n3- Désinstaller des applications",
             "Quelle taille fait-il ?", "Windows", 2, "disque,plein,windows"),
            ("D:\ non reconnu", "Le disque D: n'apparaît plus", "Problème de partition ou de câble",
             "1- Vérifier le câble\n2- Utiliser Gestion des disques\n3- Tester le disque",
             "Le disque fait-il du bruit ?", "Windows", 4, "disque,partition,windows"),
            ("Windows freeze", "Windows se fige", "Manque de RAM ou CPU",
             "1- Ouvrir Gestionnaire des tâches\n2- Vérifier la RAM\n3- Désactiver les animations",
             "Quelle application est ouverte ?", "Windows", 3, "freeze,windows"),
            ("Windows rame au démarrage", "Windows met du temps à démarrer", "Trop de programmes au démarrage",
             "1- Désactiver les programmes\n2- Nettoyer le disque\n3- Activer Fast Boot", "Depuis quand ?", "Windows",
             2, "demarrage,windows"),
            ("Fichier système corrompu", "SFC trouve des erreurs", "Fichiers système endommagés",
             "1- Exécuter sfc /scannow\n2- Exécuter DISM\n3- Réparer l'installation", "Quel est l'erreur ?", "Windows",
             4, "systeme,corrompu,windows"),
            ("Registre corrompu", "Erreurs dans le registre", "Registre endommagé",
             "1- Utiliser CCleaner\n2- Restaurer le registre\n3- Réinstaller Windows", "Depuis quand ?", "Windows", 5,
             "registre,windows"),

            # Windows - Pilotes
            ("Pilote écran ne fonctionne pas", "L'écran s'affiche mal", "Pilote graphique corrompu",
             "1- Télécharger le pilote\n2- Désinstaller l'ancien\n3- Installer le nouveau", "Quelle carte graphique ?",
             "Windows", 3, "pilote,ecran,windows"),
            ("Pilote réseau manquant", "Pas de connexion Internet", "Pilote réseau manquant",
             "1- Télécharger le pilote\n2- Installer en mode sans échec\n3- Utiliser une clé USB",
             "Quelle carte réseau ?", "Windows", 3, "pilote,reseau,windows"),
            ("Problème d'imprimante", "L'imprimante ne fonctionne pas", "Pilote d'imprimante manquant",
             "1- Télécharger le pilote\n2- Installer manuellement\n3- Vérifier le port USB", "Quelle imprimante ?",
             "Windows", 3, "pilote,imprimante,windows"),
            ("Pilote audio ne fonctionne pas", "Pas de son sur le PC", "Pilote audio corrompu",
             "1- Télécharger le pilote\n2- Désinstaller l'ancien\n3- Installer le nouveau", "Quelle carte son ?",
             "Windows", 3, "pilote,audio,windows"),

            # Windows - Réseau
            ("Connexion limitée", "WiFi connecté mais pas d'Internet", "Problème de DNS ou DHCP",
             "1- Vider le cache DNS\n2- Renouveler l'IP\n3- Redémarrer le routeur", "Le WiFi s'affiche ?", "Windows", 3,
             "reseau,connexion,windows"),
            ("Pas de WiFi", "Le WiFi ne s'affiche pas", "Pilote WiFi désactivé",
             "1- Vérifier l'adaptateur\n2- Activer le WiFi\n3- Redémarrer le service", "Le PC a-t-il un bouton WiFi ?",
             "Windows", 3, "wifi,reseau,windows"),
            ("Problème de proxy", "Internet ne fonctionne pas", "Proxy mal configuré",
             "1- Désactiver le proxy\n2- Vérifier les paramètres\n3- Contacter l'admin", "Utilisez-vous un proxy ?",
             "Windows", 4, "proxy,reseau,windows"),
            ("Problème de VPN Windows", "Le VPN ne se connecte pas", "Configuration VPN incorrecte",
             "1- Vérifier les identifiants\n2- Changer de serveur\n3- Réinstaller le VPN", "Quelle est l'erreur ?",
             "Windows", 4, "vpn,reseau,windows"),
            ("DNS ne répond pas", "Impossible de résoudre les noms", "Serveur DNS hors service",
             "1- Utiliser Google DNS\n2- Vider le cache\n3- Redémarrer le service", "Quel est votre DNS ?", "Windows",
             3, "dns,reseau,windows"),

            # Windows - Application
            ("Excel ne s'ouvre pas", "Excel se bloque au démarrage", "Fichier corrompu ou add-in",
             "1- Ouvrir en mode sans échec\n2- Désactiver les add-ins\n3- Réparer Office", "Quelle version d'Office ?",
             "Windows", 3, "excel,windows"),
            ("Word ne fonctionne pas", "Word ne s'ouvre pas", "Problème de fichier",
             "1- Ouvrir en mode sans échec\n2- Réparer Office\n3- Réinstaller", "Quelle version ?", "Windows", 3,
             "word,windows"),
            ("Outlook ne démarre pas", "Outlook se bloque", "Fichier .pst corrompu",
             "1- Ouvrir en mode sans échec\n2- Réparer le fichier .pst\n3- Créer un nouveau profil",
             "Quelle taille fait le fichier .pst ?", "Windows", 4, "outlook,windows"),
            ("Teams ne fonctionne pas", "Teams ne se connecte pas", "Cache corrompu",
             "1- Vider le cache\n2- Réinstaller Teams\n3- Vérifier le proxy", "L'application se lance ?", "Windows", 3,
             "teams,windows"),
            ("OneDrive ne synchronise pas", "OneDrive bloqué", "Problème de synchronisation",
             "1- Vider le cache\n2- Réinitialiser OneDrive\n3- Vérifier le stockage", "Quel est l'erreur ?", "Windows",
             3, "onedrive,windows"),
            ("Chrome ne fonctionne pas", "Chrome se bloque", "Cache ou extension",
             "1- Vider le cache\n2- Désactiver les extensions\n3- Réinstaller Chrome", "Quelle est l'erreur ?",
             "Windows", 2, "chrome,windows"),
            ("Firefox ne fonctionne pas", "Firefox se bloque", "Problème de cache",
             "1- Vider le cache\n2- Désactiver les extensions\n3- Réinstaller", "Quelle version ?", "Windows", 2,
             "firefox,windows"),
            ("Adobe ne fonctionne pas", "Adobe PDF ne s'ouvre pas", "Problème d'Adobe",
             "1- Réparer Adobe\n2- Réinstaller\n3- Télécharger une mise à jour", "Quelle version d'Adobe ?", "Windows",
             3, "adobe,windows"),
            ("Application plante", "L'application se bloque", "Manque de mémoire",
             "1- Augmenter la RAM\n2- Fermer les applications\n3- Réinstaller", "Quelle application ?", "Windows", 3,
             "application,windows"),

            # Windows - Sécurité
            ("Windows Defender désactivé", "Antivirus Windows est désactivé", "Politique de sécurité",
             "1- Activer Windows Defender\n2- Vérifier le registre\n3- Réinstaller Defender", "Que dit l'erreur ?",
             "Windows", 3, "defender,securite,windows"),
            ("Erreur de pare-feu", "Le pare-feu bloque tout", "Configuration trop stricte",
             "1- Désactiver temporairement\n2- Ajouter des règles\n3- Réinitialiser",
             "Quelle application est bloquée ?", "Windows", 3, "firewall,securite,windows"),
            ("Problème de BitLocker", "BitLocker demande la clé", "Clé de récupération",
             "1- Trouver la clé\n2- Désactiver BitLocker\n3- Contacter l'admin", "Où est la clé ?", "Windows", 5,
             "bitlocker,securite,windows"),
            ("Problème de ransomware", "Fichiers chiffrés", "Ransomware",
             "1- Déconnecter du réseau\n2- Contacter un expert\n3- Utiliser un outil de décryptage",
             "Avez-vous une sauvegarde ?", "Windows", 5, "ransomware,securite,windows"),
            ("Phishing détecté", "Email suspect reçu", "Phishing",
             "1- Ne pas cliquer\n2- Signaler l'email\n3- Changer les mots de passe", "Avez-vous cliqué ?", "Windows", 4,
             "phishing,securite,windows"),
            ("Compte Microsoft piraté", "Le compte Microsoft est piraté", "Mot de passe volé",
             "1- Changer le mot de passe\n2- Activer 2FA\n3- Contacter Microsoft", "Le compte est-il actif ?",
             "Windows", 5, "pirate,securite,windows"),

            # Windows - Bureau
            ("Icônes disparues", "Les icônes du bureau ont disparu", "Problème d'affichage",
             "1- Cliquer droit -> Afficher\n2- Redémarrer l'explorateur\n3- Vérifier les paramètres",
             "Que s'est-il passé ?", "Windows", 2, "icones,bureau,windows"),
            ("Barre des tâches ne fonctionne pas", "La barre des tâches ne répond plus", "Explorateur Windows bloqué",
             "1- Redémarrer l'explorateur\n2- Vérifier les paramètres\n3- Désactiver les notifications",
             "Depuis quand ?", "Windows", 3, "barre-taches,windows"),
            ("Écran noir au démarrage", "Écran noir après le logo Windows", "Pilote ou fichier système",
             "1- Démarrer en mode sans échec\n2- Désinstaller le pilote\n3- Restaurer le système",
             "Quel est le code d'erreur ?", "Windows", 4, "ecran-noir,windows"),
            ("Écran bleu", "Écran bleu de la mort", "Pilote ou matériel",
             "1- Noter le code d'erreur\n2- Démarrer en mode sans échec\n3- Vérifier le matériel", "Quel est le code ?",
             "Windows", 5, "bsod,windows"),
            ("Écran blanc", "Écran blanc au démarrage", "Problème d'affichage",
             "1- Vérifier le câble\n2- Tester un autre écran\n3- Démarrer en mode sans échec", "Le PC démarre-t-il ?",
             "Windows", 3, "ecran-blanc,windows"),
            ("Problème de résolution", "Résolution trop grande ou trop petite", "Paramètres d'affichage",
             "1- Changer la résolution\n2- Mettre à jour le pilote\n3- Vérifier le câble", "Quelle résolution ?",
             "Windows", 2, "resolution,windows"),
            ("L'écran clignote", "L'écran clignote ou scintille", "Problème de pilote",
             "1- Mettre à jour le pilote\n2- Changer le taux de rafraîchissement\n3- Tester un autre écran",
             "Depuis quand ?", "Windows", 3, "clignote,ecran,windows"),
            # Linux - Distribution
            ("Ubuntu ne démarre pas", "Ubuntu reste bloqué au démarrage", "Problème de noyau ou de GRUB",
             "1- Démarrer en mode recovery\n2- Réparer GRUB\n3- Réinstaller le noyau", "Quelle version d'Ubuntu ?",
             "Linux", 4, "ubuntu,demarrage,linux"),
            ("Debian ne démarre pas", "Debian ne démarre pas", "Problème de GRUB",
             "1- Démarrer en mode rescue\n2- Réparer GRUB\n3- Réinstaller le noyau", "Quelle version de Debian ?",
             "Linux", 4, "debian,demarrage,linux"),
            ("Arch Linux ne démarre pas", "Arch Linux ne démarre pas", "Problème de noyau ou de GRUB",
             "1- Démarrer en mode fallback\n2- Réparer GRUB\n3- Réinstaller le noyau", "Quelle version d'Arch ?",
             "Linux", 4, "arch,demarrage,linux"),
            ("Fedora ne démarre pas", "Fedora ne démarre pas", "Problème de GRUB",
             "1- Démarrer en mode rescue\n2- Réparer GRUB\n3- Réinstaller le noyau", "Quelle version de Fedora ?",
             "Linux", 4, "fedora,demarrage,linux"),
            ("Linux Mint ne démarre pas", "Linux Mint ne démarre pas", "Problème de GRUB",
             "1- Démarrer en mode recovery\n2- Réparer GRUB\n3- Réinstaller le noyau", "Quelle version de Mint ?",
             "Linux", 4, "mint,demarrage,linux"),
            ("Dual boot Windows/Linux ne fonctionne pas", "Le dual boot ne fonctionne pas", "Problème de GRUB",
             "1- Réparer GRUB\n2- Réinstaller GRUB\n3- Vérifier le fichier grub.cfg", "Quel OS est installé ?", "Linux",
             4, "dual-boot,linux,windows"),
            ("GRUB ne s'affiche pas", "GRUB ne s'affiche pas", "Problème de GRUB",
             "1- Réparer GRUB\n2- Réinstaller GRUB\n3- Vérifier le BIOS", "Quel est le message d'erreur ?", "Linux", 4,
             "grub,linux,boot"),
            ("Erreur GRUB rescue", "GRUB affiche 'grub rescue>'", "Problème de GRUB",
             "1- Identifier la partition\n2- Réinstaller GRUB\n3- Utiliser un live USB", "Quelle est l'erreur ?",
             "Linux", 5, "grub,linux,boot"),

            # Linux - Performance
            ("Linux est très lent", "Linux rame", "Swap plein ou processus en arrière-plan",
             "1- Vérifier avec htop\n2- Vider la mémoire swap\n3- Désactiver les services inutiles",
             "Quelle distribution ?", "Linux", 2, "lent,performance,linux"),
            ("Linux freeze", "Linux se fige", "Manque de RAM",
             "1- Vérifier avec htop\n2- Augmenter la swap\n3- Tuer les processus", "Quelle est l'application ?",
             "Linux", 3, "freeze,linux"),
            ("La mémoire swap est pleine", "La mémoire swap est saturée", "Swap pleine",
             "1- Libérer de la swap\n2- Augmenter la swap\n3- Réduire les processus", "Quelle taille de swap ?",
             "Linux", 3, "swap,performance,linux"),
            ("Le système est lent au démarrage", "Linux met du temps à démarrer", "Trop de services",
             "1- Désactiver les services\n2- Utiliser systemd-analyze\n3- Désactiver les services inutiles",
             "Depuis quand ?", "Linux", 2, "demarrage,performance,linux"),

            # Linux - Paquets
            ("Apt-get ne fonctionne pas", "Apt-get ne fonctionne pas", "Paquets corrompus",
             "1- Utiliser apt-get install -f\n2- Vider le cache\n3- Réinstaller le paquet",
             "Quel est le message d'erreur ?", "Linux", 3, "apt,paquets,linux"),
            ("Dpkg verrouillé", "Dpkg est verrouillé", "Processus dpkg en cours",
             "1- Vérifier les processus\n2- Tuer dpkg\n3- Supprimer le verrou", "Que dit l'erreur ?", "Linux", 3,
             "dpkg,paquets,linux"),
            ("Paquet corrompu", "Paquet endommagé", "Paquet corrompu",
             "1- Réinstaller le paquet\n2- Purger le paquet\n3- Installer depuis les sources", "Quel paquet ?", "Linux",
             3, "paquet,corrompu,linux"),
            ("Problème de dépendances", "Dépendances non satisfaites", "Dépendances manquantes",
             "1- Utiliser apt-get install -f\n2- Vérifier les dépendances\n3- Installer manuellement",
             "Quelle dépendance ?", "Linux", 3, "dependances,paquets,linux"),
            ("Problème de Snap", "Snap ne fonctionne pas", "Problème de Snap",
             "1- Réinstaller Snap\n2- Vider le cache\n3- Désactiver Snap", "Quel est le problème ?", "Linux", 3,
             "snap,paquets,linux"),
            ("Problème de Flatpak", "Flatpak ne fonctionne pas", "Problème de Flatpak",
             "1- Réinstaller Flatpak\n2- Mettre à jour\n3- Vérifier les permissions", "Quel est le problème ?", "Linux",
             3, "flatpak,paquets,linux"),

            # Linux - Permissions
            ("Permission denied", "Permission non accordée", "Problème de droits",
             "1- Utiliser chmod\n2- Utiliser chown\n3- Vérifier le propriétaire", "Quel est le fichier ?", "Linux", 3,
             "permission,linux"),
            ("Sudo ne fonctionne pas", "Sudo ne fonctionne pas", "Problème de sudoers",
             "1- Vérifier le fichier sudoers\n2- Ajouter l'utilisateur\n3- Réinitialiser les droits",
             "Que dit l'erreur ?", "Linux", 4, "sudo,permission,linux"),
            ("Problème de root", "Mot de passe root oublié", "Mot de passe root",
             "1- Démarrer en mode recovery\n2- Réinitialiser le mot de passe\n3- Redémarrer", "Avez-vous un live USB ?",
             "Linux", 4, "root,permission,linux"),
            ("Problème de chmod", "chmod ne fonctionne pas", "Problème de droits",
             "1- Vérifier les droits\n2- Utiliser chmod -R\n3- Utiliser chown", "Quel est le fichier ?", "Linux", 3,
             "chmod,permission,linux"),

            # Linux - SSH
            ("SSH ne se connecte pas", "Impossible de se connecter en SSH", "Service SSH arrêté ou pare-feu",
             "1- Vérifier le service SSH\n2- Vérifier le pare-feu\n3- Vérifier les permissions",
             "Quelle est l'erreur SSH ?", "Linux", 4, "ssh,reseau,linux"),
            ("SSH permission refusée", "Permission refusée en SSH", "Mot de passe ou clé",
             "1- Vérifier le mot de passe\n2- Vérifier la clé\n3- Vérifier le fichier authorized_keys",
             "Utilisez-vous une clé ?", "Linux", 4, "ssh,permission,linux"),
            ("SSH timeout", "Timeout en SSH", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier le pare-feu\n3- Vérifier le service SSH", "Le serveur est-il allumé ?",
             "Linux", 4, "ssh,timeout,linux"),
            ("Problème de clé SSH", "Clé SSH invalide", "Clé SSH corrompue",
             "1- Générer une nouvelle clé\n2- Ajouter la clé\n3- Vérifier les permissions", "Avez-vous une clé ?",
             "Linux", 4, "ssh,cle,linux"),

            # Linux - Docker
            ("Docker ne démarre pas", "Docker ne fonctionne pas", "Problème de service Docker",
             "1- Vérifier le service\n2- Réinstaller Docker\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Linux", 4, "docker,linux"),
            ("Docker image ne fonctionne pas", "L'image Docker ne fonctionne pas", "Problème d'image",
             "1- Vérifier l'image\n2- Rebuild\n3- Vérifier les logs", "Quelle est l'image ?", "Linux", 4,
             "docker,image,linux"),
            ("Docker container ne démarre pas", "Le container Docker ne démarre pas", "Problème de container",
             "1- Vérifier les logs\n2- Vérifier la configuration\n3- Rebuild", "Quel est le container ?", "Linux", 4,
             "docker,container,linux"),
            ("Problème de Docker Compose", "Docker Compose ne fonctionne pas", "Problème de configuration",
             "1- Vérifier le fichier\n2- Rebuild\n3- Vérifier les services", "Quelle est l'erreur ?", "Linux", 4,
             "docker,compose,linux"),
            ("Docker volume ne fonctionne pas", "Le volume Docker ne fonctionne pas", "Problème de volume",
             "1- Vérifier le volume\n2- Recréer le volume\n3- Vérifier les permissions", "Quel est le volume ?",
             "Linux", 4, "docker,volume,linux"),

            # Linux - Réseau
            ("Pas de connexion réseau Linux", "Pas de réseau sous Linux", "Service réseau arrêté",
             "1- Vérifier le service\n2- Vérifier le câble\n3- Vérifier le DHCP", "Que dit ifconfig ?", "Linux", 3,
             "reseau,linux"),
            ("DNS ne fonctionne pas Linux", "DNS ne résout pas les noms", "Problème de DNS",
             "1- Utiliser 8.8.8.8\n2- Vider le cache\n3- Vérifier resolv.conf", "Quel est votre DNS ?", "Linux", 3,
             "dns,reseau,linux"),
            ("Problème de firewall Linux", "Pare-feu bloque tout", "Problème de firewall",
             "1- Désactiver temporairement\n2- Ajouter des règles\n3- Vérifier UFW", "Quelle est l'application ?",
             "Linux", 3, "firewall,reseau,linux"),
            ("Problème de VPN Linux", "Le VPN ne se connecte pas", "Problème de VPN",
             "1- Vérifier les identifiants\n2- Changer de serveur\n3- Réinstaller le VPN", "Quelle est l'erreur ?",
             "Linux", 4, "vpn,reseau,linux"),

            # Linux - Services
            ("Service systemd ne fonctionne pas", "Le service systemd ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Réinstaller le service", "Quel service ?", "Linux", 4,
             "systemd,service,linux"),
            ("Apache ne fonctionne pas", "Apache ne démarre pas", "Problème d'Apache",
             "1- Vérifier le service\n2- Vérifier le port\n3- Vérifier les logs", "Que dit l'erreur ?", "Linux", 4,
             "apache,service,linux"),
            ("MySQL ne fonctionne pas", "MySQL ne démarre pas", "Problème de MySQL",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Réparer la base", "Quelle est l'erreur ?", "Linux", 4,
             "mysql,service,linux"),
            ("PostgreSQL ne fonctionne pas", "PostgreSQL ne démarre pas", "Problème de PostgreSQL",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Réparer la base", "Quelle est l'erreur ?", "Linux", 4,
             "postgresql,service,linux"),
            ("Nginx ne fonctionne pas", "Nginx ne démarre pas", "Problème de Nginx",
             "1- Vérifier le service\n2- Vérifier le port\n3- Vérifier les logs", "Que dit l'erreur ?", "Linux", 4,
             "nginx,service,linux"),

            # Linux - Fichiers
            ("Problème de système de fichiers", "Système de fichiers corrompu", "Problème de filesystem",
             "1- Utiliser fsck\n2- Vérifier les disques\n3- Réparer le système", "Quel est le système ?", "Linux", 4,
             "filesystem,linux"),
            ("Partition full Linux", "Partition pleine", "Disque plein",
             "1- Vider les logs\n2- Supprimer les fichiers temporaires\n3- Augmenter la partition",
             "Quelle partition ?", "Linux", 3, "partition,plein,linux"),
            ("Problème de NFS", "NFS ne fonctionne pas", "Problème de NFS",
             "1- Vérifier le service\n2- Vérifier le montage\n3- Vérifier les logs", "Quelle est l'erreur ?", "Linux",
             4, "nfs,linux"),
            ("Problème de Samba", "Samba ne fonctionne pas", "Problème de Samba",
             "1- Vérifier le service\n2- Vérifier le smb.conf\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Linux", 4, "samba,linux"),
            ("Problème de swap Linux", "La swap ne fonctionne pas", "Problème de swap",
             "1- Vérifier la swap\n2- Recréer la swap\n3- Vérifier le fstab", "Quelle est l'erreur ?", "Linux", 3,
             "swap,linux"),
            # MacOS - Démarrage
            ("Mac ne démarre pas", "Mac reste bloqué sur écran blanc", "Problème de disque ou de système",
             "1- Démarrer en mode sans échec\n2- Utiliser la récupération macOS\n3- Réinstaller macOS",
             "Y a-t-il un bruit de disque ?", "MacOS", 4, "demarrage,mac,apple"),
            ("Mac reboot en boucle", "Le Mac redémarre en boucle", "Problème de système",
             "1- Démarrer en mode sans échec\n2- Utiliser la récupération\n3- Réinstaller", "Quelle version de macOS ?",
             "MacOS", 4, "reboot,mac,apple"),
            ("Mac sur écran gris", "Mac reste sur écran gris", "Problème de disque",
             "1- Démarrer en mode sans échec\n2- Utiliser Utilitaires\n3- Réparer le disque",
             "Le disque est-il reconnu ?", "MacOS", 4, "ecran-gris,mac,apple"),
            ("Mac sur écran noir", "Mac reste sur écran noir", "Problème de carte graphique",
             "1- Démarrer en mode sans échec\n2- Vérifier le câble\n3- Réinstaller macOS", "L'écran s'allume-t-il ?",
             "MacOS", 4, "ecran-noir,mac,apple"),

            # MacOS - Performance
            ("Mac très lent", "Mac rame", "Disque plein ou mémoire insuffisante",
             "1- Vérifier l'espace disque\n2- Nettoyer les caches\n3- Réduire les programmes au démarrage",
             "Depuis quand ?", "MacOS", 2, "lent,performance,mac"),
            ("Mac freeze", "Le Mac se fige", "Manque de RAM",
             "1- Vérifier le moniteur d'activité\n2- Fermer les applications\n3- Redémarrer",
             "Quelle est l'application ?", "MacOS", 3, "freeze,mac"),
            ("Mac chauffe", "Mac très chaud", "Ventilation bloquée",
             "1- Nettoyer les ventilateurs\n2- Vérifier les processus\n3- Réduire la charge", "Depuis quand ?", "MacOS",
             3, "chauffe,mac"),
            ("Mac ventilateur très bruyant", "Ventilateurs très bruyants", "Problème de ventilation",
             "1- Vérifier les processus\n2- Nettoyer les ventilateurs\n3- Vérifier la température",
             "Que dit le moniteur ?", "MacOS", 3, "ventilateur,bruit,mac"),

            # MacOS - Mises à jour
            ("macOS ne se met pas à jour", "La mise à jour macOS échoue", "Espace insuffisant ou connexion",
             "1- Vérifier l'espace disque\n2- Vider les caches\n3- Télécharger manuellement",
             "Quelle version de macOS ?", "MacOS", 3, "update,mac,apple"),
            ("macOS installé mais ne démarre pas", "macOS installé mais ne démarre pas", "Problème de système",
             "1- Démarrer en mode sans échec\n2- Utiliser la récupération\n3- Réinstaller", "Quelle version ?", "MacOS",
             4, "install,mac,apple"),
            ("Problème de mise à jour de sécurité", "Mise à jour de sécurité échoue", "Problème de mise à jour",
             "1- Vérifier l'espace\n2- Vider les caches\n3- Télécharger manuellement", "Quelle est l'erreur ?", "MacOS",
             3, "update,securite,mac"),

            # MacOS - Applications
            ("Application ne s'ouvre pas sur Mac", "Application ne s'ouvre pas", "Problème de permission",
             "1- Vérifier les permissions\n2- Réinstaller l'application\n3- Vérifier Gatekeeper",
             "Quelle application ?", "MacOS", 3, "application,mac"),
            ("Application plante sur Mac", "Application plante", "Manque de mémoire",
             "1- Vérifier le moniteur\n2- Réinstaller l'application\n3- Mettre à jour", "Quelle application ?", "MacOS",
             3, "application,plante,mac"),
            ("Problème de Gatekeeper", "Gatekeeper bloque l'application", "Problème de sécurité",
             "1- Désactiver temporairement\n2- Ajouter l'application\n3- Vérifier les permissions",
             "Que dit l'erreur ?", "MacOS", 3, "gatekeeper,securite,mac"),
            ("Problème de Notarization", "Application non notarisée", "Problème de sécurité",
             "1- Vérifier la notarisation\n2- Désactiver temporairement\n3- Utiliser le terminal", "Que dit l'erreur ?",
             "MacOS", 3, "notarization,securite,mac"),

            # MacOS - Disque
            ("Disque Mac non reconnu", "Disque externe non reconnu", "Problème de formatage",
             "1- Vérifier le câble\n2- Vérifier le format\n3- Utiliser Utilitaire de disque", "Quel est le format ?",
             "MacOS", 3, "disque,mac"),
            ("Disque Mac plein", "Disque saturé", "Disque plein",
             "1- Vider la corbeille\n2- Nettoyer les caches\n3- Supprimer des fichiers", "Quelle taille ?", "MacOS", 2,
             "disque,plein,mac"),
            ("Disque Mac corrompu", "Disque corrompu", "Problème de disque",
             "1- Utiliser Utilitaire de disque\n2- Réparer le disque\n3- Sauvegarder les données",
             "Que dit l'utilitaire ?", "MacOS", 4, "disque,corrompu,mac"),

            # MacOS - Réseau
            ("WiFi Mac ne se connecte pas", "Impossible de se connecter au WiFi", "Problème de WiFi",
             "1- Redémarrer le WiFi\n2- Oublier le réseau\n3- Redémarrer le Mac", "Le WiFi s'affiche-t-il ?", "MacOS",
             2, "wifi,mac,reseau"),
            ("Mac pas de réseau", "Pas de réseau sur Mac", "Problème de DHCP",
             "1- Vérifier le DHCP\n2- Renouveler l'IP\n3- Vérifier le câble", "Que dit l'erreur ?", "MacOS", 3,
             "reseau,mac"),
            ("VPN Mac ne fonctionne pas", "Le VPN ne se connecte pas", "Problème de VPN",
             "1- Vérifier les identifiants\n2- Changer de serveur\n3- Réinstaller le VPN", "Quelle est l'erreur ?",
             "MacOS", 4, "vpn,mac,reseau"),

            # MacOS - Sécurité
            ("Mac virus", "Virus détecté sur Mac", "Malware",
             "1- Exécuter Malwarebytes\n2- Vérifier les extensions\n3- Réinstaller macOS", "Que détecte-t-il ?",
             "MacOS", 4, "virus,securite,mac"),
            ("Mac compte piraté", "Compte piraté sur Mac", "Mot de passe volé",
             "1- Changer le mot de passe\n2- Activer 2FA\n3- Vérifier les connexions", "Le compte est-il actif ?",
             "MacOS", 5, "pirate,securite,mac"),
            ("Mac pare-feu bloqué", "Pare-feu bloque tout", "Problème de pare-feu",
             "1- Vérifier le pare-feu\n2- Ajouter des règles\n3- Désactiver temporairement", "Quelle application ?",
             "MacOS", 3, "firewall,securite,mac"),
            ("Mac ransomware", "Fichiers chiffrés sur Mac", "Ransomware",
             "1- Déconnecter du réseau\n2- Contacter un expert\n3- Utiliser un outil de décryptage",
             "Avez-vous une sauvegarde ?", "MacOS", 5, "ransomware,securite,mac"),

            # MacOS - Hardware
            ("Mac ne charge pas", "Le Mac ne charge pas", "Problème de chargeur",
             "1- Vérifier le chargeur\n2- Vérifier le port\n3- Contacter l'assistance", "Le chargeur est-il branché ?",
             "MacOS", 3, "charge,mac"),
            ("Mac écran clignote", "L'écran du Mac clignote", "Problème de carte graphique",
             "1- Vérifier le câble\n2- Redémarrer\n3- Contacter l'assistance", "Depuis quand ?", "MacOS", 3,
             "ecran,clignote,mac"),
            ("Mac clavier ne fonctionne pas", "Le clavier du Mac ne fonctionne pas", "Problème de clavier",
             "1- Vérifier le câble\n2- Vérifier le Bluetooth\n3- Redémarrer", "Le clavier est-il connecté ?", "MacOS",
             3, "clavier,mac"),
            ("Mac souris ne fonctionne pas", "La souris du Mac ne fonctionne pas", "Problème de souris",
             "1- Vérifier le câble\n2- Vérifier le Bluetooth\n3- Redémarrer", "La souris est-elle connectée ?", "MacOS",
             3, "souris,mac"),
            ("Mac touchpad ne fonctionne pas", "Le touchpad du Mac ne fonctionne pas", "Problème de touchpad",
             "1- Vérifier les paramètres\n2- Redémarrer\n3- Contacter l'assistance", "Que dit l'erreur ?", "MacOS", 3,
             "touchpad,mac"),
            # Réseau - WiFi
            ("WiFi ne se connecte pas", "Impossible de se connecter au WiFi", "Mot de passe incorrect ou signal faible",
             "1- Vérifier le mot de passe\n2- Se rapprocher de la box\n3- Redémarrer le routeur",
             "Le WiFi s'affiche-t-il ?", "Reseau", 2, "wifi,connexion,reseau"),
            ("WiFi connecté mais pas d'Internet", "WiFi connecté mais pas d'accès Internet", "Problème de DNS ou DHCP",
             "1- Vider le cache DNS\n2- Renouveler l'IP\n3- Redémarrer le routeur", "Le WiFi est-il connecté ?",
             "Reseau", 3, "wifi,internet,reseau"),
            ("WiFi lent", "WiFi très lent", "Interférences ou bande passante",
             "1- Changer de canal\n2- Se rapprocher de la box\n3- Passer en 5GHz", "Quelle est votre vitesse ?",
             "Reseau", 2, "wifi,lent,reseau"),
            ("WiFi se déconnecte", "WiFi se déconnecte sans cesse", "Problème de pilote ou de routeur",
             "1- Mettre à jour le pilote\n2- Changer de canal\n3- Redémarrer le routeur", "Depuis quand ?", "Reseau", 3,
             "wifi,deconnexion,reseau"),
            ("WiFi non disponible", "Le WiFi n'est pas disponible", "Carte WiFi désactivée",
             "1- Activer le WiFi\n2- Vérifier le pilote\n3- Vérifier le BIOS", "Le WiFi est-il activé ?", "Reseau", 3,
             "wifi,indisponible,reseau"),
            ("WiFi mot de passe oublié", "Mot de passe WiFi oublié", "Mot de passe perdu",
             "1- Vérifier sur le routeur\n2- Réinitialiser le mot de passe\n3- Contacter le FAI",
             "Avez-vous accès au routeur ?", "Reseau", 2, "wifi,mot-de-passe,reseau"),
            ("WiFi 5GHz ne fonctionne pas", "Le WiFi 5GHz ne fonctionne pas", "Problème de compatibilité",
             "1- Vérifier le pilote\n2- Changer de canal\n3- Activer le 5GHz", "Le 5GHz est-il activé ?", "Reseau", 3,
             "wifi,5ghz,reseau"),
            ("WiFi captive portal", "Page de connexion WiFi ne s'affiche pas", "Problème de captive portal",
             "1- Ouvrir un navigateur\n2- Tenter http://neverssl.com\n3- Vérifier le proxy",
             "La page s'affiche-t-elle ?", "Reseau", 3, "wifi,captive,reseau"),

            # Réseau - Ethernet
            ("Ethernet ne fonctionne pas", "Le câble Ethernet n'est pas reconnu", "Câble ou carte réseau défectueuse",
             "1- Vérifier le câble\n2- Vérifier la carte réseau\n3- Réinstaller le pilote", "La LED est-elle allumée ?",
             "Reseau", 3, "ethernet,reseau"),
            ("Ethernet lent", "Connexion Ethernet lente", "Problème de câble ou de carte",
             "1- Vérifier le câble\n2- Vérifier la carte\n3- Changer de port", "Quelle est la vitesse ?", "Reseau", 3,
             "ethernet,lent,reseau"),
            ("Ethernet non détecté", "La carte Ethernet n'est pas détectée", "Pilote manquant",
             "1- Installer le pilote\n2- Vérifier le BIOS\n3- Vérifier le matériel", "La carte est-elle visible ?",
             "Reseau", 4, "ethernet,detecte,reseau"),
            ("Problème de switch Ethernet", "Le switch ne fonctionne pas", "Problème de switch",
             "1- Vérifier l'alimentation\n2- Vérifier les câbles\n3- Redémarrer le switch",
             "Les LEDs sont-elles allumées ?", "Reseau", 3, "ethernet,switch,reseau"),

            # Réseau - DNS
            ("Problème de DNS", "Impossible de résoudre les noms", "DNS mal configuré ou serveur HS",
             "1- Utiliser Google DNS (8.8.8.8)\n2- Vider le cache DNS\n3- Changer de serveur DNS",
             "Quel est votre serveur DNS ?", "Reseau", 3, "dns,reseau"),
            ("DNS ne répond pas", "Le serveur DNS ne répond pas", "Serveur DNS hors service",
             "1- Utiliser un autre DNS\n2- Vider le cache\n3- Redémarrer le service", "Quel est l'erreur ?", "Reseau",
             3, "dns,repond,reseau"),
            ("DNS cache pollué", "Le cache DNS est pollué", "Problème de cache",
             "1- Vider le cache DNS\n2- Redémarrer le service\n3- Utiliser un autre DNS", "Depuis quand ?", "Reseau", 3,
             "dns,cache,reseau"),
            ("DNS over HTTPS", "Problème avec DNS over HTTPS", "Configuration DoH",
             "1- Désactiver DoH\n2- Vérifier la configuration\n3- Utiliser un autre DNS", "Utilisez-vous DoH ?",
             "Reseau", 3, "dns,doh,reseau"),

            # Réseau - DHCP
            ("Problème de DHCP", "Le DHCP ne fonctionne pas", "Serveur DHCP hors service",
             "1- Renouveler l'IP\n2- Vérifier le serveur DHCP\n3- Configurer une IP fixe",
             "Le serveur DHCP est-il actif ?", "Reseau", 3, "dhcp,reseau"),
            ("IP non attribuée", "L'IP n'est pas attribuée", "Problème de DHCP",
             "1- Renouveler l'IP\n2- Vérifier le DHCP\n3- Configurer une IP fixe", "Que dit ipconfig ?", "Reseau", 3,
             "ip,dhcp,reseau"),
            ("Conflit d'IP", "Conflit d'adresse IP", "Deux périphériques avec la même IP",
             "1- Renouveler l'IP\n2- Configurer une IP fixe\n3- Vérifier le DHCP", "Quelle est l'IP ?", "Reseau", 3,
             "ip,conflit,reseau"),

            # Réseau - VPN
            ("Problème de VPN", "Le VPN ne se connecte pas", "Configuration incorrecte ou serveur HS",
             "1- Vérifier les identifiants\n2- Vérifier la configuration\n3- Changer de serveur VPN",
             "Quelle est l'erreur VPN ?", "Reseau", 4, "vpn,reseau"),
            ("VPN lent", "VPN très lent", "Bande passante limitée",
             "1- Changer de serveur\n2- Changer de protocole\n3- Vérifier la connexion", "Quelle est votre vitesse ?",
             "Reseau", 3, "vpn,lent,reseau"),
            ("VPN ne se connecte pas", "Le VPN ne se connecte pas", "Problème de configuration",
             "1- Vérifier les identifiants\n2- Vérifier le firewall\n3- Changer de protocole", "Quelle est l'erreur ?",
             "Reseau", 4, "vpn,connexion,reseau"),
            ("VPN bloque Internet", "Le VPN bloque l'accès Internet", "Problème de kill switch",
             "1- Désactiver le kill switch\n2- Changer de serveur\n3- Vérifier la configuration",
             "Internet fonctionne-t-il sans VPN ?", "Reseau", 3, "vpn,internet,reseau"),

            # Réseau - Routeur
            ("Routeur ne fonctionne pas", "Le routeur ne fonctionne pas", "Problème d'alimentation ou de configuration",
             "1- Redémarrer le routeur\n2- Vérifier l'alimentation\n3- Réinitialiser le routeur",
             "Les LEDs sont-elles allumées ?", "Reseau", 3, "routeur,reseau"),
            ("Routeur lent", "Le routeur est lent", "Problème de bande passante",
             "1- Redémarrer le routeur\n2- Vérifier les connexions\n3- Mettre à jour le firmware", "Depuis quand ?",
             "Reseau", 3, "routeur,lent,reseau"),
            ("Routeur WiFi faible", "Signal WiFi faible", "Position du routeur",
             "1- Déplacer le routeur\n2- Ajouter un répéteur\n3- Changer de canal", "Où est le routeur ?", "Reseau", 2,
             "routeur,wifi,faible,reseau"),
            ("Routeur surchauffe", "Le routeur surchauffe", "Problème de ventilation",
             "1- Ventiler le routeur\n2- Déplacer le routeur\n3- Contacter le FAI", "Le routeur est-il chaud ?",
             "Reseau", 3, "routeur,surchauffe,reseau"),
            ("Routeur firmware", "Firmware du routeur à mettre à jour", "Firmware obsolète",
             "1- Vérifier le firmware\n2- Télécharger le firmware\n3- Mettre à jour", "Quelle est la version ?",
             "Reseau", 3, "routeur,firmware,reseau"),

            # Réseau - Réseau d'entreprise
            ("Proxy ne fonctionne pas", "Le proxy ne fonctionne pas", "Configuration incorrecte",
             "1- Vérifier les paramètres\n2- Vérifier le proxy\n3- Contacter l'admin", "Utilisez-vous un proxy ?",
             "Reseau", 4, "proxy,reseau"),
            ("Réseau d'entreprise ne fonctionne pas", "Le réseau d'entreprise ne fonctionne pas", "Problème de VLAN",
             "1- Vérifier le VLAN\n2- Vérifier le DHCP\n3- Contacter l'admin", "Le réseau est-il allumé ?", "Reseau", 4,
             "entreprise,reseau"),
            ("Problème de VLAN", "Le VLAN ne fonctionne pas", "Configuration VLAN incorrecte",
             "1- Vérifier le VLAN\n2- Vérifier les ports\n3- Vérifier le trunk", "Quel est le VLAN ?", "Reseau", 4,
             "vlan,reseau"),
            ("Problème de NAT", "Le NAT ne fonctionne pas", "Configuration NAT incorrecte",
             "1- Vérifier le NAT\n2- Vérifier les ports\n3- Vérifier le routing", "Quel est le port ?", "Reseau", 4,
             "nat,reseau"),
            ("Problème de firewall d'entreprise", "Le firewall bloque tout", "Configuration du firewall",
             "1- Vérifier les règles\n2- Ajouter des règles\n3- Contacter l'admin", "Quelle application ?", "Reseau", 4,
             "firewall,entreprise,reseau"),

            # Réseau - Routage
            ("Problème de routage", "Le routage ne fonctionne pas", "Table de routage incorrecte",
             "1- Vérifier le routage\n2- Ajouter une route\n3- Vérifier le gateway", "Quelle est la route ?", "Reseau",
             4, "routage,reseau"),
            ("Gateway ne fonctionne pas", "Le gateway ne fonctionne pas", "Problème de gateway",
             "1- Vérifier le gateway\n2- Changer le gateway\n3- Vérifier le ping", "Le gateway est-il accessible ?",
             "Reseau", 4, "gateway,reseau"),
            ("Problème de static route", "La route statique ne fonctionne pas", "Configuration incorrecte",
             "1- Vérifier la route\n2- Ajouter la route\n3- Vérifier le réseau", "Quelle est la route ?", "Reseau", 4,
             "route,static,reseau"),
            ("Problème de policy routing", "Le policy routing ne fonctionne pas", "Configuration incorrecte",
             "1- Vérifier le policy\n2- Vérifier les règles\n3- Vérifier le routage", "Quel est le policy ?", "Reseau",
             4, "policy,routing,reseau"),

            # Réseau - Monitoring
            ("Ping ne fonctionne pas", "Le ping ne fonctionne pas", "Problème de réseau",
             "1- Vérifier le ping\n2- Vérifier le firewall\n3- Vérifier le routage", "Quelle est l'adresse ?", "Reseau",
             3, "ping,reseau"),
            ("Traceroute ne fonctionne pas", "Le traceroute ne fonctionne pas", "Problème de routage",
             "1- Vérifier le traceroute\n2- Vérifier le routage\n3- Vérifier le firewall", "Quelle est l'adresse ?",
             "Reseau", 3, "traceroute,reseau"),
            ("Problème de bandwidth", "Bande passante saturée", "Utilisation élevée",
             "1- Vérifier la bande passante\n2- Limiter les téléchargements\n3- Contacter le FAI",
             "Quelle est l'utilisation ?", "Reseau", 3, "bandwidth,reseau"),
            ("Problème de latency", "Latence élevée", "Problème de réseau",
             "1- Vérifier la latence\n2- Vérifier le routage\n3- Contacter le FAI", "Quelle est la latence ?", "Reseau",
             3, "latence,reseau"),
            ("Problème de packet loss", "Perte de paquets", "Problème de réseau",
             "1- Vérifier le packet loss\n2- Vérifier le câble\n3- Contacter le FAI", "Quel est le taux de perte ?",
             "Reseau", 3, "packet-loss,reseau"),
            ("Problème de MTU", "MTU incorrect", "Problème de MTU",
             "1- Vérifier le MTU\n2- Changer le MTU\n3- Vérifier le ping", "Quel est le MTU ?", "Reseau", 4,
             "mtu,reseau"),
            ("Problème de MSS", "MSS incorrect", "Problème de MSS",
             "1- Vérifier le MSS\n2- Changer le MSS\n3- Vérifier le ping", "Quel est le MSS ?", "Reseau", 4,
             "mss,reseau"),
            ("Problème de TCP window", "TCP window incorrect", "Problème de TCP",
             "1- Vérifier la fenêtre TCP\n2- Changer la fenêtre\n3- Vérifier le réseau", "Quelle est la fenêtre ?",
             "Reseau", 4, "tcp,window,reseau"),
            # Sécurité - Antivirus
            ("Virus détecté", "Antivirus a détecté un virus", "Malware ou fichier infecté",
             "1- Exécuter une analyse complète\n2- Mettre en quarantaine\n3- Supprimer le fichier",
             "Quel fichier est infecté ?", "Securite", 4, "virus,malware,securite"),
            ("Antivirus ne fonctionne pas", "L'antivirus ne fonctionne pas", "Antivirus désactivé",
             "1- Activer l'antivirus\n2- Mettre à jour\n3- Réinstaller", "Quel antivirus ?", "Securite", 3,
             "antivirus,securite"),
            ("Antivirus ne se met pas à jour", "L'antivirus ne se met pas à jour", "Problème de mise à jour",
             "1- Vérifier la connexion\n2- Télécharger manuellement\n3- Réinstaller", "Quelle est l'erreur ?",
             "Securite", 3, "antivirus,update,securite"),
            ("Faux positif antivirus", "L'antivirus détecte un faux positif", "Fichier légitime détecté",
             "1- Ajouter une exception\n2- Mettre à jour l'antivirus\n3- Contacter l'éditeur", "Quel fichier ?",
             "Securite", 3, "antivirus,faux-positif,securite"),
            ("Antivirus bloque tout", "L'antivirus bloque tout", "Configuration trop stricte",
             "1- Désactiver temporairement\n2- Ajouter des exceptions\n3- Changer de niveau", "Quelle application ?",
             "Securite", 3, "antivirus,bloque,securite"),

            # Sécurité - Malware
            ("Malware détecté", "Malware détecté sur le PC", "Malware",
             "1- Exécuter Malwarebytes\n2- Nettoyer le PC\n3- Réinstaller Windows", "Que détecte-t-il ?", "Securite", 4,
             "malware,securite"),
            ("Spyware détecté", "Spyware détecté", "Spyware",
             "1- Exécuter un scan\n2- Nettoyer le PC\n3- Changer les mots de passe", "Que détecte-t-il ?", "Securite",
             4, "spyware,securite"),
            ("Adware détecté", "Adware détecté", "Adware",
             "1- Exécuter un scan\n2- Nettoyer le PC\n3- Supprimer les extensions", "Que détecte-t-il ?", "Securite", 3,
             "adware,securite"),
            ("Trojan détecté", "Trojan détecté", "Trojan",
             "1- Exécuter un scan\n2- Mettre en quarantaine\n3- Nettoyer le PC", "Que détecte-t-il ?", "Securite", 5,
             "trojan,securite"),
            ("Rootkit détecté", "Rootkit détecté", "Rootkit",
             "1- Exécuter un scan\n2- Utiliser un outil spécialisé\n3- Réinstaller Windows", "Que détecte-t-il ?",
             "Securite", 5, "rootkit,securite"),

            # Sécurité - Ransomware
            ("Ransomware détecté", "Fichiers chiffrés par ransomware", "Ransomware",
             "1- Déconnecter le PC d'Internet\n2- Contacter un expert\n3- Utiliser un outil de décryptage",
             "Avez-vous une sauvegarde ?", "Securite", 5, "ransomware,securite"),
            ("Ransomware demande rançon", "Message de ransomware", "Ransomware",
             "1- Ne pas payer\n2- Contacter un expert\n3- Restaurer les sauvegardes", "Avez-vous une sauvegarde ?",
             "Securite", 5, "ransomware,securite"),
            ("Fichiers chiffrés", "Fichiers chiffrés sans raison", "Ransomware",
             "1- Déconnecter le PC\n2- Contacter un expert\n3- Utiliser un outil de décryptage",
             "Quel est l'extension ?", "Securite", 5, "chiffre,ransomware,securite"),

            # Sécurité - Phishing
            ("Phishing détecté", "Email suspect reçu", "Phishing",
             "1- Ne pas cliquer\n2- Signaler l'email\n3- Changer les mots de passe", "Avez-vous cliqué ?", "Securite",
             4, "phishing,securite"),
            ("Lien phishing", "Lien suspect reçu", "Phishing", "1- Ne pas cliquer\n2- Vérifier l'URL\n3- Signaler",
             "Avez-vous cliqué ?", "Securite", 4, "phishing,lien,securite"),
            ("Email phishing", "Email de phishing reçu", "Phishing",
             "1- Ne pas répondre\n2- Signaler l'email\n3- Vider la corbeille", "Avez-vous répondu ?", "Securite", 4,
             "phishing,email,securite"),
            ("SMS phishing", "SMS suspect reçu", "Phishing", "1- Ne pas cliquer\n2- Supprimer le SMS\n3- Signaler",
             "Avez-vous cliqué ?", "Securite", 4, "phishing,sms,securite"),

            # Sécurité - Pare-feu
            ("Pare-feu bloque tout", "Le pare-feu bloque tout", "Configuration trop restrictive",
             "1- Désactiver temporairement\n2- Ajouter des règles\n3- Vérifier les logs",
             "Quelle application est bloquée ?", "Securite", 3, "firewall,securite"),
            ("Pare-feu désactivé", "Le pare-feu est désactivé", "Pare-feu désactivé",
             "1- Activer le pare-feu\n2- Configurer le pare-feu\n3- Vérifier les règles", "Que dit l'erreur ?",
             "Securite", 3, "firewall,desactive,securite"),
            ("Règle de pare-feu", "Règle de pare-feu bloquante", "Règle incorrecte",
             "1- Vérifier les règles\n2- Ajouter une règle\n3- Supprimer la règle", "Quelle est la règle ?", "Securite",
             3, "firewall,regle,securite"),

            # Sécurité - Authentification
            ("Problème de mot de passe", "Mot de passe oublié", "Mot de passe perdu",
             "1- Utiliser la récupération\n2- Réinitialiser le mot de passe\n3- Contacter l'admin",
             "Avez-vous un email ?", "Securite", 3, "mot-de-passe,securite"),
            ("Problème de 2FA", "Le 2FA ne fonctionne pas", "Code 2FA incorrect",
             "1- Vérifier le code\n2- Utiliser les codes de secours\n3- Contacter le support",
             "Avez-vous les codes de secours ?", "Securite", 4, "2fa,securite"),
            ("Problème de MFA", "Le MFA ne fonctionne pas", "MFA incorrect",
             "1- Vérifier le code\n2- Utiliser les codes de secours\n3- Contacter le support",
             "Avez-vous les codes de secours ?", "Securite", 4, "mfa,securite"),
            ("Compte piraté", "Compte piraté", "Mot de passe volé",
             "1- Changer le mot de passe\n2- Activer 2FA\n3- Vérifier les connexions", "Le compte est-il actif ?",
             "Securite", 5, "pirate,securite"),
            ("Compte verrouillé", "Compte verrouillé", "Trop de tentatives",
             "1- Attendre\n2- Contacter l'admin\n3- Réinitialiser", "Quelle est l'erreur ?", "Securite", 3,
             "verrouille,securite"),

            # Sécurité - Chiffrement
            ("Problème de chiffrement", "Chiffrement ne fonctionne pas", "Problème de clé",
             "1- Vérifier la clé\n2- Réinstaller\n3- Contacter le support", "Quelle est l'erreur ?", "Securite", 4,
             "chiffrement,securite"),
            ("Problème de PGP", "PGP ne fonctionne pas", "Problème de PGP",
             "1- Vérifier la clé\n2- Réinstaller\n3- Générer une nouvelle clé", "Quelle est l'erreur ?", "Securite", 4,
             "pgp,securite"),
            ("Problème de GPG", "GPG ne fonctionne pas", "Problème de GPG",
             "1- Vérifier la clé\n2- Réinstaller\n3- Générer une nouvelle clé", "Quelle est l'erreur ?", "Securite", 4,
             "gpg,securite"),
            ("Problème de certificat", "Certificat invalide", "Certificat expiré",
             "1- Vérifier la date\n2- Renouveler le certificat\n3- Contacter l'autorité", "Quelle est la date ?",
             "Securite", 4, "certificat,securite"),
            ("Problème de SSL", "SSL ne fonctionne pas", "Certificat SSL invalide",
             "1- Vérifier le certificat\n2- Renouveler le certificat\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "ssl,securite"),

            # Sécurité - Sauvegarde
            ("Sauvegarde ne fonctionne pas", "La sauvegarde échoue", "Problème de sauvegarde",
             "1- Vérifier l'espace\n2- Vérifier les fichiers\n3- Réessayer", "Quelle est l'erreur ?", "Securite", 3,
             "sauvegarde,securite"),
            ("Sauvegarde corrompue", "Sauvegarde corrompue", "Problème de sauvegarde",
             "1- Vérifier les fichiers\n2- Restaurer\n3- Recréer la sauvegarde", "Quel est le fichier ?", "Securite", 4,
             "sauvegarde,corrompue,securite"),
            ("Restauration échoue", "La restauration échoue", "Problème de restauration",
             "1- Vérifier les fichiers\n2- Utiliser un autre outil\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "restauration,securite"),
            ("Problème de backup cloud", "Le backup cloud échoue", "Problème de cloud",
             "1- Vérifier la connexion\n2- Vérifier l'espace\n3- Réessayer", "Quelle est l'erreur ?", "Securite", 3,
             "backup,cloud,securite"),
            ("Problème de backup local", "Le backup local échoue", "Problème de disque",
             "1- Vérifier le disque\n2- Vérifier l'espace\n3- Réessayer", "Quelle est l'erreur ?", "Securite", 3,
             "backup,local,securite"),

            # Sécurité - Autre
            ("Problème de sécurité Windows", "Problème de sécurité Windows", "Configuration de sécurité",
             "1- Vérifier Windows Update\n2- Vérifier Defender\n3- Vérifier le pare-feu", "Que dit l'erreur ?",
             "Securite", 3, "securite,windows"),
            ("Problème de sécurité Linux", "Problème de sécurité Linux", "Configuration de sécurité",
             "1- Vérifier les mises à jour\n2- Vérifier SELinux\n3- Vérifier le pare-feu", "Que dit l'erreur ?",
             "Securite", 3, "securite,linux"),
            ("Problème de sécurité Mac", "Problème de sécurité Mac", "Configuration de sécurité",
             "1- Vérifier les mises à jour\n2- Vérifier Gatekeeper\n3- Vérifier le pare-feu", "Que dit l'erreur ?",
             "Securite", 3, "securite,mac"),
            ("Problème de sécurité réseau", "Problème de sécurité réseau", "Configuration de sécurité",
             "1- Vérifier le pare-feu\n2- Vérifier le VPN\n3- Vérifier les ports", "Que dit l'erreur ?", "Securite", 3,
             "securite,reseau"),
            ("Problème de sécurité cloud", "Problème de sécurité cloud", "Configuration de sécurité",
             "1- Vérifier les permissions\n2- Vérifier les accès\n3- Contacter le support", "Que dit l'erreur ?",
             "Securite", 3, "securite,cloud"),
            # Matériel - CPU
            ("CPU surchauffe", "Le CPU chauffe trop", "Ventilateur bloqué ou pâte thermique sèche",
             "1- Nettoyer le ventilateur\n2- Changer la pâte thermique\n3- Vérifier la ventilation",
             "Quelle température ?", "Materiel", 3, "cpu,surchauffe,materiel"),
            ("CPU 100%", "Le CPU est à 100%", "Processus en arrière-plan",
             "1- Ouvrir le gestionnaire de tâches\n2- Identifier le processus\n3- Tuer le processus",
             "Quel processus ?", "Materiel", 2, "cpu,100%,materiel"),
            ("CPU ne fonctionne pas", "Le CPU ne fonctionne pas", "CPU défectueux",
             "1- Vérifier l'alimentation\n2- Vérifier le socket\n3- Contacter un réparateur", "Le PC démarre-t-il ?",
             "Materiel", 5, "cpu,defectueux,materiel"),
            ("CPU underclock", "CPU sous-utilisé", "Paramètres BIOS",
             "1- Vérifier le BIOS\n2- Activer le turbo\n3- Vérifier l'alimentation", "Quelle est la fréquence ?",
             "Materiel", 3, "cpu,underclock,materiel"),
            ("CPU overclock", "CPU overclocké", "Paramètres BIOS",
             "1- Réinitialiser le BIOS\n2- Réduire l'overclock\n3- Vérifier la température",
             "Quelle est la fréquence ?", "Materiel", 4, "cpu,overclock,materiel"),
            ("Problème de socket CPU", "Problème de socket CPU", "Socket endommagé",
             "1- Vérifier les pins\n2- Vérifier le CPU\n3- Contacter un réparateur", "Le PC démarre-t-il ?", "Materiel",
             5, "cpu,socket,materiel"),
            ("Problème de montage CPU", "CPU mal monté", "Problème d'installation",
             "1- Vérifier le montage\n2- Remonter le CPU\n3- Vérifier le socket", "Le PC démarre-t-il ?", "Materiel", 4,
             "cpu,montage,materiel"),

            # Matériel - RAM
            ("RAM insuffisante", "Pas assez de RAM", "Mémoire insuffisante",
             "1- Fermer les applications\n2- Ajouter de la RAM\n3- Augmenter la swap", "Quelle quantité de RAM ?",
             "Materiel", 2, "ram,insuffisant,materiel"),
            ("RAM defectueuse", "RAM défectueuse", "Barrette RAM HS",
             "1- Tester avec MemTest86\n2- Retirer les barrettes une par une\n3- Remplacer la RAM",
             "Quel est le message d'erreur ?", "Materiel", 4, "ram,defectueux,materiel"),
            ("RAM non reconnue", "La RAM n'est pas reconnue", "Problème de barrette",
             "1- Vérifier les barrettes\n2- Nettoyer les contacts\n3- Vérifier le BIOS", "La RAM est-elle détectée ?",
             "Materiel", 3, "ram,non-reconnue,materiel"),
            ("RAM mal installée", "RAM mal installée", "Problème d'installation",
             "1- Vérifier les barrettes\n2- Réinstaller les barrettes\n3- Vérifier le slot", "Le PC démarre-t-il ?",
             "Materiel", 3, "ram,installation,materiel"),
            ("Problème de slot RAM", "Slot RAM défectueux", "Slot endommagé",
             "1- Tester un autre slot\n2- Vérifier les contacts\n3- Contacter un réparateur",
             "La RAM est-elle détectée ?", "Materiel", 4, "ram,slot,materiel"),
            ("RAM speed", "RAM trop lente", "Fréquence incorrecte",
             "1- Vérifier le BIOS\n2- Activer XMP\n3- Vérifier la fréquence", "Quelle est la fréquence ?", "Materiel",
             3, "ram,vitesse,materiel"),

            # Matériel - Disque dur / SSD
            ("Disque dur ne fonctionne pas", "Le disque dur ne fonctionne pas", "Disque dur HS",
             "1- Vérifier le câble\n2- Utiliser un outil de récupération\n3- Remplacer le disque",
             "Le disque fait-il du bruit ?", "Materiel", 4, "disque,defectueux,materiel"),
            ("SSD ne fonctionne pas", "Le SSD ne fonctionne pas", "SSD HS",
             "1- Vérifier le câble\n2- Vérifier le BIOS\n3- Remplacer le SSD", "Le SSD est-il reconnu ?", "Materiel", 4,
             "ssd,defectueux,materiel"),
            ("Disque dur lent", "Le disque dur est lent", "Disque fragmenté",
             "1- Défragmenter\n2- Nettoyer le disque\n3- Remplacer par un SSD", "Quelle est la vitesse ?", "Materiel",
             2, "disque,lent,materiel"),
            ("Disque dur plein", "Le disque dur est plein", "Espace insuffisant",
             "1- Nettoyer le disque\n2- Supprimer des fichiers\n3- Ajouter un disque", "Quelle est la taille ?",
             "Materiel", 2, "disque,plein,materiel"),
            ("SSD lent", "Le SSD est lent", "SSD plein", "1- Vérifier le TRIM\n2- Nettoyer le SSD\n3- Remplacer le SSD",
             "Quelle est la vitesse ?", "Materiel", 3, "ssd,lent,materiel"),
            ("Disque dur ne démarre pas", "Le disque dur ne démarre pas", "Disque HS",
             "1- Vérifier l'alimentation\n2- Vérifier le câble\n3- Contacter un réparateur",
             "Le disque fait-il du bruit ?", "Materiel", 4, "disque,demarrage,materiel"),
            ("Problème de partition", "Problème de partition", "Table de partitions corrompue",
             "1- Utiliser un outil de récupération\n2- Recréer la table\n3- Formater", "Quelle est l'erreur ?",
             "Materiel", 4, "partition,materiel"),
            ("Problème de MBR", "MBR corrompu", "MBR endommagé",
             "1- Réparer le MBR\n2- Utiliser un outil de récupération\n3- Réinstaller", "Quelle est l'erreur ?",
             "Materiel", 4, "mbr,materiel"),
            ("Problème de GPT", "GPT corrompu", "GPT endommagé",
             "1- Réparer le GPT\n2- Utiliser un outil de récupération\n3- Réinstaller", "Quelle est l'erreur ?",
             "Materiel", 4, "gpt,materiel"),

            # Matériel - Carte mère
            ("Carte mère ne fonctionne pas", "La carte mère ne fonctionne pas", "Carte mère HS",
             "1- Vérifier l'alimentation\n2- Vérifier les composants\n3- Contacter un réparateur",
             "Le PC démarre-t-il ?", "Materiel", 5, "carte-mere,defectueux,materiel"),
            ("Problème de BIOS", "Le BIOS ne fonctionne pas", "BIOS corrompu",
             "1- Réinitialiser le BIOS\n2- Mettre à jour le BIOS\n3- Contacter le fabricant", "Quelle est l'erreur ?",
             "Materiel", 4, "bios,materiel"),
            ("Problème de CMOS", "Le CMOS ne fonctionne pas", "Pile CMOS vide",
             "1- Remplacer la pile\n2- Réinitialiser le CMOS\n3- Vérifier le BIOS", "Que dit l'erreur ?", "Materiel", 3,
             "cmos,materiel"),
            ("Problème de ports USB", "Les ports USB ne fonctionnent pas", "Problème de carte mère",
             "1- Vérifier les ports\n2- Mettre à jour les pilotes\n3- Contacter un réparateur",
             "Les ports sont-ils reconnus ?", "Materiel", 3, "usb,materiel"),
            ("Problème de ports SATA", "Les ports SATA ne fonctionnent pas", "Problème de carte mère",
             "1- Vérifier les câbles\n2- Vérifier le BIOS\n3- Contacter un réparateur",
             "Les disques sont-ils reconnus ?", "Materiel", 4, "sata,materiel"),
            ("Problème de PCIe", "Les ports PCIe ne fonctionnent pas", "Problème de carte mère",
             "1- Vérifier les cartes\n2- Vérifier le BIOS\n3- Contacter un réparateur",
             "Les cartes sont-elles reconnues ?", "Materiel", 4, "pcie,materiel"),

            # Matériel - Alimentation
            ("Alimentation ne fonctionne pas", "L'alimentation ne fonctionne pas", "Alimentation HS",
             "1- Vérifier le câble\n2- Tester une autre prise\n3- Remplacer l'alimentation", "Le PC s'allume-t-il ?",
             "Materiel", 4, "alimentation,defectueux,materiel"),
            ("Alimentation insuffisante", "Alimentation pas assez puissante", "Alimentation sous-dimensionnée",
             "1- Vérifier la puissance\n2- Ajouter une alimentation\n3- Remplacer l'alimentation",
             "Quelle est la puissance ?", "Materiel", 3, "alimentation,insuffisant,materiel"),
            ("Problème de câble alimentation", "Câble d'alimentation défectueux", "Câble HS",
             "1- Vérifier le câble\n2- Remplacer le câble\n3- Tester une autre prise", "Le PC s'allume-t-il ?",
             "Materiel", 3, "alimentation,cable,materiel"),
            ("Alimentation bruyante", "Alimentation fait du bruit", "Ventilateur d'alimentation",
             "1- Nettoyer le ventilateur\n2- Remplacer le ventilateur\n3- Remplacer l'alimentation",
             "Quel type de bruit ?", "Materiel", 3, "alimentation,bruit,materiel"),
            ("Alimentation surchauffe", "Alimentation chauffe trop", "Problème de ventilation",
             "1- Ventiler l'alimentation\n2- Nettoyer le ventilateur\n3- Remplacer l'alimentation",
             "Quelle est la température ?", "Materiel", 3, "alimentation,surchauffe,materiel"),

            # Matériel - Périphériques
            ("Souris ne fonctionne pas", "La souris ne fonctionne pas", "Problème de souris",
             "1- Vérifier le câble\n2- Vérifier le Bluetooth\n3- Réinstaller le pilote",
             "La souris est-elle connectée ?", "Materiel", 2, "souris,materiel"),
            ("Clavier ne fonctionne pas", "Le clavier ne fonctionne pas", "Problème de clavier",
             "1- Vérifier le câble\n2- Vérifier le Bluetooth\n3- Réinstaller le pilote", "Le clavier est-il connecté ?",
             "Materiel", 2, "clavier,materiel"),
            ("Écran ne fonctionne pas", "L'écran ne fonctionne pas", "Problème d'écran",
             "1- Vérifier le câble\n2- Tester un autre écran\n3- Réinstaller le pilote", "L'écran s'allume-t-il ?",
             "Materiel", 3, "ecran,materiel"),
            ("Imprimante ne fonctionne pas", "L'imprimante ne fonctionne pas", "Problème d'imprimante",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier l'encre", "L'imprimante est-elle allumée ?",
             "Materiel", 3, "imprimante,materiel"),
            ("Scanner ne fonctionne pas", "Le scanner ne fonctionne pas", "Problème de scanner",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier les permissions",
             "Le scanner est-il allumé ?", "Materiel", 3, "scanner,materiel"),
            ("Webcam ne fonctionne pas", "La webcam ne fonctionne pas", "Problème de webcam",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier les permissions",
             "La webcam est-elle allumée ?", "Materiel", 3, "webcam,materiel"),
            ("Micro ne fonctionne pas", "Le micro ne fonctionne pas", "Problème de micro",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier les permissions", "Le micro est-il allumé ?",
             "Materiel", 3, "micro,materiel"),
            ("Haut-parleurs ne fonctionnent pas", "Les haut-parleurs ne fonctionnent pas", "Problème audio",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier le volume", "Le son est-il activé ?",
             "Materiel", 2, "audio,materiel"),

            # Matériel - Refroidissement
            ("Ventilateur ne fonctionne pas", "Le ventilateur ne fonctionne pas", "Ventilateur HS",
             "1- Nettoyer le ventilateur\n2- Remplacer le ventilateur\n3- Vérifier l'alimentation",
             "Le ventilateur tourne-t-il ?", "Materiel", 3, "ventilateur,materiel"),
            ("PC surchauffe", "Le PC surchauffe", "Problème de ventilation",
             "1- Nettoyer les ventilateurs\n2- Vérifier la pâte thermique\n3- Ajouter un ventilateur",
             "Quelle est la température ?", "Materiel", 3, "surchauffe,materiel"),
            ("Ventilateur bruyant", "Ventilateur fait du bruit", "Ventilateur usé",
             "1- Nettoyer le ventilateur\n2- Remplacer le ventilateur\n3- Vérifier les roulements",
             "Quel type de bruit ?", "Materiel", 3, "ventilateur,bruit,materiel"),
            ("Problème de watercooling", "Watercooling ne fonctionne pas", "Problème de watercooling",
             "1- Vérifier les tubes\n2- Vérifier la pompe\n3- Contacter un réparateur",
             "Le watercooling fonctionne-t-il ?", "Materiel", 4, "watercooling,materiel"),
            ("Problème de pâte thermique", "Pâte thermique sèche", "Pâte thermique à changer",
             "1- Nettoyer le CPU\n2- Appliquer de la pâte thermique\n3- Remonter le CPU", "Quelle est la température ?",
             "Materiel", 3, "pate-thermique,materiel"),
            # Bureautique - Office
            ("Word ne s'ouvre pas", "Word ne s'ouvre pas", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Réparer Office\n3- Réinstaller Office", "Quelle version d'Office ?",
             "Bureautique", 3, "word,office"),
            ("Word se bloque", "Word se bloque", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Désactiver les add-ins\n3- Réparer Office", "Quelle est l'erreur ?",
             "Bureautique", 3, "word,bloque,office"),
            ("Word fichier corrompu", "Fichier Word corrompu", "Problème de fichier",
             "1- Utiliser la récupération\n2- Ouvrir avec WordPad\n3- Utiliser un outil de récupération",
             "Quel est le fichier ?", "Bureautique", 4, "word,corrompu,office"),
            ("Word ne sauvegarde pas", "Word ne sauvegarde pas", "Problème de sauvegarde",
             "1- Vérifier le disque\n2- Vérifier les permissions\n3- Réparer Office", "Que dit l'erreur ?",
             "Bureautique", 3, "word,sauvegarde,office"),
            ("Word mise en page", "Mise en page Word décalée", "Problème de mise en page",
             "1- Vérifier les marges\n2- Vérifier les sauts de page\n3- Réinitialiser", "Quelle est l'erreur ?",
             "Bureautique", 2, "word,mise-en-page,office"),

            # Bureautique - Excel
            ("Excel ne s'ouvre pas", "Excel ne s'ouvre pas", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Réparer Office\n3- Réinstaller Office", "Quelle version d'Office ?",
             "Bureautique", 3, "excel,office"),
            ("Excel se bloque", "Excel se bloque", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Désactiver les add-ins\n3- Réparer Office", "Quelle est l'erreur ?",
             "Bureautique", 3, "excel,bloque,office"),
            ("Excel fichier corrompu", "Fichier Excel corrompu", "Problème de fichier",
             "1- Utiliser la récupération\n2- Ouvrir avec OpenOffice\n3- Utiliser un outil de récupération",
             "Quel est le fichier ?", "Bureautique", 4, "excel,corrompu,office"),
            ("Excel ne calcule pas", "Excel ne calcule pas", "Problème de calcul",
             "1- Vérifier les formules\n2- Activer le calcul automatique\n3- Vérifier les références",
             "Que dit l'erreur ?", "Bureautique", 3, "excel,calcul,office"),
            ("Excel macro ne fonctionne pas", "Les macros Excel ne fonctionnent pas", "Problème de sécurité",
             "1- Activer les macros\n2- Vérifier le niveau de sécurité\n3- Réparer Office", "Que dit l'erreur ?",
             "Bureautique", 3, "excel,macro,office"),
            ("Excel graphique", "Problème de graphique Excel", "Problème de graphique",
             "1- Vérifier les données\n2- Recréer le graphique\n3- Vérifier les types", "Quel est le graphique ?",
             "Bureautique", 3, "excel,graphique,office"),

            # Bureautique - PowerPoint
            ("PowerPoint ne s'ouvre pas", "PowerPoint ne s'ouvre pas", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Réparer Office\n3- Réinstaller Office", "Quelle version d'Office ?",
             "Bureautique", 3, "powerpoint,office"),
            ("PowerPoint se bloque", "PowerPoint se bloque", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Désactiver les add-ins\n3- Réparer Office", "Quelle est l'erreur ?",
             "Bureautique", 3, "powerpoint,bloque,office"),
            ("PowerPoint fichier corrompu", "Fichier PowerPoint corrompu", "Problème de fichier",
             "1- Utiliser la récupération\n2- Ouvrir avec OpenOffice\n3- Utiliser un outil de récupération",
             "Quel est le fichier ?", "Bureautique", 4, "powerpoint,corrompu,office"),
            ("PowerPoint ne s'affiche pas", "PowerPoint ne s'affiche pas", "Problème d'affichage",
             "1- Vérifier les paramètres\n2- Vérifier le pilote\n3- Réparer Office", "Que dit l'erreur ?",
             "Bureautique", 3, "powerpoint,affichage,office"),
            ("PowerPoint animation", "Problème d'animation PowerPoint", "Problème d'animation",
             "1- Vérifier les animations\n2- Réinitialiser\n3- Vérifier les transitions", "Quel est le problème ?",
             "Bureautique", 3, "powerpoint,animation,office"),

            # Bureautique - Outlook
            ("Outlook ne s'ouvre pas", "Outlook ne s'ouvre pas", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Réparer Office\n3- Réinstaller Office", "Quelle version d'Office ?",
             "Bureautique", 3, "outlook,office"),
            ("Outlook se bloque", "Outlook se bloque", "Problème d'Office",
             "1- Ouvrir en mode sans échec\n2- Désactiver les add-ins\n3- Réparer Office", "Quelle est l'erreur ?",
             "Bureautique", 3, "outlook,bloque,office"),
            ("Outlook ne reçoit pas d'emails", "Outlook ne reçoit pas d'emails", "Problème de configuration",
             "1- Vérifier le serveur\n2- Vérifier le compte\n3- Réparer Outlook", "Quelle est l'erreur ?",
             "Bureautique", 3, "outlook,reception,office"),
            ("Outlook ne peut pas envoyer", "Outlook ne peut pas envoyer", "Problème de configuration",
             "1- Vérifier le serveur\n2- Vérifier le compte\n3- Réparer Outlook", "Quelle est l'erreur ?",
             "Bureautique", 3, "outlook,envoi,office"),
            ("Outlook fichier PST corrompu", "Fichier PST corrompu", "Problème de fichier",
             "1- Utiliser ScanPST\n2- Réparer le fichier\n3- Recréer le fichier", "Quel est le fichier ?",
             "Bureautique", 4, "outlook,pst,corrompu,office"),
            ("Outlook signature", "Signature Outlook ne fonctionne pas", "Problème de signature",
             "1- Vérifier la signature\n2- Recréer la signature\n3- Vérifier les paramètres", "Quelle est l'erreur ?",
             "Bureautique", 2, "outlook,signature,office"),
            ("Outlook synchronisation", "Problème de synchronisation Outlook", "Problème de synchronisation",
             "1- Vérifier la connexion\n2- Réparer Outlook\n3- Recréer le compte", "Quelle est l'erreur ?",
             "Bureautique", 3, "outlook,synchronisation,office"),

            # Bureautique - Teams
            ("Teams ne s'ouvre pas", "Teams ne s'ouvre pas", "Problème de Teams",
             "1- Vider le cache\n2- Réinstaller Teams\n3- Vérifier la connexion", "Quelle est l'erreur ?",
             "Bureautique", 3, "teams,office"),
            ("Teams se bloque", "Teams se bloque", "Problème de Teams",
             "1- Vider le cache\n2- Réinstaller Teams\n3- Vérifier la connexion", "Quelle est l'erreur ?",
             "Bureautique", 3, "teams,bloque,office"),
            ("Teams ne se connecte pas", "Teams ne se connecte pas", "Problème de connexion",
             "1- Vérifier la connexion\n2- Vérifier le compte\n3- Réinstaller Teams", "Quelle est l'erreur ?",
             "Bureautique", 3, "teams,connexion,office"),
            ("Teams micro", "Le micro ne fonctionne pas dans Teams", "Problème de micro",
             "1- Vérifier le micro\n2- Vérifier les permissions\n3- Réinstaller Teams", "Le micro est-il reconnu ?",
             "Bureautique", 3, "teams,micro,office"),
            ("Teams caméra", "La caméra ne fonctionne pas dans Teams", "Problème de caméra",
             "1- Vérifier la caméra\n2- Vérifier les permissions\n3- Réinstaller Teams",
             "La caméra est-elle reconnue ?", "Bureautique", 3, "teams,camera,office"),
            ("Teams partage d'écran", "Le partage d'écran ne fonctionne pas", "Problème de partage",
             "1- Vérifier les permissions\n2- Vérifier le pilote\n3- Réinstaller Teams", "Que dit l'erreur ?",
             "Bureautique", 3, "teams,partage,office"),

            # Bureautique - OneDrive
            ("OneDrive ne synchronise pas", "OneDrive ne synchronise pas", "Problème de synchronisation",
             "1- Vider le cache\n2- Réinitialiser OneDrive\n3- Vérifier le stockage", "Quelle est l'erreur ?",
             "Bureautique", 3, "onedrive,synchronisation,office"),
            ("OneDrive ne se connecte pas", "OneDrive ne se connecte pas", "Problème de connexion",
             "1- Vérifier la connexion\n2- Vérifier le compte\n3- Réinstaller OneDrive", "Quelle est l'erreur ?",
             "Bureautique", 3, "onedrive,connexion,office"),
            ("OneDrive fichier en conflit", "Fichier OneDrive en conflit", "Problème de conflit",
             "1- Résoudre le conflit\n2- Choisir la version\n3- Synchroniser à nouveau", "Quel est le fichier ?",
             "Bureautique", 3, "onedrive,conflit,office"),
            ("OneDrive espace plein", "Espace OneDrive plein", "Espace insuffisant",
             "1- Supprimer des fichiers\n2- Vider la corbeille\n3- Ajouter de l'espace", "Quelle est la taille ?",
             "Bureautique", 2, "onedrive,plein,office"),
            ("OneDrive fichier supprimé", "Fichier OneDrive supprimé", "Problème de suppression",
             "1- Vérifier la corbeille\n2- Restaurer le fichier\n3- Contacter le support", "Quel est le fichier ?",
             "Bureautique", 3, "onedrive,supprime,office"),

            # Bureautique - SharePoint
            ("SharePoint ne s'ouvre pas", "SharePoint ne s'ouvre pas", "Problème de SharePoint",
             "1- Vérifier la connexion\n2- Vérifier les permissions\n3- Contacter l'admin", "Quelle est l'erreur ?",
             "Bureautique", 3, "sharepoint,office"),
            ("SharePoint fichier", "Problème de fichier SharePoint", "Problème de fichier",
             "1- Vérifier le fichier\n2- Vérifier les permissions\n3- Contacter l'admin", "Quel est le fichier ?",
             "Bureautique", 3, "sharepoint,fichier,office"),
            ("SharePoint synchronisation", "Problème de synchronisation SharePoint", "Problème de synchronisation",
             "1- Vérifier la connexion\n2- Réinitialiser\n3- Contacter l'admin", "Quelle est l'erreur ?", "Bureautique",
             3, "sharepoint,synchronisation,office"),

            # Bureautique - Général
            ("Problème d'activation Office", "Office ne s'active pas", "Problème de licence",
             "1- Vérifier la licence\n2- Activer manuellement\n3- Contacter le support", "Quelle est l'erreur ?",
             "Bureautique", 3, "office,activation"),
            ("Problème de licence Office", "Licence Office invalide", "Problème de licence",
             "1- Vérifier la licence\n2- Réactiver\n3- Contacter le support", "Quelle est l'erreur ?", "Bureautique", 3,
             "office,licence"),
            ("Problème d'installation Office", "Office ne s'installe pas", "Problème d'installation",
             "1- Vérifier l'espace\n2- Vider le cache\n3- Réessayer", "Quelle est l'erreur ?", "Bureautique", 3,
             "office,installation"),
            ("Problème de mise à jour Office", "Office ne se met pas à jour", "Problème de mise à jour",
             "1- Vérifier la connexion\n2- Télécharger manuellement\n3- Réparer Office", "Quelle est l'erreur ?",
             "Bureautique", 3, "office,update"),
            ("Problème de réparation Office", "Office ne se répare pas", "Problème de réparation",
             "1- Vérifier l'installation\n2- Utiliser l'outil de réparation\n3- Réinstaller", "Quelle est l'erreur ?",
             "Bureautique", 3, "office,reparation"),
            ("Problème de désinstallation Office", "Office ne se désinstalle pas", "Problème de désinstallation",
             "1- Utiliser l'outil de désinstallation\n2- Supprimer manuellement\n3- Contacter le support",
             "Quelle est l'erreur ?", "Bureautique", 3, "office,desinstallation"),
            # Développement - Python
            ("Python ne s'installe pas", "Python ne s'installe pas", "Problème d'installation",
             "1- Vérifier l'espace\n2- Télécharger la version correcte\n3- Installer manuellement",
             "Quelle version de Python ?", "Dev", 3, "python,installation"),
            ("Python ne démarre pas", "Python ne démarre pas", "Problème d'environnement",
             "1- Vérifier les variables d'environnement\n2- Réinstaller Python\n3- Vérifier le PATH",
             "Que dit l'erreur ?", "Dev", 3, "python,demarrage"),
            ("Python ModuleNotFoundError", "Module Python manquant", "Module non installé",
             "1- Installer le module\n2- Vérifier les versions\n3- Vérifier l'environnement", "Quel module ?", "Dev", 3,
             "python,module"),
            ("Python syntax error", "Erreur de syntaxe Python", "Problème de syntaxe",
             "1- Vérifier la syntaxe\n2- Utiliser un linter\n3- Corriger le code", "Quelle est l'erreur ?", "Dev", 2,
             "python,syntaxe"),
            ("Python import error", "Erreur d'importation Python", "Problème d'import",
             "1- Vérifier le module\n2- Vérifier le chemin\n3- Vérifier l'environnement", "Quel module ?", "Dev", 3,
             "python,import"),
            ("Python version incompatibilité", "Version Python incompatible", "Problème de version",
             "1- Utiliser la bonne version\n2- Utiliser venv\n3- Mettre à jour", "Quelle version ?", "Dev", 3,
             "python,version"),
            ("Python pip ne fonctionne pas", "Pip ne fonctionne pas", "Problème de pip",
             "1- Mettre à jour pip\n2- Réinstaller pip\n3- Vérifier l'environnement", "Que dit l'erreur ?", "Dev", 3,
             "python,pip"),
            ("Python virtualenv", "Problème d'environnement virtuel", "Problème de venv",
             "1- Créer un nouvel environnement\n2- Vérifier l'activation\n3- Réinstaller", "Quelle est l'erreur ?",
             "Dev", 3, "python,venv"),
            ("Python pyenv", "Problème de pyenv", "Problème de pyenv",
             "1- Vérifier pyenv\n2- Installer la version\n3- Définir la version", "Quelle est l'erreur ?", "Dev", 3,
             "python,pyenv"),

            # Développement - Java
            ("Java ne s'installe pas", "Java ne s'installe pas", "Problème d'installation",
             "1- Vérifier l'espace\n2- Télécharger la version correcte\n3- Installer manuellement",
             "Quelle version de Java ?", "Dev", 3, "java,installation"),
            ("Java ne démarre pas", "Java ne démarre pas", "Problème d'environnement",
             "1- Vérifier les variables d'environnement\n2- Réinstaller Java\n3- Vérifier le PATH",
             "Que dit l'erreur ?", "Dev", 3, "java,demarrage"),
            ("Java class not found", "Classe Java non trouvée", "Problème de classpath",
             "1- Vérifier le classpath\n2- Vérifier les jar\n3- Compiler", "Quelle classe ?", "Dev", 3, "java,class"),
            ("Java version incompatible", "Version Java incompatible", "Problème de version",
             "1- Utiliser la bonne version\n2- Mettre à jour\n3- Changer la version", "Quelle version ?", "Dev", 3,
             "java,version"),
            ("Java memory error", "Erreur de mémoire Java", "Mémoire insuffisante",
             "1- Augmenter la mémoire\n2- Vérifier le code\n3- Optimiser", "Quelle est l'erreur ?", "Dev", 3,
             "java,memoire"),
            ("Java Maven", "Problème de Maven", "Problème de Maven",
             "1- Vérifier le pom.xml\n2- Nettoyer le projet\n3- Mettre à jour les dépendances", "Quelle est l'erreur ?",
             "Dev", 3, "java,maven"),
            ("Java Gradle", "Problème de Gradle", "Problème de Gradle",
             "1- Vérifier le build.gradle\n2- Nettoyer le projet\n3- Mettre à jour les dépendances",
             "Quelle est l'erreur ?", "Dev", 3, "java,gradle"),

            # Développement - Git
            ("Git ne fonctionne pas", "Git ne fonctionne pas", "Problème de Git",
             "1- Vérifier l'installation\n2- Vérifier les variables d'environnement\n3- Réinstaller",
             "Que dit l'erreur ?", "Dev", 3, "git"),
            ("Git clone ne fonctionne pas", "Git clone échoue", "Problème de connexion",
             "1- Vérifier l'URL\n2- Vérifier le SSH\n3- Vérifier le HTTPS", "Quelle est l'erreur ?", "Dev", 3,
             "git,clone"),
            ("Git push échoue", "Git push échoue", "Problème de permission",
             "1- Vérifier les droits\n2- Vérifier le SSH\n3- Vérifier le HTTPS", "Quelle est l'erreur ?", "Dev", 3,
             "git,push"),
            ("Git pull échoue", "Git pull échoue", "Problème de conflit",
             "1- Résoudre les conflits\n2- Stash les changements\n3- Forcer le pull", "Quelle est l'erreur ?", "Dev", 3,
             "git,pull"),
            ("Git merge conflict", "Conflit de merge Git", "Problème de conflit",
             "1- Résoudre les conflits\n2- Abort le merge\n3- Utiliser un outil", "Quel fichier ?", "Dev", 3,
             "git,merge,conflit"),
            ("Git rebase", "Problème de rebase Git", "Problème de rebase",
             "1- Abort le rebase\n2- Résoudre les conflits\n3- Continuer", "Quelle est l'erreur ?", "Dev", 3,
             "git,rebase"),
            ("Git SSH key", "Problème de clé SSH Git", "Problème de clé SSH",
             "1- Générer une clé\n2- Ajouter la clé\n3- Vérifier les permissions", "Quelle est l'erreur ?", "Dev", 3,
             "git,ssh,cle"),

            # Développement - VS Code
            ("VS Code ne s'ouvre pas", "VS Code ne s'ouvre pas", "Problème de VS Code",
             "1- Vider le cache\n2- Réinstaller VS Code\n3- Vérifier les paramètres", "Quelle est l'erreur ?", "Dev", 3,
             "vscode"),
            ("VS Code ne compile pas", "VS Code ne compile pas", "Problème de compilation",
             "1- Vérifier le projet\n2- Vérifier les extensions\n3- Réinstaller", "Quelle est l'erreur ?", "Dev", 3,
             "vscode,compilation"),
            ("VS Code extension", "Problème d'extension VS Code", "Extension défectueuse",
             "1- Désactiver l'extension\n2- Supprimer l'extension\n3- Réinstaller l'extension", "Quelle extension ?",
             "Dev", 3, "vscode,extension"),
            ("VS Code debug", "Problème de debug VS Code", "Problème de debug",
             "1- Vérifier la configuration\n2- Vérifier le code\n3- Réinstaller", "Quelle est l'erreur ?", "Dev", 3,
             "vscode,debug"),
            ("VS Code terminal", "Problème de terminal VS Code", "Problème de terminal",
             "1- Vérifier le terminal\n2- Changer de terminal\n3- Réinstaller", "Quelle est l'erreur ?", "Dev", 3,
             "vscode,terminal"),

            # Développement - Docker
            ("Docker ne s'installe pas", "Docker ne s'installe pas", "Problème d'installation",
             "1- Vérifier l'espace\n2- Télécharger la version correcte\n3- Installer manuellement",
             "Quelle version de Docker ?", "Dev", 3, "docker,installation"),
            ("Docker ne démarre pas", "Docker ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Réinstaller Docker\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Dev", 3, "docker,demarrage"),
            ("Docker image", "Problème d'image Docker", "Image corrompue",
             "1- Supprimer l'image\n2- Rebuild\n3- Télécharger à nouveau", "Quelle image ?", "Dev", 3, "docker,image"),
            ("Docker container", "Problème de container Docker", "Container en erreur",
             "1- Vérifier les logs\n2- Redémarrer\n3- Rebuild", "Quel container ?", "Dev", 3, "docker,container"),
            ("Docker compose", "Problème de Docker Compose", "Problème de compose",
             "1- Vérifier le fichier\n2- Rebuild\n3- Vérifier les services", "Quelle est l'erreur ?", "Dev", 3,
             "docker,compose"),
            ("Docker volume", "Problème de volume Docker", "Problème de volume",
             "1- Vérifier le volume\n2- Recréer le volume\n3- Vérifier les permissions", "Quel volume ?", "Dev", 3,
             "docker,volume"),
            ("Docker network", "Problème de réseau Docker", "Problème de réseau",
             "1- Vérifier le réseau\n2- Recréer le réseau\n3- Vérifier les ports", "Quel réseau ?", "Dev", 3,
             "docker,reseau"),

            # Développement - SQL
            ("SQL ne se connecte pas", "SQL ne se connecte pas", "Problème de connexion",
             "1- Vérifier les identifiants\n2- Vérifier le serveur\n3- Vérifier le port", "Quelle est l'erreur ?",
             "Dev", 3, "sql,connexion"),
            ("SQL query error", "Erreur de requête SQL", "Problème de requête",
             "1- Vérifier la syntaxe\n2- Vérifier les tables\n3- Corriger la requête", "Quelle est l'erreur ?", "Dev",
             3, "sql,query"),
            ("SQL database", "Problème de base SQL", "Base corrompue", "1- Réparer la base\n2- Restaurer\n3- Recréer",
             "Quelle est l'erreur ?", "Dev", 3, "sql,database"),
            ("SQL table", "Problème de table SQL", "Table corrompue", "1- Réparer la table\n2- Recréer\n3- Restaurer",
             "Quelle table ?", "Dev", 3, "sql,table"),
            ("SQL index", "Problème d'index SQL", "Index corrompu",
             "1- Reconstruire l'index\n2- Supprimer l'index\n3- Recréer l'index", "Quel index ?", "Dev", 3,
             "sql,index"),
            ("SQL backup", "Problème de backup SQL", "Backup échoue",
             "1- Vérifier l'espace\n2- Vérifier les permissions\n3- Réessayer", "Quelle est l'erreur ?", "Dev", 3,
             "sql,backup"),

            # Développement - API
            ("API ne répond pas", "API ne répond pas", "Problème d'API",
             "1- Vérifier l'URL\n2- Vérifier les identifiants\n3- Vérifier le serveur", "Quelle est l'erreur ?", "Dev",
             3, "api"),
            ("API timeout", "API timeout", "Problème de timeout",
             "1- Augmenter le timeout\n2- Vérifier le serveur\n3- Optimiser", "Quelle est l'erreur ?", "Dev", 3,
             "api,timeout"),
            ("API authentification", "API authentification échoue", "Problème d'auth",
             "1- Vérifier le token\n2- Vérifier les identifiants\n3- Vérifier les droits", "Quelle est l'erreur ?",
             "Dev", 3, "api,auth"),
            ("API rate limit", "API rate limit atteint", "Problème de rate limit",
             "1- Attendre\n2- Optimiser les requêtes\n3- Contacter le support", "Quelle est l'erreur ?", "Dev", 3,
             "api,rate-limit"),
            ("API JSON", "Problème de JSON API", "JSON invalide",
             "1- Vérifier le JSON\n2- Vérifier le format\n3- Corriger", "Quelle est l'erreur ?", "Dev", 3, "api,json"),
            ("API version", "Problème de version API", "Version incompatible",
             "1- Utiliser la bonne version\n2- Mettre à jour\n3- Contacter le support", "Quelle version ?", "Dev", 3,
             "api,version"),
            # Cloud - AWS
            ("AWS ne se connecte pas", "AWS ne se connecte pas", "Problème de connexion AWS",
             "1- Vérifier les identifiants\n2- Vérifier les permissions\n3- Vérifier le réseau",
             "Quelle est l'erreur ?", "Cloud", 3, "aws,connexion,cloud"),
            ("AWS EC2 ne démarre pas", "EC2 ne démarre pas", "Problème EC2",
             "1- Vérifier l'instance\n2- Vérifier les logs\n3- Redémarrer l'instance", "Quelle est l'erreur ?", "Cloud",
             3, "aws,ec2,cloud"),
            ("AWS S3 ne fonctionne pas", "S3 ne fonctionne pas", "Problème S3",
             "1- Vérifier les permissions\n2- Vérifier le bucket\n3- Vérifier le réseau", "Quelle est l'erreur ?",
             "Cloud", 3, "aws,s3,cloud"),
            ("AWS RDS ne fonctionne pas", "RDS ne fonctionne pas", "Problème RDS",
             "1- Vérifier l'instance\n2- Vérifier les logs\n3- Vérifier le réseau", "Quelle est l'erreur ?", "Cloud", 3,
             "aws,rds,cloud"),
            ("AWS Lambda ne fonctionne pas", "Lambda ne fonctionne pas", "Problème Lambda",
             "1- Vérifier le code\n2- Vérifier les logs\n3- Vérifier les permissions", "Quelle est l'erreur ?", "Cloud",
             3, "aws,lambda,cloud"),
            ("AWS IAM", "Problème de IAM AWS", "Problème de permissions",
             "1- Vérifier les rôles\n2- Vérifier les politiques\n3- Vérifier les identités", "Quelle est l'erreur ?",
             "Cloud", 3, "aws,iam,cloud"),
            ("AWS CloudFormation", "Problème de CloudFormation", "Problème de template",
             "1- Vérifier le template\n2- Vérifier les logs\n3- Vérifier les ressources", "Quelle est l'erreur ?",
             "Cloud", 3, "aws,cloudformation,cloud"),
            ("AWS VPC", "Problème de VPC AWS", "Problème de réseau",
             "1- Vérifier le VPC\n2- Vérifier les subnets\n3- Vérifier les route tables", "Quelle est l'erreur ?",
             "Cloud", 3, "aws,vpc,cloud"),

            # Cloud - Azure
            ("Azure ne se connecte pas", "Azure ne se connecte pas", "Problème de connexion Azure",
             "1- Vérifier les identifiants\n2- Vérifier les permissions\n3- Vérifier le réseau",
             "Quelle est l'erreur ?", "Cloud", 3, "azure,connexion,cloud"),
            ("Azure VM ne démarre pas", "VM Azure ne démarre pas", "Problème VM",
             "1- Vérifier l'instance\n2- Vérifier les logs\n3- Redémarrer l'instance", "Quelle est l'erreur ?", "Cloud",
             3, "azure,vm,cloud"),
            ("Azure Blob ne fonctionne pas", "Azure Blob ne fonctionne pas", "Problème Blob",
             "1- Vérifier les permissions\n2- Vérifier le conteneur\n3- Vérifier le réseau", "Quelle est l'erreur ?",
             "Cloud", 3, "azure,blob,cloud"),
            ("Azure SQL ne fonctionne pas", "Azure SQL ne fonctionne pas", "Problème SQL",
             "1- Vérifier l'instance\n2- Vérifier les logs\n3- Vérifier le réseau", "Quelle est l'erreur ?", "Cloud", 3,
             "azure,sql,cloud"),
            ("Azure Functions ne fonctionne pas", "Azure Functions ne fonctionne pas", "Problème Functions",
             "1- Vérifier le code\n2- Vérifier les logs\n3- Vérifier les permissions", "Quelle est l'erreur ?", "Cloud",
             3, "azure,functions,cloud"),
            ("Azure AD", "Problème de Azure AD", "Problème d'authentification",
             "1- Vérifier les identifiants\n2- Vérifier les permissions\n3- Vérifier le domaine",
             "Quelle est l'erreur ?", "Cloud", 3, "azure,ad,cloud"),
            ("Azure DevOps", "Problème de Azure DevOps", "Problème de pipeline",
             "1- Vérifier le pipeline\n2- Vérifier les logs\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Cloud", 3, "azure,devops,cloud"),
            ("Azure Kubernetes", "Problème de AKS", "Problème de Kubernetes",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Vérifier les nodes", "Quelle est l'erreur ?", "Cloud", 3,
             "azure,aks,cloud"),

            # Cloud - GCP
            ("GCP ne se connecte pas", "GCP ne se connecte pas", "Problème de connexion GCP",
             "1- Vérifier les identifiants\n2- Vérifier les permissions\n3- Vérifier le réseau",
             "Quelle est l'erreur ?", "Cloud", 3, "gcp,connexion,cloud"),
            ("GCP Compute ne fonctionne pas", "Compute Engine ne fonctionne pas", "Problème Compute",
             "1- Vérifier l'instance\n2- Vérifier les logs\n3- Redémarrer l'instance", "Quelle est l'erreur ?", "Cloud",
             3, "gcp,compute,cloud"),
            ("GCP Storage ne fonctionne pas", "GCP Storage ne fonctionne pas", "Problème Storage",
             "1- Vérifier les permissions\n2- Vérifier le bucket\n3- Vérifier le réseau", "Quelle est l'erreur ?",
             "Cloud", 3, "gcp,storage,cloud"),
            ("GCP BigQuery ne fonctionne pas", "BigQuery ne fonctionne pas", "Problème BigQuery",
             "1- Vérifier le projet\n2- Vérifier les permissions\n3- Vérifier la requête", "Quelle est l'erreur ?",
             "Cloud", 3, "gcp,bigquery,cloud"),
            ("GCP Cloud Functions", "Cloud Functions ne fonctionne pas", "Problème Functions",
             "1- Vérifier le code\n2- Vérifier les logs\n3- Vérifier les permissions", "Quelle est l'erreur ?", "Cloud",
             3, "gcp,functions,cloud"),
            ("GCP IAM", "Problème de IAM GCP", "Problème de permissions",
             "1- Vérifier les rôles\n2- Vérifier les politiques\n3- Vérifier les identités", "Quelle est l'erreur ?",
             "Cloud", 3, "gcp,iam,cloud"),
            ("GCP Kubernetes", "Problème de GKE", "Problème de Kubernetes",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Vérifier les nodes", "Quelle est l'erreur ?", "Cloud", 3,
             "gcp,gke,cloud"),

            # Cloud - Général
            ("Problème de cloud", "Problème de cloud en général", "Problème de cloud",
             "1- Vérifier la connexion\n2- Vérifier les identifiants\n3- Vérifier le service", "Quelle est l'erreur ?",
             "Cloud", 3, "cloud"),
            ("Problème de backup cloud", "Backup cloud échoue", "Problème de backup",
             "1- Vérifier l'espace\n2- Vérifier les permissions\n3- Réessayer", "Quelle est l'erreur ?", "Cloud", 3,
             "cloud,backup"),
            ("Problème de migration cloud", "Migration cloud échoue", "Problème de migration",
             "1- Vérifier les données\n2- Vérifier les outils\n3- Réessayer", "Quelle est l'erreur ?", "Cloud", 3,
             "cloud,migration"),
            ("Problème de sécurité cloud", "Sécurité cloud", "Problème de sécurité",
             "1- Vérifier les permissions\n2- Vérifier les logs\n3- Vérifier les accès", "Quelle est l'erreur ?",
             "Cloud", 3, "cloud,securite"),
            ("Problème de coût cloud", "Coût cloud trop élevé", "Problème de coût",
             "1- Vérifier l'utilisation\n2- Optimiser les ressources\n3- Contacter le support", "Quel est le coût ?",
             "Cloud", 3, "cloud,cout"),
            ("Problème de performance cloud", "Performance cloud", "Problème de performance",
             "1- Vérifier les ressources\n2- Optimiser\n3- Contacter le support", "Quelle est l'erreur ?", "Cloud", 3,
             "cloud,performance"),
            ("Problème de monitoring cloud", "Monitoring cloud", "Problème de monitoring",
             "1- Vérifier les logs\n2- Vérifier les métriques\n3- Contacter le support", "Quelle est l'erreur ?",
             "Cloud", 3, "cloud,monitoring"),
            # Virtualisation - VMware
            ("VMware ne s'installe pas", "VMware ne s'installe pas", "Problème d'installation VMware",
             "1- Vérifier l'espace\n2- Télécharger la version correcte\n3- Installer manuellement",
             "Quelle version de VMware ?", "Virtualisation", 3, "vmware,installation,virtualisation"),
            ("VMware ne démarre pas", "VMware ne démarre pas", "Problème de service VMware",
             "1- Vérifier le service\n2- Réinstaller VMware\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Virtualisation", 3, "vmware,demarrage,virtualisation"),
            ("VMware VM ne démarre pas", "VM ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             3, "vmware,vm,virtualisation"),
            ("VMware VM lente", "VM lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 3, "vmware,lent,virtualisation"),
            ("VMware snapshot", "Problème de snapshot VMware", "Snapshot corrompu",
             "1- Supprimer le snapshot\n2- Recréer le snapshot\n3- Vérifier les logs", "Quel est le problème ?",
             "Virtualisation", 3, "vmware,snapshot,virtualisation"),
            ("VMware réseau", "Problème de réseau VMware", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le switch\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 3, "vmware,reseau,virtualisation"),
            ("VMware datastore", "Problème de datastore VMware", "Datastore plein",
             "1- Vérifier l'espace\n2- Nettoyer\n3- Ajouter un datastore", "Quelle est la taille ?", "Virtualisation",
             3, "vmware,datastore,virtualisation"),
            ("VMware HA", "Problème de HA VMware", "Problème de haute disponibilité",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Vérifier les hôtes", "Quelle est l'erreur ?",
             "Virtualisation", 3, "vmware,ha,virtualisation"),
            ("VMware DRS", "Problème de DRS VMware", "Problème de répartition",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Vérifier les hôtes", "Quelle est l'erreur ?",
             "Virtualisation", 3, "vmware,drs,virtualisation"),
            ("VMware vMotion", "Problème de vMotion VMware", "vMotion échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Vérifier les hôtes", "Quelle est l'erreur ?",
             "Virtualisation", 3, "vmware,vmotion,virtualisation"),

            # Virtualisation - Hyper-V
            ("Hyper-V ne s'installe pas", "Hyper-V ne s'installe pas", "Problème d'installation Hyper-V",
             "1- Vérifier l'espace\n2- Activer Hyper-V\n3- Installer manuellement", "Quelle version de Windows ?",
             "Virtualisation", 3, "hyper-v,installation,virtualisation"),
            ("Hyper-V ne démarre pas", "Hyper-V ne démarre pas", "Problème de service Hyper-V",
             "1- Vérifier le service\n2- Réinstaller Hyper-V\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Virtualisation", 3, "hyper-v,demarrage,virtualisation"),
            ("Hyper-V VM ne démarre pas", "VM Hyper-V ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             3, "hyper-v,vm,virtualisation"),
            ("Hyper-V VM lente", "VM Hyper-V lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 3, "hyper-v,lent,virtualisation"),
            ("Hyper-V réseau", "Problème de réseau Hyper-V", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le switch\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 3, "hyper-v,reseau,virtualisation"),
            ("Hyper-V checkpoint", "Problème de checkpoint Hyper-V", "Checkpoint corrompu",
             "1- Supprimer le checkpoint\n2- Recréer le checkpoint\n3- Vérifier les logs", "Quel est le problème ?",
             "Virtualisation", 3, "hyper-v,checkpoint,virtualisation"),
            ("Hyper-V live migration", "Problème de live migration Hyper-V", "Migration échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Vérifier les hôtes", "Quelle est l'erreur ?",
             "Virtualisation", 3, "hyper-v,migration,virtualisation"),
            ("Hyper-V storage", "Problème de stockage Hyper-V", "Stockage plein",
             "1- Vérifier l'espace\n2- Nettoyer\n3- Ajouter du stockage", "Quelle est la taille ?", "Virtualisation", 3,
             "hyper-v,stockage,virtualisation"),

            # Virtualisation - VirtualBox
            ("VirtualBox ne s'installe pas", "VirtualBox ne s'installe pas", "Problème d'installation VirtualBox",
             "1- Vérifier l'espace\n2- Télécharger la version correcte\n3- Installer manuellement",
             "Quelle version de VirtualBox ?", "Virtualisation", 3, "virtualbox,installation,virtualisation"),
            ("VirtualBox ne démarre pas", "VirtualBox ne démarre pas", "Problème de service VirtualBox",
             "1- Vérifier le service\n2- Réinstaller VirtualBox\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualbox,demarrage,virtualisation"),
            ("VirtualBox VM ne démarre pas", "VM VirtualBox ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             3, "virtualbox,vm,virtualisation"),
            ("VirtualBox VM lente", "VM VirtualBox lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 3, "virtualbox,lent,virtualisation"),
            ("VirtualBox réseau", "Problème de réseau VirtualBox", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le NAT\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualbox,reseau,virtualisation"),
            ("VirtualBox USB", "Problème de USB VirtualBox", "USB non reconnu",
             "1- Vérifier les paramètres\n2- Installer les extensions\n3- Vérifier les logs",
             "Quel est le périphérique ?", "Virtualisation", 3, "virtualbox,usb,virtualisation"),
            ("VirtualBox partage", "Problème de partage VirtualBox", "Dossier partagé",
             "1- Vérifier les paramètres\n2- Installer les extensions\n3- Vérifier les logs", "Quel est le dossier ?",
             "Virtualisation", 3, "virtualbox,partage,virtualisation"),

            # Virtualisation - Général
            ("Problème de virtualisation", "Problème de virtualisation en général", "Problème de virtualisation",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Vérifier les ressources", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualisation"),
            ("Problème de performance virtualisation", "Performance virtualisation", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 3, "virtualisation,performance"),
            ("Problème de réseau virtualisation", "Réseau virtualisation", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Vérifier les paramètres", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualisation,reseau"),
            ("Problème de stockage virtualisation", "Stockage virtualisation", "Problème de stockage",
             "1- Vérifier l'espace\n2- Vérifier les logs\n3- Vérifier les paramètres", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualisation,stockage"),
            ("Problème de sécurité virtualisation", "Sécurité virtualisation", "Problème de sécurité",
             "1- Vérifier les permissions\n2- Vérifier les logs\n3- Vérifier les paramètres", "Quelle est l'erreur ?",
             "Virtualisation", 3, "virtualisation,securite"),
            # Cybersécurité avancée - Pentest
            ("Problème de pentest", "Test d'intrusion échoue", "Problème de pentest",
             "1- Vérifier les outils\n2- Vérifier les permissions\n3- Vérifier les cibles", "Quel est l'outil ?",
             "Securite", 4, "pentest,securite"),
            ("Nmap ne fonctionne pas", "Nmap ne fonctionne pas", "Problème de Nmap",
             "1- Vérifier l'installation\n2- Vérifier les permissions\n3- Réinstaller", "Quelle est l'erreur ?",
             "Securite", 4, "nmap,securite"),
            ("Metasploit ne fonctionne pas", "Metasploit ne fonctionne pas", "Problème de Metasploit",
             "1- Vérifier l'installation\n2- Mettre à jour\n3- Réinstaller", "Quelle est l'erreur ?", "Securite", 4,
             "metasploit,securite"),
            ("Burp Suite ne fonctionne pas", "Burp Suite ne fonctionne pas", "Problème de Burp",
             "1- Vérifier l'installation\n2- Vérifier le proxy\n3- Réinstaller", "Quelle est l'erreur ?", "Securite", 4,
             "burp,securite"),
            ("Wireshark ne fonctionne pas", "Wireshark ne fonctionne pas", "Problème de Wireshark",
             "1- Vérifier l'installation\n2- Vérifier les permissions\n3- Réinstaller", "Quelle est l'erreur ?",
             "Securite", 4, "wireshark,securite"),
            ("Hydra ne fonctionne pas", "Hydra ne fonctionne pas", "Problème de Hydra",
             "1- Vérifier l'installation\n2- Vérifier les cibles\n3- Réinstaller", "Quelle est l'erreur ?", "Securite",
             4, "hydra,securite"),
            ("John the Ripper ne fonctionne pas", "John the Ripper ne fonctionne pas", "Problème de John",
             "1- Vérifier l'installation\n2- Vérifier les fichiers\n3- Réinstaller", "Quelle est l'erreur ?",
             "Securite", 4, "john,securite"),

            # Cybersécurité avancée - Forensics
            ("Problème de forensics", "Analyse forensique échoue", "Problème de forensics",
             "1- Vérifier les outils\n2- Vérifier les données\n3- Contacter un expert", "Quel est l'outil ?",
             "Securite", 5, "forensics,securite"),
            ("Problème de récupération de données", "Récupération de données échoue", "Problème de récupération",
             "1- Utiliser un outil de récupération\n2- Contacter un expert\n3- Vérifier le support",
             "Quel est le support ?", "Securite", 5, "recuperation,securite"),
            ("Problème de preuve numérique", "Preuve numérique non valide", "Problème de preuve",
             "1- Vérifier la chaîne de custody\n2- Vérifier l'intégrité\n3- Contacter un expert",
             "Quelle est l'erreur ?", "Securite", 5, "preuve,securite"),
            ("Problème de chiffrement forensics", "Chiffrement bloque l'analyse", "Problème de chiffrement",
             "1- Vérifier la clé\n2- Utiliser un outil de décryptage\n3- Contacter un expert",
             "Quel est le chiffrement ?", "Securite", 5, "chiffrement,forensics,securite"),
            ("Problème de malware analysis", "Analyse de malware échoue", "Problème de malware",
             "1- Vérifier l'environnement\n2- Utiliser un sandbox\n3- Contacter un expert", "Quel est le malware ?",
             "Securite", 5, "malware,analyse,securite"),

            # Cybersécurité avancée - SIEM
            ("SIEM ne fonctionne pas", "SIEM ne fonctionne pas", "Problème de SIEM",
             "1- Vérifier la connexion\n2- Vérifier les logs\n3- Contacter le support", "Quel est le SIEM ?",
             "Securite", 4, "siem,securite"),
            ("Splunk ne fonctionne pas", "Splunk ne fonctionne pas", "Problème de Splunk",
             "1- Vérifier l'installation\n2- Vérifier les logs\n3- Réinstaller", "Quelle est l'erreur ?", "Securite", 4,
             "splunk,securite"),
            ("ELK Stack ne fonctionne pas", "ELK Stack ne fonctionne pas", "Problème de ELK",
             "1- Vérifier Elasticsearch\n2- Vérifier Logstash\n3- Vérifier Kibana", "Quelle est l'erreur ?", "Securite",
             4, "elk,securite"),
            ("Problème de logs", "Les logs ne s'affichent pas", "Problème de logs",
             "1- Vérifier la source\n2- Vérifier le format\n3- Vérifier les permissions", "Quelle est l'erreur ?",
             "Securite", 3, "logs,securite"),
            ("Problème d'alertes", "Les alertes ne fonctionnent pas", "Problème d'alertes",
             "1- Vérifier les règles\n2- Vérifier les notifications\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Securite", 3, "alertes,securite"),

            # Cybersécurité avancée - IDS/IPS
            ("IDS ne fonctionne pas", "IDS ne fonctionne pas", "Problème de IDS",
             "1- Vérifier l'installation\n2- Vérifier les règles\n3- Vérifier les logs", "Quel est le IDS ?",
             "Securite", 4, "ids,securite"),
            ("IPS ne fonctionne pas", "IPS ne fonctionne pas", "Problème de IPS",
             "1- Vérifier l'installation\n2- Vérifier les règles\n3- Vérifier les logs", "Quel est le IPS ?",
             "Securite", 4, "ips,securite"),
            ("Snort ne fonctionne pas", "Snort ne fonctionne pas", "Problème de Snort",
             "1- Vérifier l'installation\n2- Vérifier les règles\n3- Réinstaller", "Quelle est l'erreur ?", "Securite",
             4, "snort,securite"),
            ("Suricata ne fonctionne pas", "Suricata ne fonctionne pas", "Problème de Suricata",
             "1- Vérifier l'installation\n2- Vérifier les règles\n3- Réinstaller", "Quelle est l'erreur ?", "Securite",
             4, "suricata,securite"),
            ("Zeek ne fonctionne pas", "Zeek ne fonctionne pas", "Problème de Zeek",
             "1- Vérifier l'installation\n2- Vérifier les scripts\n3- Réinstaller", "Quelle est l'erreur ?", "Securite",
             4, "zeek,securite"),

            # Cybersécurité avancée - WAF
            ("WAF ne fonctionne pas", "WAF ne fonctionne pas", "Problème de WAF",
             "1- Vérifier l'installation\n2- Vérifier les règles\n3- Vérifier les logs", "Quel est le WAF ?",
             "Securite", 4, "waf,securite"),
            ("Cloudflare WAF", "Problème de Cloudflare WAF", "Problème de WAF",
             "1- Vérifier la configuration\n2- Vérifier les règles\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "cloudflare,waf,securite"),
            ("AWS WAF", "Problème de AWS WAF", "Problème de WAF",
             "1- Vérifier la configuration\n2- Vérifier les règles\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "aws,waf,securite"),
            ("ModSecurity", "Problème de ModSecurity", "Problème de WAF",
             "1- Vérifier la configuration\n2- Vérifier les règles\n3- Réinstaller", "Quelle est l'erreur ?",
             "Securite", 4, "modsecurity,waf,securite"),

            # Cybersécurité avancée - Zero Trust
            ("Problème de Zero Trust", "Zero Trust ne fonctionne pas", "Problème de Zero Trust",
             "1- Vérifier la configuration\n2- Vérifier les identités\n3- Vérifier les accès", "Quelle est l'erreur ?",
             "Securite", 5, "zerotrust,securite"),
            ("Problème de micro-segmentation", "Micro-segmentation ne fonctionne pas", "Problème de segmentation",
             "1- Vérifier la configuration\n2- Vérifier les règles\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Securite", 5, "micro-segmentation,securite"),
            ("Problème de IAM Zero Trust", "IAM Zero Trust ne fonctionne pas", "Problème de IAM",
             "1- Vérifier les identités\n2- Vérifier les permissions\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Securite", 5, "iam,zerotrust,securite"),
            ("Problème de PAM Zero Trust", "PAM Zero Trust ne fonctionne pas", "Problème de PAM",
             "1- Vérifier les identités\n2- Vérifier les permissions\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Securite", 5, "pam,zerotrust,securite"),
            ("Problème de SASE", "SASE ne fonctionne pas", "Problème de SASE",
             "1- Vérifier la connexion\n2- Vérifier la configuration\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 5, "sase,securite"),

            # Cybersécurité avancée - SOC
            ("Problème de SOC", "SOC ne fonctionne pas", "Problème de SOC",
             "1- Vérifier les outils\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "soc,securite"),
            ("Problème de réponse à incident", "Réponse à incident échoue", "Problème d'incident",
             "1- Vérifier le plan\n2- Vérifier les outils\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 5, "incident,securite"),
            ("Problème de threat hunting", "Threat hunting ne fonctionne pas", "Problème de hunting",
             "1- Vérifier les données\n2- Vérifier les outils\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 5, "threat-hunting,securite"),
            ("Problème de CTI", "CTI ne fonctionne pas", "Problème de CTI",
             "1- Vérifier les sources\n2- Vérifier les outils\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "cti,securite"),
            ("Problème de vuln management", "Vulnerability management ne fonctionne pas", "Problème de vulnérabilités",
             "1- Vérifier les scanners\n2- Vérifier les rapports\n3- Contacter le support", "Quelle est l'erreur ?",
             "Securite", 4, "vulnerability,securite"),
            # Mobile - Android
            ("Android ne démarre pas", "Android ne démarre pas", "Problème de système",
             "1- Redémarrer en mode safe\n2- Vider le cache\n3- Réinitialiser", "Quelle version d'Android ?", "Mobile",
             3, "android,demarrage,mobile"),
            ("Android est lent", "Android rame", "Mémoire ou cache plein",
             "1- Vider le cache\n2- Fermer les applications\n3- Redémarrer", "Depuis quand ?", "Mobile", 2,
             "android,lent,mobile"),
            ("Android application plante", "Application Android plante", "Problème d'application",
             "1- Vider le cache\n2- Réinstaller\n3- Mettre à jour", "Quelle application ?", "Mobile", 3,
             "android,application,mobile"),
            ("Android batterie se vide vite", "Batterie Android se vide", "Application en arrière-plan",
             "1- Vérifier les applications\n2- Désactiver les notifications\n3- Activer l'économie d'énergie",
             "Depuis quand ?", "Mobile", 2, "android,batterie,mobile"),
            ("Android WiFi ne se connecte pas", "WiFi Android ne se connecte pas", "Problème de WiFi",
             "1- Redémarrer le WiFi\n2- Oublier le réseau\n3- Redémarrer le téléphone", "Le WiFi s'affiche-t-il ?",
             "Mobile", 2, "android,wifi,mobile"),
            ("Android Bluetooth ne fonctionne pas", "Bluetooth Android ne fonctionne pas", "Problème de Bluetooth",
             "1- Redémarrer Bluetooth\n2- Oublier l'appareil\n3- Redémarrer le téléphone",
             "Le Bluetooth s'affiche-t-il ?", "Mobile", 2, "android,bluetooth,mobile"),
            ("Android USB ne fonctionne pas", "USB Android ne fonctionne pas", "Problème de USB",
             "1- Vérifier le câble\n2- Vérifier le port\n3- Activer le débogage USB", "Le téléphone est-il détecté ?",
             "Mobile", 3, "android,usb,mobile"),
            ("Android écran cassé", "Écran Android cassé", "Problème d'écran",
             "1- Contacter un réparateur\n2- Remplacer l'écran\n3- Sauvegarder les données", "L'écran est-il fissuré ?",
             "Mobile", 3, "android,ecran,mobile"),
            ("Android son ne fonctionne pas", "Son Android ne fonctionne pas", "Problème de son",
             "1- Vérifier le volume\n2- Redémarrer\n3- Vérifier les haut-parleurs", "Le son est-il activé ?", "Mobile",
             2, "android,son,mobile"),
            ("Android micro ne fonctionne pas", "Micro Android ne fonctionne pas", "Problème de micro",
             "1- Vérifier le micro\n2- Redémarrer\n3- Contacter un réparateur", "Le micro est-il reconnu ?", "Mobile",
             3, "android,micro,mobile"),
            ("Android appareil photo ne fonctionne pas", "Appareil photo Android ne fonctionne pas",
             "Problème de caméra", "1- Vider le cache\n2- Redémarrer\n3- Contacter un réparateur",
             "L'appareil photo s'ouvre-t-il ?", "Mobile", 3, "android,camera,mobile"),
            ("Android mises à jour ne s'installent pas", "Mises à jour Android ne s'installent pas",
             "Problème de mise à jour", "1- Vérifier l'espace\n2- Vider le cache\n3- Télécharger manuellement",
             "Quelle est l'erreur ?", "Mobile", 3, "android,update,mobile"),
            ("Android Google Play ne fonctionne pas", "Google Play ne fonctionne pas", "Problème de Play Store",
             "1- Vider le cache\n2- Vider les données\n3- Réinstaller", "Quelle est l'erreur ?", "Mobile", 3,
             "android,playstore,mobile"),
            ("Android Gmail ne fonctionne pas", "Gmail Android ne fonctionne pas", "Problème de Gmail",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "android,gmail,mobile"),
            ("Android Maps ne fonctionne pas", "Google Maps ne fonctionne pas", "Problème de Maps",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le GPS", "Quelle est l'erreur ?", "Mobile", 3,
             "android,maps,mobile"),
            ("Android WhatsApp ne fonctionne pas", "WhatsApp ne fonctionne pas", "Problème de WhatsApp",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "android,whatsapp,mobile"),
            ("Android Messenger ne fonctionne pas", "Messenger ne fonctionne pas", "Problème de Messenger",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "android,messenger,mobile"),
            ("Android Instagram ne fonctionne pas", "Instagram ne fonctionne pas", "Problème de Instagram",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "android,instagram,mobile"),
            ("Android TikTok ne fonctionne pas", "TikTok ne fonctionne pas", "Problème de TikTok",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "android,tiktok,mobile"),

            # Mobile - iOS
            ("iPhone ne démarre pas", "iPhone ne démarre pas", "Problème de système",
             "1- Forcer le redémarrage\n2- Mode DFU\n3- Restaurer", "Quel modèle d'iPhone ?", "Mobile", 3,
             "iphone,demarrage,mobile"),
            ("iPhone est lent", "iPhone rame", "Mémoire pleine",
             "1- Vider le cache\n2- Fermer les applications\n3- Redémarrer", "Depuis quand ?", "Mobile", 2,
             "iphone,lent,mobile"),
            ("iPhone application plante", "Application iPhone plante", "Problème d'application",
             "1- Vider le cache\n2- Réinstaller\n3- Mettre à jour", "Quelle application ?", "Mobile", 3,
             "iphone,application,mobile"),
            ("iPhone batterie se vide vite", "Batterie iPhone se vide", "Application en arrière-plan",
             "1- Vérifier les applications\n2- Désactiver les notifications\n3- Activer l'économie d'énergie",
             "Depuis quand ?", "Mobile", 2, "iphone,batterie,mobile"),
            ("iPhone WiFi ne se connecte pas", "WiFi iPhone ne se connecte pas", "Problème de WiFi",
             "1- Redémarrer le WiFi\n2- Oublier le réseau\n3- Redémarrer l'iPhone", "Le WiFi s'affiche-t-il ?",
             "Mobile", 2, "iphone,wifi,mobile"),
            ("iPhone Bluetooth ne fonctionne pas", "Bluetooth iPhone ne fonctionne pas", "Problème de Bluetooth",
             "1- Redémarrer Bluetooth\n2- Oublier l'appareil\n3- Redémarrer l'iPhone", "Le Bluetooth s'affiche-t-il ?",
             "Mobile", 2, "iphone,bluetooth,mobile"),
            ("iPhone USB ne fonctionne pas", "USB iPhone ne fonctionne pas", "Problème de USB",
             "1- Vérifier le câble\n2- Vérifier le port\n3- Redémarrer l'iPhone", "L'iPhone est-il détecté ?", "Mobile",
             3, "iphone,usb,mobile"),
            ("iPhone écran cassé", "Écran iPhone cassé", "Problème d'écran",
             "1- Contacter Apple\n2- Remplacer l'écran\n3- Sauvegarder les données", "L'écran est-il fissuré ?",
             "Mobile", 3, "iphone,ecran,mobile"),
            ("iPhone son ne fonctionne pas", "Son iPhone ne fonctionne pas", "Problème de son",
             "1- Vérifier le volume\n2- Redémarrer\n3- Vérifier le mode silencieux", "Le son est-il activé ?", "Mobile",
             2, "iphone,son,mobile"),
            ("iPhone micro ne fonctionne pas", "Micro iPhone ne fonctionne pas", "Problème de micro",
             "1- Vérifier le micro\n2- Redémarrer\n3- Contacter Apple", "Le micro est-il reconnu ?", "Mobile", 3,
             "iphone,micro,mobile"),
            ("iPhone appareil photo ne fonctionne pas", "Appareil photo iPhone ne fonctionne pas", "Problème de caméra",
             "1- Vider le cache\n2- Redémarrer\n3- Contacter Apple", "L'appareil photo s'ouvre-t-il ?", "Mobile", 3,
             "iphone,camera,mobile"),
            ("iPhone mises à jour ne s'installent pas", "Mises à jour iOS ne s'installent pas",
             "Problème de mise à jour", "1- Vérifier l'espace\n2- Vider le cache\n3- Télécharger manuellement",
             "Quelle est l'erreur ?", "Mobile", 3, "iphone,update,mobile"),
            ("iPhone App Store ne fonctionne pas", "App Store iPhone ne fonctionne pas", "Problème de App Store",
             "1- Vider le cache\n2- Vider les données\n3- Redémarrer", "Quelle est l'erreur ?", "Mobile", 3,
             "iphone,appstore,mobile"),
            ("iPhone Mail ne fonctionne pas", "Mail iPhone ne fonctionne pas", "Problème de Mail",
             "1- Vider le cache\n2- Réinstaller\n3- Vérifier le compte", "Quelle est l'erreur ?", "Mobile", 3,
             "iphone,mail,mobile"),
            ("iPhone Face ID ne fonctionne pas", "Face ID iPhone ne fonctionne pas", "Problème de Face ID",
             "1- Nettoyer la caméra\n2- Réinitialiser\n3- Contacter Apple", "Face ID est-il activé ?", "Mobile", 3,
             "iphone,faceid,mobile"),
            ("iPhone Touch ID ne fonctionne pas", "Touch ID iPhone ne fonctionne pas", "Problème de Touch ID",
             "1- Nettoyer le capteur\n2- Réinitialiser\n3- Contacter Apple", "Touch ID est-il activé ?", "Mobile", 3,
             "iphone,touchid,mobile"),
            ("iPhone iCloud ne synchronise pas", "iCloud ne synchronise pas", "Problème de iCloud",
             "1- Vérifier la connexion\n2- Vérifier le compte\n3- Redémarrer", "Quelle est l'erreur ?", "Mobile", 3,
             "iphone,icloud,mobile"),
            ("iPhone AirDrop ne fonctionne pas", "AirDrop ne fonctionne pas", "Problème de AirDrop",
             "1- Vérifier WiFi/Bluetooth\n2- Redémarrer\n3- Vérifier les paramètres", "AirDrop est-il activé ?",
             "Mobile", 3, "iphone,airdrop,mobile"),
            ("iPhone Apple Pay ne fonctionne pas", "Apple Pay ne fonctionne pas", "Problème de Apple Pay",
             "1- Vérifier la carte\n2- Vérifier le compte\n3- Contacter la banque", "Apple Pay est-il activé ?",
             "Mobile", 3, "iphone,applepay,mobile"),
            ("iPhone Siri ne fonctionne pas", "Siri ne fonctionne pas", "Problème de Siri",
             "1- Vérifier la connexion\n2- Redémarrer\n3- Vérifier les paramètres", "Siri est-il activé ?", "Mobile", 3,
             "iphone,siri,mobile"),
            # Réseau avancé - BGP
            ("Problème de BGP", "BGP ne fonctionne pas", "Problème de BGP",
             "1- Vérifier les voisins\n2- Vérifier les préfixes\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "bgp,reseau"),
            ("Problème de route BGP", "Route BGP non apprise", "Problème de BGP",
             "1- Vérifier les filtres\n2- Vérifier les AS\n3- Vérifier les logs", "Quelle route ?", "Reseau", 5,
             "bgp,route,reseau"),
            ("Problème de BGP sessions", "Sessions BGP down", "Problème de BGP",
             "1- Vérifier la connectivité\n2- Vérifier les paramètres\n3- Vérifier les logs", "Quelle session ?",
             "Reseau", 5, "bgp,session,reseau"),
            ("Problème de BGP attributes", "Attributs BGP incorrects", "Problème de BGP",
             "1- Vérifier les attributs\n2- Vérifier les politiques\n3- Vérifier les logs", "Quel attribut ?", "Reseau",
             5, "bgp,attribut,reseau"),
            ("Problème de BGP communities", "Communautés BGP incorrectes", "Problème de BGP",
             "1- Vérifier les communautés\n2- Vérifier les politiques\n3- Vérifier les logs", "Quelle communauté ?",
             "Reseau", 5, "bgp,communautes,reseau"),

            # Réseau avancé - OSPF
            ("Problème de OSPF", "OSPF ne fonctionne pas", "Problème de OSPF",
             "1- Vérifier les voisins\n2- Vérifier les zones\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau",
             5, "ospf,reseau"),
            ("Problème de voisin OSPF", "Voisin OSPF down", "Problème de OSPF",
             "1- Vérifier la connectivité\n2- Vérifier les paramètres\n3- Vérifier les logs", "Quel voisin ?", "Reseau",
             5, "ospf,voisin,reseau"),
            ("Problème de route OSPF", "Route OSPF non apprise", "Problème de OSPF",
             "1- Vérifier les zones\n2- Vérifier les métriques\n3- Vérifier les logs", "Quelle route ?", "Reseau", 5,
             "ospf,route,reseau"),
            ("Problème de zone OSPF", "Zone OSPF incorrecte", "Problème de OSPF",
             "1- Vérifier les zones\n2- Vérifier les paramètres\n3- Vérifier les logs", "Quelle zone ?", "Reseau", 5,
             "ospf,zone,reseau"),
            ("Problème de OSPF authentication", "Authentification OSPF échoue", "Problème de OSPF",
             "1- Vérifier l'authentification\n2- Vérifier les clés\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "ospf,auth,reseau"),

            # Réseau avancé - MPLS
            ("Problème de MPLS", "MPLS ne fonctionne pas", "Problème de MPLS",
             "1- Vérifier les LSP\n2- Vérifier les labels\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau", 5,
             "mpls,reseau"),
            ("Problème de LDP", "LDP ne fonctionne pas", "Problème de MPLS",
             "1- Vérifier les voisins\n2- Vérifier les labels\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau",
             5, "mpls,ldp,reseau"),
            ("Problème de RSVP", "RSVP ne fonctionne pas", "Problème de MPLS",
             "1- Vérifier les voisins\n2- Vérifier les reservations\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "mpls,rsvp,reseau"),
            ("Problème de TE", "Traffic engineering ne fonctionne pas", "Problème de MPLS",
             "1- Vérifier les tunnels\n2- Vérifier les paramètres\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "mpls,te,reseau"),
            ("Problème de VPN MPLS", "VPN MPLS ne fonctionne pas", "Problème de MPLS",
             "1- Vérifier les VRF\n2- Vérifier les routes\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau", 5,
             "mpls,vpn,reseau"),

            # Réseau avancé - SDN
            ("Problème de SDN", "SDN ne fonctionne pas", "Problème de SDN",
             "1- Vérifier le controller\n2- Vérifier les switches\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "sdn,reseau"),
            ("Problème de OpenFlow", "OpenFlow ne fonctionne pas", "Problème de SDN",
             "1- Vérifier le controller\n2- Vérifier les règles\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "sdn,openflow,reseau"),
            ("Problème de SDN controller", "Controller SDN ne fonctionne pas", "Problème de SDN",
             "1- Vérifier le service\n2- Vérifier la configuration\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 5, "sdn,controller,reseau"),
            ("Problème de SDN switch", "Switch SDN ne fonctionne pas", "Problème de SDN",
             "1- Vérifier la connectivité\n2- Vérifier les règles\n3- Vérifier les logs", "Quel switch ?", "Reseau", 5,
             "sdn,switch,reseau"),
            ("Problème de SDN application", "Application SDN ne fonctionne pas", "Problème de SDN",
             "1- Vérifier l'application\n2- Vérifier les APIs\n3- Vérifier les logs", "Quelle application ?", "Reseau",
             5, "sdn,app,reseau"),

            # Réseau avancé - Load Balancing
            ("Problème de load balancing", "Load balancing ne fonctionne pas", "Problème de LB",
             "1- Vérifier les pools\n2- Vérifier les membres\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau",
             4, "load-balancing,reseau"),
            ("Problème de HAProxy", "HAProxy ne fonctionne pas", "Problème de HAProxy",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Réinstaller", "Quelle est l'erreur ?", "Reseau", 4,
             "haproxy,reseau"),
            ("Problème de NGINX LB", "NGINX load balancing ne fonctionne pas", "Problème de NGINX",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Réinstaller", "Quelle est l'erreur ?", "Reseau", 4,
             "nginx,lb,reseau"),
            ("Problème de F5", "F5 ne fonctionne pas", "Problème de F5",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Reseau", 5, "f5,reseau"),
            ("Problème de AWS ELB", "AWS ELB ne fonctionne pas", "Problème de ELB",
             "1- Vérifier les instances\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Reseau", 4, "aws,elb,reseau"),

            # Réseau avancé - CDN
            ("Problème de CDN", "CDN ne fonctionne pas", "Problème de CDN",
             "1- Vérifier les origins\n2- Vérifier les caches\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau",
             4, "cdn,reseau"),
            ("Problème de CloudFront", "CloudFront ne fonctionne pas", "Problème de CDN",
             "1- Vérifier les origins\n2- Vérifier les distributions\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 4, "cloudfront,cdn,reseau"),
            ("Problème de Cloudflare", "Cloudflare ne fonctionne pas", "Problème de CDN",
             "1- Vérifier le DNS\n2- Vérifier les règles\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau", 4,
             "cloudflare,cdn,reseau"),
            ("Problème de Fastly", "Fastly ne fonctionne pas", "Problème de CDN",
             "1- Vérifier les origins\n2- Vérifier les services\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Reseau", 4, "fastly,cdn,reseau"),
            ("Problème de cache CDN", "Cache CDN ne fonctionne pas", "Problème de CDN",
             "1- Vider le cache\n2- Vérifier les règles\n3- Vérifier les logs", "Quelle est l'erreur ?", "Reseau", 4,
             "cdn,cache,reseau"),
            # Réseaux sociaux
            ("Publication Facebook impossible", "Impossible de publier sur la page Facebook",
             "Problème de permissions ou d'API",
             "1- Vérifier votre connexion\n2- Vérifier le niveau d'accès\n3- Contacter le support Facebook",
             "Avez-vous changé votre mot de passe ?", "Reseau social", 3, "facebook,publication"),
            ("Compte Instagram bloqué", "Compte Instagram temporairement bloqué", "Activité suspecte ou spam",
             "1- Vérifier vos emails\n2- Changer votre mot de passe\n3- Contacter le support Instagram",
             "Avez-vous utilisé une application tierce ?", "Reseau social", 3, "instagram,bloque"),
            ("Problème de visibilité LinkedIn", "Les publications ne sont pas vues", "Problème d'algorithme",
             "1- Varier les formats de contenu\n2- Interagir plus souvent\n3- Utiliser des hashtags pertinents",
             "Quel type de contenu publiez-vous ?", "Reseau social", 2, "linkedin,visibilite"),
            ("Tweet ne se publie pas", "Impossible de tweeter", "Problème d'API ou de limites",
             "1- Vérifier votre connexion\n2- Vérifier la longueur du tweet\n3- Réessayer plus tard",
             "Le tweet est-il trop long ?", "Reseau social", 2, "twitter,tweet"),
            ("Problème de vidéo YouTube", "La vidéo ne se téléverse pas", "Problème de format ou de droits",
             "1- Vérifier le format de la vidéo\n2- Vérifier la taille du fichier\n3- Vérifier les droits d'auteur",
             "Quel est le format de la vidéo ?", "Reseau social", 3, "youtube,video"),
            ("Problème de téléchargement TikTok", "La vidéo ne se télécharge pas", "Problème de réseau ou de serveur",
             "1- Vérifier votre connexion Internet\n2- Réessayer plus tard\n3- Vider le cache de l'application",
             "L'application est-elle à jour ?", "Reseau social", 3, "tiktok,telechargement"),
            ("Perte de mots de passe réseaux sociaux", "Mot de passe des réseaux sociaux oublié", "Mot de passe perdu",
             "1- Utiliser la fonction 'Mot de passe oublié'\n2- Vérifier vos emails\n3- Contacter le support",
             "Avez-vous plusieurs comptes ?", "Reseau social", 2, "reseau-social,mdp"),
            ("Problème de synchronisation entre médias", "Publication non synchronisée sur plusieurs réseaux",
             "Problème d'outil de gestion (ex: Buffer)",
             "1- Vérifier la connexion de l'outil\n2- Vérifier les permissions\n3- Publier manuellement",
             "Utilisez-vous un outil de gestion ?", "Reseau social", 3, "synchronisation,reseau-social"),
            # Stockage - NAS
            ("NAS ne répond pas", "Le NAS ne répond plus au réseau", "Problème réseau ou disque HS",
             "1- Vérifier le réseau\n2- Redémarrer le NAS\n3- Vérifier les disques", "Les LEDs sont-elles allumées ?",
             "Stockage", 3, "nas,stockage"),
            ("NAS disque HS", "Un disque du NAS est mort", "Disque dur défaillant",
             "1- Identifier le disque défaillant\n2- Remplacer le disque\n3- Reconstruire le RAID",
             "Quel est le statut du RAID ?", "Stockage", 4, "nas,disque,raid"),
            ("NAS RAID dégradé", "Le RAID du NAS est dégradé", "Un disque est mort",
             "1- Remplacer le disque\n2- Reconstruire le RAID\n3- Vérifier les logs", "Quel est le niveau du RAID ?",
             "Stockage", 4, "nas,raid,degrade"),
            ("NAS lent", "Le NAS est très lent", "Disques lents ou réseau saturé",
             "1- Vérifier le réseau\n2- Vérifier les disques\n3- Vérifier les logs", "Quelle est la vitesse ?",
             "Stockage", 3, "nas,lent,stockage"),
            ("NAS connexion impossible", "Impossible de se connecter au NAS", "Problème réseau",
             "1- Vérifier le réseau\n2- Vérifier les identifiants\n3- Redémarrer le NAS", "Le NAS est-il allumé ?",
             "Stockage", 3, "nas,connexion,stockage"),
            ("NAS sauvegarde échoue", "La sauvegarde sur le NAS échoue", "Problème de droits ou d'espace",
             "1- Vérifier l'espace disque\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Stockage",
             3, "nas,sauvegarde,stockage"),

            # Stockage - SAN
            ("SAN ne répond pas", "Le SAN ne répond plus", "Problème réseau ou de disque",
             "1- Vérifier le réseau FC\n2- Redémarrer le SAN\n3- Vérifier les logs", "Les LEDs sont-elles allumées ?",
             "Stockage", 4, "san,stockage"),
            ("SAN performance", "Le SAN est lent", "Problème de disque ou de réseau",
             "1- Vérifier les disques\n2- Vérifier le réseau\n3- Vérifier les logs", "Quelle est la performance ?",
             "Stockage", 4, "san,performance,stockage"),
            ("SAN LUN non reconnue", "Une LUN n'est pas reconnue", "Problème de mapping",
             "1- Vérifier le mapping\n2- Vérifier les permissions\n3- Redémarrer le SAN", "La LUN est-elle visible ?",
             "Stockage", 4, "san,lun,stockage"),
            ("SAN snapshot", "Problème de snapshot SAN", "Espace insuffisant",
             "1- Vérifier l'espace\n2- Supprimer les anciens snapshots\n3- Recréer le snapshot",
             "Quelle est la taille ?", "Stockage", 4, "san,snapshot,stockage"),
            ("SAN réplication", "Problème de réplication SAN", "Problème réseau ou de disque",
             "1- Vérifier le réseau\n2- Vérifier les disques\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Stockage", 4, "san,replication,stockage"),

            # Stockage - Sauvegarde
            ("Sauvegarde Windows échoue", "La sauvegarde Windows échoue", "Problème de disque",
             "1- Vérifier l'espace disque\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Stockage",
             3, "sauvegarde,windows"),
            ("Sauvegarde Linux échoue", "La sauvegarde Linux échoue", "Problème de droits ou d'espace",
             "1- Vérifier l'espace\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Stockage", 3,
             "sauvegarde,linux"),
            ("Sauvegarde Mac échoue", "La sauvegarde Mac échoue", "Problème de Time Machine",
             "1- Vérifier le disque\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Stockage", 3,
             "sauvegarde,mac"),
            ("Restauration échoue", "La restauration des données échoue", "Problème de fichier",
             "1- Vérifier les fichiers\n2- Vérifier les droits\n3- Réessayer", "Quel est le fichier ?", "Stockage", 4,
             "restauration,sauvegarde"),
            ("Backup cloud échoue", "Le backup cloud échoue", "Problème de connexion",
             "1- Vérifier la connexion\n2- Vérifier les identifiants\n3- Réessayer", "Quelle est l'erreur ?",
             "Stockage", 3, "backup,cloud"),
            ("Backup local échoue", "Le backup local échoue", "Problème de disque",
             "1- Vérifier le disque\n2- Vérifier l'espace\n3- Réessayer", "Quelle est l'erreur ?", "Stockage", 3,
             "backup,local"),
            ("Sauvegarde corrompue", "La sauvegarde est corrompue", "Problème de fichier",
             "1- Vérifier les fichiers\n2- Recréer la sauvegarde\n3- Utiliser un outil de récupération",
             "Quel est le fichier ?", "Stockage", 4, "sauvegarde,corrompue"),
            ("Plan de sauvegarde", "Le plan de sauvegarde ne fonctionne pas", "Problème de configuration",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Stockage", 3,
             "sauvegarde,plan"),
            ("Rétention sauvegarde", "Problème de rétention des sauvegardes", "Espace insuffisant",
             "1- Vérifier l'espace\n2- Supprimer les anciennes sauvegardes\n3- Augmenter l'espace",
             "Quelle est la rétention ?", "Stockage", 3, "sauvegarde,retention"),
            # Messagerie - Exchange / Mail
            ("Exchange ne démarre pas", "Exchange ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Messagerie", 4,
             "exchange,messagerie"),
            ("Exchange base corrompue", "La base Exchange est corrompue", "Problème de base",
             "1- Utiliser eseutil\n2- Restaurer la base\n3- Contacter le support", "Que dit eseutil ?", "Messagerie", 5,
             "exchange,base-corrompue,messagerie"),
            ("SMTP ne fonctionne pas", "Le serveur SMTP ne fonctionne pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier le port\n3- Vérifier les logs", "Quelle est l'erreur ?", "Messagerie",
             3, "smtp,messagerie"),
            ("POP3 ne fonctionne pas", "Le serveur POP3 ne fonctionne pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier le port\n3- Vérifier les logs", "Quelle est l'erreur ?", "Messagerie",
             3, "pop3,messagerie"),
            ("IMAP ne fonctionne pas", "Le serveur IMAP ne fonctionne pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier le port\n3- Vérifier les logs", "Quelle est l'erreur ?", "Messagerie",
             3, "imap,messagerie"),
            ("Email non reçu", "Les emails ne sont pas reçus", "Problème de DNS",
             "1- Vérifier le DNS\n2- Vérifier le MX\n3- Vérifier les logs", "Quelle est l'erreur ?", "Messagerie", 3,
             "email,reception,messagerie"),
            ("Email non envoyé", "Les emails ne sont pas envoyés", "Problème de SMTP",
             "1- Vérifier le SMTP\n2- Vérifier les identifiants\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Messagerie", 3, "email,envoi,messagerie"),
            ("Spam detection", "Les emails sont marqués comme spam", "Problème de réputation",
             "1- Vérifier la réputation\n2- Vérifier les headers\n3- Contacter le support", "Quelle est l'erreur ?",
             "Messagerie", 3, "spam,email,messagerie"),
            ("Phishing détecté", "Email de phishing détecté", "Problème de sécurité",
             "1- Ne pas cliquer\n2- Signaler l'email\n3- Changer les mots de passe", "Avez-vous cliqué ?", "Messagerie",
             4, "phishing,email,messagerie"),
            ("Boîte mail pleine", "La boîte mail est pleine", "Espace insuffisant",
             "1- Supprimer les anciens emails\n2- Vider la corbeille\n3- Augmenter l'espace", "Quelle est la taille ?",
             "Messagerie", 2, "boite-mail,pleine,messagerie"),

            # Collaboration - Slack
            ("Slack ne se connecte pas", "Slack ne se connecte pas", "Problème de connexion",
             "1- Vérifier la connexion\n2- Vérifier les identifiants\n3- Vérifier le proxy", "Quelle est l'erreur ?",
             "Collaboration", 3, "slack,connexion,collaboration"),
            ("Slack notifications", "Les notifications Slack ne fonctionnent pas", "Problème de paramètres",
             "1- Vérifier les paramètres\n2- Vérifier les permissions\n3- Réinstaller", "Quelle est l'erreur ?",
             "Collaboration", 3, "slack,notifications,collaboration"),
            ("Slack fichiers", "Problème de partage de fichiers Slack", "Problème de fichiers",
             "1- Vérifier le fichier\n2- Vérifier les permissions\n3- Réessayer", "Quel est le fichier ?",
             "Collaboration", 3, "slack,fichiers,collaboration"),

            # Collaboration - Zoom
            ("Zoom ne démarre pas", "Zoom ne démarre pas", "Problème de Zoom",
             "1- Réinstaller Zoom\n2- Vérifier les permissions\n3- Vider le cache", "Quelle est l'erreur ?",
             "Collaboration", 3, "zoom,demarrage,collaboration"),
            ("Zoom audio", "Problème d'audio sur Zoom", "Problème de micro",
             "1- Vérifier le micro\n2- Vérifier les permissions\n3- Vérifier les paramètres",
             "Le micro est-il reconnu ?", "Collaboration", 3, "zoom,audio,collaboration"),
            ("Zoom vidéo", "Problème de vidéo sur Zoom", "Problème de caméra",
             "1- Vérifier la caméra\n2- Vérifier les permissions\n3- Vérifier les paramètres",
             "La caméra est-elle reconnue ?", "Collaboration", 3, "zoom,video,collaboration"),
            ("Zoom partage d'écran", "Problème de partage d'écran sur Zoom", "Problème de permissions",
             "1- Vérifier les permissions\n2- Vérifier les paramètres\n3- Réinstaller Zoom", "Quelle est l'erreur ?",
             "Collaboration", 3, "zoom,partage,collaboration"),

            # Collaboration - Teams
            ("Teams ne démarre pas", "Teams ne démarre pas", "Problème de Teams",
             "1- Vider le cache\n2- Réinstaller Teams\n3- Vérifier la connexion", "Quelle est l'erreur ?",
             "Collaboration", 3, "teams,demarrage,collaboration"),
            ("Teams appel", "Problème d'appel sur Teams", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier le micro\n3- Vérifier la caméra", "Quelle est l'erreur ?",
             "Collaboration", 3, "teams,appel,collaboration"),
            ("Teams réunion", "Problème de réunion Teams", "Problème de paramètres",
             "1- Vérifier les paramètres\n2- Vérifier les permissions\n3- Réinstaller Teams", "Quelle est l'erreur ?",
             "Collaboration", 3, "teams,reunion,collaboration"),
            # E-commerce - Shopify
            ("Shopify ne se connecte pas", "Shopify ne se connecte pas", "Problème de connexion Shopify",
             "1- Vérifier la connexion Internet\n2- Vérifier les identifiants\n3- Contacter le support",
             "Quelle est l'erreur ?", "E-commerce", 3, "shopify,ecommerce"),
            ("Shopify lent", "Shopify est lent", "Problème de performance",
             "1- Vider le cache\n2- Optimiser les images\n3- Contacter le support", "Depuis quand ?", "E-commerce", 3,
             "shopify,lent,ecommerce"),
            ("Shopify paiement", "Problème de paiement Shopify", "Paiement refusé",
             "1- Vérifier la carte\n2- Vérifier le compte\n3- Contacter la banque", "Quelle est l'erreur ?",
             "E-commerce", 3, "shopify,paiement,ecommerce"),
            ("Shopify commande", "Problème de commande Shopify", "Commande non traitée",
             "1- Vérifier le stock\n2- Vérifier le paiement\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "shopify,commande,ecommerce"),
            ("Shopify stock", "Problème de stock Shopify", "Stock incorrect",
             "1- Vérifier le stock\n2- Mettre à jour\n3- Contacter le support", "Quel est le produit ?", "E-commerce",
             3, "shopify,stock,ecommerce"),
            ("Shopify produit", "Problème de produit Shopify", "Produit non visible",
             "1- Vérifier le produit\n2- Vérifier le statut\n3- Contacter le support", "Quel est le produit ?",
             "E-commerce", 3, "shopify,produit,ecommerce"),

            # E-commerce - WooCommerce
            ("WooCommerce ne se connecte pas", "WooCommerce ne se connecte pas", "Problème de connexion",
             "1- Vérifier le site\n2- Vérifier les identifiants\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "woocommerce,ecommerce"),
            ("WooCommerce lent", "WooCommerce est lent", "Problème de performance",
             "1- Vider le cache\n2- Optimiser les images\n3- Contacter le support", "Depuis quand ?", "E-commerce", 3,
             "woocommerce,lent,ecommerce"),
            ("WooCommerce paiement", "Problème de paiement WooCommerce", "Paiement refusé",
             "1- Vérifier la carte\n2- Vérifier le compte\n3- Contacter la banque", "Quelle est l'erreur ?",
             "E-commerce", 3, "woocommerce,paiement,ecommerce"),
            ("WooCommerce commande", "Problème de commande WooCommerce", "Commande non traitée",
             "1- Vérifier le stock\n2- Vérifier le paiement\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "woocommerce,commande,ecommerce"),
            ("WooCommerce stock", "Problème de stock WooCommerce", "Stock incorrect",
             "1- Vérifier le stock\n2- Mettre à jour\n3- Contacter le support", "Quel est le produit ?", "E-commerce",
             3, "woocommerce,stock,ecommerce"),
            ("WooCommerce produit", "Problème de produit WooCommerce", "Produit non visible",
             "1- Vérifier le produit\n2- Vérifier le statut\n3- Contacter le support", "Quel est le produit ?",
             "E-commerce", 3, "woocommerce,produit,ecommerce"),

            # E-commerce - PrestaShop
            ("PrestaShop ne se connecte pas", "PrestaShop ne se connecte pas", "Problème de connexion",
             "1- Vérifier le site\n2- Vérifier les identifiants\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "prestashop,ecommerce"),
            ("PrestaShop lent", "PrestaShop est lent", "Problème de performance",
             "1- Vider le cache\n2- Optimiser les images\n3- Contacter le support", "Depuis quand ?", "E-commerce", 3,
             "prestashop,lent,ecommerce"),
            ("PrestaShop paiement", "Problème de paiement PrestaShop", "Paiement refusé",
             "1- Vérifier la carte\n2- Vérifier le compte\n3- Contacter la banque", "Quelle est l'erreur ?",
             "E-commerce", 3, "prestashop,paiement,ecommerce"),
            ("PrestaShop commande", "Problème de commande PrestaShop", "Commande non traitée",
             "1- Vérifier le stock\n2- Vérifier le paiement\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "prestashop,commande,ecommerce"),
            ("PrestaShop stock", "Problème de stock PrestaShop", "Stock incorrect",
             "1- Vérifier le stock\n2- Mettre à jour\n3- Contacter le support", "Quel est le produit ?", "E-commerce",
             3, "prestashop,stock,ecommerce"),

            # E-commerce - Général
            ("Problème de panier", "Le panier ne fonctionne pas", "Problème de panier",
             "1- Vider le panier\n2- Vérifier le site\n3- Contacter le support", "Quelle est l'erreur ?", "E-commerce",
             3, "panier,ecommerce"),
            ("Problème de livraison", "La livraison ne fonctionne pas", "Problème de livraison",
             "1- Vérifier l'adresse\n2- Vérifier le transporteur\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "livraison,ecommerce"),
            ("Problème de facturation", "La facturation ne fonctionne pas", "Problème de facturation",
             "1- Vérifier l'adresse\n2- Vérifier le paiement\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "facturation,ecommerce"),
            ("Problème de retour", "Le retour ne fonctionne pas", "Problème de retour",
             "1- Vérifier le produit\n2- Vérifier le délai\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "retour,ecommerce"),
            ("Problème de remboursement", "Le remboursement ne fonctionne pas", "Problème de remboursement",
             "1- Vérifier le paiement\n2- Vérifier le compte\n3- Contacter le support", "Quelle est l'erreur ?",
             "E-commerce", 3, "remboursement,ecommerce"),
            # Hébergement - Apache
            ("Apache ne démarre pas", "Apache ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Hébergement", 4,
             "apache,hebergement"),
            ("Apache lent", "Apache est lent", "Problème de performance",
             "1- Vérifier les logs\n2- Optimiser les paramètres\n3- Augmenter la RAM", "Quelle est l'erreur ?",
             "Hébergement", 3, "apache,lent,hebergement"),
            ("Apache erreur 404", "Apache retourne une erreur 404", "Fichier non trouvé",
             "1- Vérifier le fichier\n2- Vérifier les droits\n3- Vérifier le .htaccess", "Quel est le fichier ?",
             "Hébergement", 3, "apache,404,hebergement"),
            ("Apache erreur 403", "Apache retourne une erreur 403", "Problème de droits",
             "1- Vérifier les droits\n2- Vérifier le .htaccess\n3- Vérifier la configuration", "Quel est le fichier ?",
             "Hébergement", 3, "apache,403,hebergement"),
            ("Apache erreur 500", "Apache retourne une erreur 500", "Erreur interne",
             "1- Vérifier les logs\n2- Vérifier le code\n3- Vérifier la configuration", "Quelle est l'erreur ?",
             "Hébergement", 4, "apache,500,hebergement"),
            ("Apache SSL", "Problème de SSL Apache", "Certificat expiré",
             "1- Vérifier le certificat\n2- Renouveler le certificat\n3- Vérifier la configuration",
             "Quelle est l'erreur ?", "Hébergement", 4, "apache,ssl,hebergement"),
            ("Apache .htaccess", "Problème de .htaccess", "Configuration incorrecte",
             "1- Vérifier le fichier\n2- Vérifier la syntaxe\n3- Redémarrer Apache", "Quelle est l'erreur ?",
             "Hébergement", 3, "apache,htaccess,hebergement"),

            # Hébergement - Nginx
            ("Nginx ne démarre pas", "Nginx ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Hébergement", 4,
             "nginx,hebergement"),
            ("Nginx lent", "Nginx est lent", "Problème de performance",
             "1- Vérifier les logs\n2- Optimiser les paramètres\n3- Augmenter la RAM", "Quelle est l'erreur ?",
             "Hébergement", 3, "nginx,lent,hebergement"),
            ("Nginx erreur 404", "Nginx retourne une erreur 404", "Fichier non trouvé",
             "1- Vérifier le fichier\n2- Vérifier les droits\n3- Vérifier la configuration", "Quel est le fichier ?",
             "Hébergement", 3, "nginx,404,hebergement"),
            ("Nginx erreur 403", "Nginx retourne une erreur 403", "Problème de droits",
             "1- Vérifier les droits\n2- Vérifier la configuration\n3- Vérifier les logs", "Quel est le fichier ?",
             "Hébergement", 3, "nginx,403,hebergement"),
            ("Nginx erreur 500", "Nginx retourne une erreur 500", "Erreur interne",
             "1- Vérifier les logs\n2- Vérifier le code\n3- Vérifier la configuration", "Quelle est l'erreur ?",
             "Hébergement", 4, "nginx,500,hebergement"),
            ("Nginx SSL", "Problème de SSL Nginx", "Certificat expiré",
             "1- Vérifier le certificat\n2- Renouveler le certificat\n3- Vérifier la configuration",
             "Quelle est l'erreur ?", "Hébergement", 4, "nginx,ssl,hebergement"),

            # Hébergement - FTP
            ("FTP ne se connecte pas", "FTP ne se connecte pas", "Problème de connexion",
             "1- Vérifier les identifiants\n2- Vérifier le port\n3- Vérifier le pare-feu", "Quelle est l'erreur ?",
             "Hébergement", 3, "ftp,hebergement"),
            ("FTP transfert échoue", "Le transfert FTP échoue", "Problème de droits",
             "1- Vérifier les droits\n2- Vérifier l'espace\n3- Vérifier le fichier", "Quel est le fichier ?",
             "Hébergement", 3, "ftp,transfert,hebergement"),
            ("FTP lent", "FTP est lent", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier le serveur\n3- Vérifier les paramètres", "Quelle est la vitesse ?",
             "Hébergement", 3, "ftp,lent,hebergement"),
            ("FTP droits", "Problème de droits FTP", "Permissions incorrectes",
             "1- Vérifier les droits\n2- Modifier les droits\n3- Vérifier la configuration", "Quel est le fichier ?",
             "Hébergement", 3, "ftp,droits,hebergement"),
            ("FTP SSL", "Problème de FTP SSL", "Certificat expiré",
             "1- Vérifier le certificat\n2- Renouveler le certificat\n3- Vérifier la configuration",
             "Quelle est l'erreur ?", "Hébergement", 3, "ftp,ssl,hebergement"),
            ("FTP passif", "Problème de FTP passif", "Configuration incorrecte",
             "1- Activer le mode passif\n2- Vérifier le pare-feu\n3- Vérifier la configuration",
             "Quelle est l'erreur ?", "Hébergement", 3, "ftp,passif,hebergement"),
            # Systèmes embarqués - POS
            ("Terminal POS ne démarre pas", "Le terminal de paiement ne démarre pas",
             "Problème d'alimentation ou de système",
             "1- Vérifier l'alimentation\n2- Redémarrer le terminal\n3- Contacter le support",
             "Le terminal est-il allumé ?", "Embarque", 3, "pos,terminal,embarque"),
            ("Terminal POS ne communique pas", "Le terminal ne communique pas avec le serveur", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier le serveur\n3- Contacter le support", "Quelle est l'erreur ?",
             "Embarque", 3, "pos,communication,embarque"),
            ("Terminal POS impression", "L'imprimante du terminal ne fonctionne pas", "Problème d'impression",
             "1- Vérifier le papier\n2- Vérifier la connexion\n3- Contacter le support",
             "L'imprimante est-elle allumée ?", "Embarque", 3, "pos,impression,embarque"),
            ("Terminal POS scan", "Le scanner du terminal ne fonctionne pas", "Problème de scanner",
             "1- Vérifier le scanner\n2- Redémarrer\n3- Contacter le support", "Le scanner est-il reconnu ?",
             "Embarque", 3, "pos,scan,embarque"),
            ("Terminal POS tactile", "L'écran tactile du terminal ne fonctionne pas", "Problème d'écran",
             "1- Nettoyer l'écran\n2- Redémarrer\n3- Contacter le support", "L'écran tactile est-il réactif ?",
             "Embarque", 3, "pos,tactile,embarque"),
            ("Terminal POS commande", "Les commandes ne sont pas prises en compte", "Problème de logiciel",
             "1- Redémarrer le logiciel\n2- Vérifier le serveur\n3- Contacter le support", "Quelle est l'erreur ?",
             "Embarque", 3, "pos,commande,embarque"),
            ("Terminal POS paiement", "Le paiement échoue sur le terminal", "Problème de paiement",
             "1- Vérifier la carte\n2- Vérifier le réseau\n3- Contacter le support", "Quelle est l'erreur ?",
             "Embarque", 3, "pos,paiement,embarque"),

            # Systèmes embarqués - IoT
            ("IoT ne se connecte pas", "L'objet connecté ne se connecte pas", "Problème de WiFi",
             "1- Vérifier le WiFi\n2- Redémarrer l'objet\n3- Réinitialiser", "Le WiFi est-il disponible ?", "Embarque",
             3, "iot,connexion,embarque"),
            ("IoT ne répond pas", "L'objet connecté ne répond plus", "Problème de réseau ou d'alimentation",
             "1- Vérifier l'alimentation\n2- Redémarrer l'objet\n3- Vérifier le réseau", "L'objet est-il allumé ?",
             "Embarque", 3, "iot,repond,embarque"),
            ("IoT perte de signal", "L'objet connecté perd le signal", "Problème de réseau",
             "1- Se rapprocher du routeur\n2- Vérifier le réseau\n3- Ajouter un répéteur", "Le signal est-il faible ?",
             "Embarque", 3, "iot,signal,embarque"),
            ("IoT batterie", "La batterie de l'objet connecté se vide vite", "Problème de batterie",
             "1- Vérifier la batterie\n2- Remplacer la batterie\n3- Réduire l'utilisation", "Quelle est l'autonomie ?",
             "Embarque", 3, "iot,batterie,embarque"),
            ("IoT firmware", "Problème de firmware IoT", "Firmware obsolète",
             "1- Vérifier le firmware\n2- Télécharger le firmware\n3- Mettre à jour", "Quelle est la version ?",
             "Embarque", 3, "iot,firmware,embarque"),
            ("IoT sécurité", "Problème de sécurité IoT", "Objet vulnérable",
             "1- Changer le mot de passe\n2- Mettre à jour le firmware\n3- Contacter le support",
             "Le mot de passe est-il fort ?", "Embarque", 3, "iot,securite,embarque"),
            ("IoT compatibilité", "L'objet connecté n'est pas compatible", "Problème de compatibilité",
             "1- Vérifier la compatibilité\n2- Mettre à jour\n3- Contacter le support", "Quel est l'objet ?",
             "Embarque", 3, "iot,compatibilite,embarque"),

            # Systèmes embarqués - Bornes
            ("Borne interactive ne démarre pas", "La borne interactive ne démarre pas", "Problème d'alimentation",
             "1- Vérifier l'alimentation\n2- Redémarrer la borne\n3- Contacter le support",
             "La borne est-elle allumée ?", "Embarque", 3, "borne,demarrage,embarque"),
            ("Borne interactive écran", "L'écran de la borne ne fonctionne pas", "Problème d'écran",
             "1- Nettoyer l'écran\n2- Redémarrer\n3- Contacter le support", "L'écran est-il allumé ?", "Embarque", 3,
             "borne,ecran,embarque"),
            ("Borne interactive tactile", "L'écran tactile de la borne ne fonctionne pas", "Problème d'écran",
             "1- Nettoyer l'écran\n2- Redémarrer\n3- Contacter le support", "L'écran tactile est-il réactif ?",
             "Embarque", 3, "borne,tactile,embarque"),
            ("Borne interactive réseau", "La borne ne se connecte pas au réseau", "Problème de réseau",
             "1- Vérifier le réseau\n2- Redémarrer la borne\n3- Contacter le support", "Quelle est l'erreur ?",
             "Embarque", 3, "borne,reseau,embarque"),
            ("Borne interactive impression", "L'imprimante de la borne ne fonctionne pas", "Problème d'impression",
             "1- Vérifier le papier\n2- Vérifier la connexion\n3- Contacter le support",
             "L'imprimante est-elle allumée ?", "Embarque", 3, "borne,impression,embarque"),
            ("Borne interactive paiement", "Le paiement échoue sur la borne", "Problème de paiement",
             "1- Vérifier la carte\n2- Vérifier le réseau\n3- Contacter le support", "Quelle est l'erreur ?",
             "Embarque", 3, "borne,paiement,embarque"),
            ("Borne interactive contenu", "Le contenu de la borne ne s'affiche pas", "Problème de contenu",
             "1- Vérifier le contenu\n2- Redémarrer la borne\n3- Contacter le support", "Quel est le contenu ?",
             "Embarque", 3, "borne,contenu,embarque"),
            # Containers - Docker général
            ("Docker daemon ne démarre pas", "Le service Docker ne démarre pas", "Problème de service Docker",
             "1- Vérifier le service systemd\n2- Vérifier les logs\n3- Redémarrer", "Que disent les logs ?",
             "Containers", 4, "docker,daemon,containers"),
            ("Docker images corrompues", "Les images Docker sont corrompues", "Problème de téléchargement",
             "1- Supprimer l'image corrompue\n2- Re-pull l'image\n3- Vérifier le registre", "Quelle est l'image ?",
             "Containers", 4, "docker,image,corrompue,containers"),
            ("Docker container en crash loop", "Le container redémarre en boucle", "Erreur dans l'application",
             "1- Voir les logs du container\n2- Vérifier la configuration\n3- Corriger l'application",
             "Que montrent les logs ?", "Containers", 4, "docker,crashloop,containers"),
            ("Docker container ne démarre pas", "Le container ne démarre pas", "Problème de commande ou de port",
             "1- Vérifier la commande\n2- Vérifier les ports\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Containers", 4, "docker,demarrage,containers"),
            ("Docker port déjà utilisé", "Le port est déjà utilisé", "Conflit de ports",
             "1- Arrêter l'autre container\n2- Changer de port\n3- Libérer le port", "Quel est le port ?", "Containers",
             3, "docker,port,conflit,containers"),
            ("Docker réseau", "Problème de réseau Docker", "Réseau Docker défaillant",
             "1- Vérifier le réseau\n2- Recréer le réseau\n3- Vérifier les logs", "Quel est le réseau ?", "Containers",
             4, "docker,reseau,containers"),
            ("Docker volume", "Problème de volume Docker", "Volume non monté",
             "1- Vérifier le volume\n2- Vérifier le chemin\n3- Recréer le volume", "Quel est le volume ?", "Containers",
             4, "docker,volume,containers"),
            ("Docker disk space", "Espace disque Docker saturé", "Images et containers inutilisés",
             "1- Nettoyer les images inutilisées\n2- Nettoyer les containers\n3- Augmenter l'espace",
             "Quelle est l'utilisation ?", "Containers", 3, "docker,disque,plein,containers"),
            ("Docker registry", "Problème de registry Docker", "Registry inaccessible",
             "1- Vérifier la connexion\n2- Vérifier les identifiants\n3- Vérifier le registry",
             "Quel est le registry ?", "Containers", 4, "docker,registry,containers"),
            ("Docker pull échoue", "Le pull de l'image échoue", "Problème de registry",
             "1- Vérifier le registry\n2- Vérifier les identifiants\n3- Réessayer", "Quelle est l'erreur ?",
             "Containers", 4, "docker,pull,containers"),
            ("Docker push échoue", "Le push de l'image échoue", "Problème de registry",
             "1- Vérifier le registry\n2- Vérifier les identifiants\n3- Réessayer", "Quelle est l'erreur ?",
             "Containers", 4, "docker,push,containers"),
            ("Docker build échoue", "Le build de l'image échoue", "Problème de Dockerfile",
             "1- Vérifier le Dockerfile\n2- Vérifier les dépendances\n3- Corriger le build", "Quelle est l'erreur ?",
             "Containers", 4, "docker,build,containers"),
            ("Docker compose ne démarre pas", "Docker compose ne démarre pas", "Problème de composition",
             "1- Vérifier le docker-compose.yml\n2- Vérifier les services\n3- Recréer les containers",
             "Quelle est l'erreur ?", "Containers", 4, "docker,compose,containers"),

            # Containers - Kubernetes
            ("Kubernetes ne démarre pas", "Kubernetes ne démarre pas", "Problème de cluster",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Containers", 5,
             "kubernetes,demarrage,containers"),
            ("Kubernetes pod en crash loop", "Le pod redémarre en boucle", "Erreur dans le pod",
             "1- Voir les logs du pod\n2- Vérifier la configuration\n3- Corriger le pod", "Que montrent les logs ?",
             "Containers", 5, "kubernetes,crashloop,containers"),
            ("Kubernetes pod ne démarre pas", "Le pod ne démarre pas", "Problème de configuration",
             "1- Vérifier le manifest\n2- Vérifier les logs\n3- Corriger le pod", "Quelle est l'erreur ?", "Containers",
             5, "kubernetes,pod,demarrage,containers"),
            ("Kubernetes service", "Problème de service Kubernetes", "Service inaccessible",
             "1- Vérifier le service\n2- Vérifier les pods\n3- Vérifier les logs", "Quel est le service ?",
             "Containers", 5, "kubernetes,service,containers"),
            ("Kubernetes ingress", "Problème de ingress Kubernetes", "Ingress inaccessible",
             "1- Vérifier le ingress\n2- Vérifier le controller\n3- Vérifier les logs", "Quel est le ingress ?",
             "Containers", 5, "kubernetes,ingress,containers"),
            ("Kubernetes volume", "Problème de volume Kubernetes", "Volume non monté",
             "1- Vérifier le PVC\n2- Vérifier le PV\n3- Vérifier les logs", "Quel est le volume ?", "Containers", 5,
             "kubernetes,volume,containers"),
            ("Kubernetes nodes", "Problème de nodes Kubernetes", "Node non prêt",
             "1- Vérifier le node\n2- Vérifier les logs\n3- Redémarrer le node", "Quel est le node ?", "Containers", 5,
             "kubernetes,nodes,containers"),
            ("Kubernetes secrets", "Problème de secrets Kubernetes", "Secret inaccessible",
             "1- Vérifier le secret\n2- Vérifier les permissions\n3- Recréer le secret", "Quel est le secret ?",
             "Containers", 5, "kubernetes,secrets,containers"),
            ("Kubernetes configmap", "Problème de configmap Kubernetes", "Configmap incorrecte",
             "1- Vérifier le configmap\n2- Vérifier les données\n3- Recréer le configmap", "Quelle est le configmap ?",
             "Containers", 5, "kubernetes,configmap,containers"),
            ("Kubernetes RBAC", "Problème de RBAC Kubernetes", "Permissions insuffisantes",
             "1- Vérifier le RBAC\n2- Vérifier les permissions\n3- Créer les règles", "Quelle est l'erreur ?",
             "Containers", 5, "kubernetes,rbac,containers"),
            # Systèmes de fichiers - NTFS
            ("NTFS corrompu", "Le système de fichiers NTFS est corrompu", "Problème de disque",
             "1- Exécuter chkdsk /f\n2- Vérifier le disque\n3- Réparer le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "ntfs,corrompu,fichiers"),
            ("NTFS plein", "Le disque NTFS est plein", "Espace insuffisant",
             "1- Supprimer des fichiers\n2- Vider la corbeille\n3- Ajouter un disque", "Quelle est la taille ?",
             "Systeme_fichiers", 2, "ntfs,plein,fichiers"),
            ("NTFS permissions", "Problème de permissions NTFS", "Droits incorrects",
             "1- Vérifier les permissions\n2- Modifier les droits\n3- Prendre possession", "Quel est le fichier ?",
             "Systeme_fichiers", 3, "ntfs,permissions,fichiers"),
            ("NTFS compression", "Problème de compression NTFS", "Compression défectueuse",
             "1- Désactiver la compression\n2- Réparer les fichiers\n3- Vérifier le disque", "Quel est le fichier ?",
             "Systeme_fichiers", 3, "ntfs,compression,fichiers"),
            ("NTFS fragmentation", "Le disque NTFS est fragmenté", "Fragmentation élevée",
             "1- Défragmenter le disque\n2- Utiliser l'outil de défragmentation\n3- Nettoyer le disque",
             "Quel est le taux de fragmentation ?", "Systeme_fichiers", 2, "ntfs,fragmentation,fichiers"),
            ("NTFS secteur défectueux", "Secteurs défectueux sur NTFS", "Problème de disque",
             "1- Exécuter chkdsk /r\n2- Remplacer le disque\n3- Sauvegarder les données", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "ntfs,secteur,defectueux,fichiers"),
            ("NTFS boot", "Problème de boot NTFS", "Fichier de boot corrompu",
             "1- Exécuter bootrec /fixmbr\n2- Exécuter bootrec /fixboot\n3- Exécuter bootrec /rebuildbcd",
             "Quelle est l'erreur ?", "Systeme_fichiers", 5, "ntfs,boot,fichiers"),

            # Systèmes de fichiers - FAT32
            ("FAT32 corrompu", "Le système de fichiers FAT32 est corrompu", "Problème de disque",
             "1- Exécuter chkdsk\n2- Vérifier le disque\n3- Réparer le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "fat32,corrompu,fichiers"),
            ("FAT32 plein", "Le disque FAT32 est plein", "Espace insuffisant",
             "1- Supprimer des fichiers\n2- Vider la corbeille\n3- Convertir en NTFS", "Quelle est la taille ?",
             "Systeme_fichiers", 2, "fat32,plein,fichiers"),
            ("FAT32 fichier trop grand", "Fichier trop grand pour FAT32", "Limite de 4GB",
             "1- Convertir en NTFS\n2- Diviser le fichier\n3- Utiliser un autre format",
             "Quelle est la taille du fichier ?", "Systeme_fichiers", 3, "fat32,fichier,grand,fichiers"),
            ("FAT32 incompatible", "FAT32 incompatible avec le système", "Problème de compatibilité",
             "1- Convertir en NTFS\n2- Changer de format\n3- Utiliser un autre disque", "Quel est le système ?",
             "Systeme_fichiers", 3, "fat32,incompatible,fichiers"),

            # Systèmes de fichiers - EXT4
            ("EXT4 corrompu", "Le système de fichiers EXT4 est corrompu", "Problème de disque",
             "1- Exécuter fsck\n2- Vérifier le disque\n3- Réparer le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "ext4,corrompu,fichiers"),
            ("EXT4 plein", "Le disque EXT4 est plein", "Espace insuffisant",
             "1- Supprimer des fichiers\n2- Vider la corbeille\n3- Ajouter un disque", "Quelle est la taille ?",
             "Systeme_fichiers", 2, "ext4,plein,fichiers"),
            ("EXT4 permissions", "Problème de permissions EXT4", "Droits incorrects",
             "1- Vérifier les permissions\n2- Modifier les droits\n3- Utiliser chmod", "Quel est le fichier ?",
             "Systeme_fichiers", 3, "ext4,permissions,fichiers"),
            ("EXT4 journal", "Problème de journal EXT4", "Journal corrompu",
             "1- Désactiver le journal\n2- Réparer le journal\n3- Réinstaller le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "ext4,journal,fichiers"),
            ("EXT4 superblock", "Problème de superblock EXT4", "Superblock corrompu",
             "1- Utiliser un superblock de secours\n2- Réparer le superblock\n3- Réinstaller le système",
             "Quelle est l'erreur ?", "Systeme_fichiers", 5, "ext4,superblock,fichiers"),

            # Systèmes de fichiers - ZFS
            ("ZFS pool", "Problème de pool ZFS", "Pool dégradé",
             "1- Vérifier le pool\n2- Remplacer les disques\n3- Réparer le pool", "Quelle est l'erreur ?",
             "Systeme_fichiers", 5, "zfs,pool,fichiers"),
            ("ZFS dataset", "Problème de dataset ZFS", "Dataset inaccessible",
             "1- Vérifier le dataset\n2- Réparer le dataset\n3- Contacter le support", "Quel est le dataset ?",
             "Systeme_fichiers", 5, "zfs,dataset,fichiers"),
            ("ZFS snapshot", "Problème de snapshot ZFS", "Snapshot corrompu",
             "1- Supprimer le snapshot\n2- Recréer le snapshot\n3- Vérifier le pool", "Quel est le snapshot ?",
             "Systeme_fichiers", 5, "zfs,snapshot,fichiers"),
            ("ZFS replication", "Problème de réplication ZFS", "Réplication échoue",
             "1- Vérifier le réseau\n2- Vérifier les datasets\n3- Réessayer", "Quelle est l'erreur ?",
             "Systeme_fichiers", 5, "zfs,replication,fichiers"),
            ("ZFS espace", "Espace ZFS insuffisant", "Pool plein",
             "1- Supprimer des snapshots\n2- Ajouter des disques\n3- Nettoyer le pool", "Quelle est la taille ?",
             "Systeme_fichiers", 4, "zfs,espace,plein,fichiers"),

            # Systèmes de fichiers - Btrfs
            ("Btrfs corrompu", "Le système de fichiers Btrfs est corrompu", "Problème de disque",
             "1- Exécuter btrfs check\n2- Réparer le système\n3- Contacter le support", "Quelle est l'erreur ?",
             "Systeme_fichiers", 4, "btrfs,corrompu,fichiers"),
            ("Btrfs plein", "Le disque Btrfs est plein", "Espace insuffisant",
             "1- Supprimer des fichiers\n2- Ajouter des disques\n3- Nettoyer le système", "Quelle est la taille ?",
             "Systeme_fichiers", 3, "btrfs,plein,fichiers"),
            ("Btrfs snapshot", "Problème de snapshot Btrfs", "Snapshot corrompu",
             "1- Supprimer le snapshot\n2- Recréer le snapshot\n3- Vérifier le système", "Quel est le snapshot ?",
             "Systeme_fichiers", 4, "btrfs,snapshot,fichiers"),
            ("Btrfs raid", "Problème de RAID Btrfs", "RAID dégradé",
             "1- Vérifier le RAID\n2- Remplacer les disques\n3- Réparer le RAID", "Quelle est l'erreur ?",
             "Systeme_fichiers", 5, "btrfs,raid,fichiers"),
            ("Btrfs compression", "Problème de compression Btrfs", "Compression défectueuse",
             "1- Désactiver la compression\n2- Réparer les fichiers\n3- Vérifier le système", "Quel est le fichier ?",
             "Systeme_fichiers", 3, "btrfs,compression,fichiers"),

            # Systèmes de fichiers - Général
            ("Problème de système de fichiers", "Système de fichiers non reconnu", "Format incompatible",
             "1- Vérifier le format\n2- Changer le format\n3- Utiliser un outil de récupération",
             "Quel est le format ?", "Systeme_fichiers", 3, "systeme-fichiers,format,fichiers"),
            ("Problème de mount", "Le mount échoue", "Problème de mount",
             "1- Vérifier le mount\n2- Vérifier les permissions\n3- Réparer le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 3, "mount,fichiers"),
            ("Problème de fstab", "Le fstab est incorrect", "Configuration incorrecte",
             "1- Vérifier le fstab\n2- Corriger le fstab\n3- Redémarrer le système", "Quelle est l'erreur ?",
             "Systeme_fichiers", 3, "fstab,fichiers"),
            # Virtualisation avancée - Proxmox
            ("Proxmox ne démarre pas", "Le serveur Proxmox ne démarre pas", "Problème de boot ou de disque",
             "1- Vérifier le boot\n2- Vérifier les disques\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 4, "proxmox,demarrage,virtualisation"),
            ("Proxmox VM ne démarre pas", "La VM Proxmox ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             4, "proxmox,vm,demarrage,virtualisation"),
            ("Proxmox VM lente", "La VM Proxmox est lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 4, "proxmox,lent,virtualisation"),
            ("Proxmox cluster", "Problème de cluster Proxmox", "Cluster dégradé",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "proxmox,cluster,virtualisation"),
            ("Proxmox backup", "Problème de backup Proxmox", "Backup échoue",
             "1- Vérifier l'espace\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 4,
             "proxmox,backup,virtualisation"),
            ("Proxmox storage", "Problème de storage Proxmox", "Storage inaccessible",
             "1- Vérifier le storage\n2- Vérifier les logs\n3- Contacter le support", "Quel est le storage ?",
             "Virtualisation", 4, "proxmox,storage,virtualisation"),
            ("Proxmox migration", "Problème de migration Proxmox", "Migration échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "proxmox,migration,virtualisation"),
            ("Proxmox HA", "Problème de HA Proxmox", "Haute disponibilité",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "proxmox,ha,virtualisation"),
            ("Proxmox réseau", "Problème de réseau Proxmox", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le bridge\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 4, "proxmox,reseau,virtualisation"),
            ("Proxmox console", "La console Proxmox ne fonctionne pas", "Problème de console",
             "1- Vérifier la console\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Virtualisation",
             3, "proxmox,console,virtualisation"),

            # Virtualisation avancée - VMware ESXi
            ("ESXi ne démarre pas", "ESXi ne démarre pas", "Problème de boot ou de disque",
             "1- Vérifier le boot\n2- Vérifier les disques\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 4, "esxi,demarrage,virtualisation"),
            ("ESXi VM ne démarre pas", "La VM ESXi ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             4, "esxi,vm,demarrage,virtualisation"),
            ("ESXi VM lente", "La VM ESXi est lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 4, "esxi,lent,virtualisation"),
            ("ESXi cluster", "Problème de cluster ESXi", "Cluster dégradé",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "esxi,cluster,virtualisation"),
            ("ESXi backup", "Problème de backup ESXi", "Backup échoue",
             "1- Vérifier l'espace\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 4,
             "esxi,backup,virtualisation"),
            ("ESXi storage", "Problème de storage ESXi", "Storage inaccessible",
             "1- Vérifier le storage\n2- Vérifier les logs\n3- Contacter le support", "Quel est le storage ?",
             "Virtualisation", 4, "esxi,storage,virtualisation"),
            ("ESXi migration", "Problème de migration ESXi", "Migration échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "esxi,migration,virtualisation"),
            ("ESXi HA", "Problème de HA ESXi", "Haute disponibilité",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "esxi,ha,virtualisation"),
            ("ESXi réseau", "Problème de réseau ESXi", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le switch\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 4, "esxi,reseau,virtualisation"),
            ("ESXi console", "La console ESXi ne fonctionne pas", "Problème de console",
             "1- Vérifier la console\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Virtualisation",
             3, "esxi,console,virtualisation"),

            # Virtualisation avancée - XCP-ng / XenServer
            ("XCP-ng ne démarre pas", "XCP-ng ne démarre pas", "Problème de boot ou de disque",
             "1- Vérifier le boot\n2- Vérifier les disques\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 4, "xcp-ng,demarrage,virtualisation"),
            ("XCP-ng VM ne démarre pas", "La VM XCP-ng ne démarre pas", "Problème de VM",
             "1- Vérifier la VM\n2- Vérifier les logs\n3- Redémarrer la VM", "Quelle est l'erreur ?", "Virtualisation",
             4, "xcp-ng,vm,demarrage,virtualisation"),
            ("XCP-ng VM lente", "La VM XCP-ng est lente", "Problème de performance",
             "1- Augmenter les ressources\n2- Vérifier les logs\n3- Optimiser", "Quelle est la performance ?",
             "Virtualisation", 4, "xcp-ng,lent,virtualisation"),
            ("XCP-ng cluster", "Problème de cluster XCP-ng", "Cluster dégradé",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "xcp-ng,cluster,virtualisation"),
            ("XCP-ng backup", "Problème de backup XCP-ng", "Backup échoue",
             "1- Vérifier l'espace\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 4,
             "xcp-ng,backup,virtualisation"),
            ("XCP-ng storage", "Problème de storage XCP-ng", "Storage inaccessible",
             "1- Vérifier le storage\n2- Vérifier les logs\n3- Contacter le support", "Quel est le storage ?",
             "Virtualisation", 4, "xcp-ng,storage,virtualisation"),
            ("XCP-ng migration", "Problème de migration XCP-ng", "Migration échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "xcp-ng,migration,virtualisation"),
            ("XCP-ng réseau", "Problème de réseau XCP-ng", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le bridge\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 4, "xcp-ng,reseau,virtualisation"),
            ("XCP-ng console", "La console XCP-ng ne fonctionne pas", "Problème de console",
             "1- Vérifier la console\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Virtualisation",
             3, "xcp-ng,console,virtualisation"),

            # Virtualisation avancée - Hyper-V avancé
            ("Hyper-V replication", "Problème de réplication Hyper-V", "Réplication échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "hyper-v,replication,virtualisation"),
            ("Hyper-V cluster", "Problème de cluster Hyper-V", "Cluster dégradé",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "Virtualisation", 5, "hyper-v,cluster,virtualisation"),
            ("Hyper-V failover", "Problème de failover Hyper-V", "Failover échoue",
             "1- Vérifier le cluster\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "hyper-v,failover,virtualisation"),
            ("Hyper-V live migration", "Problème de live migration Hyper-V", "Migration échoue",
             "1- Vérifier le réseau\n2- Vérifier les logs\n3- Réessayer", "Quelle est l'erreur ?", "Virtualisation", 5,
             "hyper-v,live-migration,virtualisation"),
            ("Hyper-V CSV", "Problème de CSV Hyper-V", "CSV inaccessible",
             "1- Vérifier le CSV\n2- Vérifier les logs\n3- Contacter le support", "Quel est le CSV ?", "Virtualisation",
             5, "hyper-v,csv,virtualisation"),
            ("Hyper-V SMB", "Problème de SMB Hyper-V", "SMB inaccessible",
             "1- Vérifier le SMB\n2- Vérifier les logs\n3- Contacter le support", "Quel est le SMB ?", "Virtualisation",
             5, "hyper-v,smb,virtualisation"),
            ("Hyper-V storage", "Problème de storage Hyper-V", "Storage inaccessible",
             "1- Vérifier le storage\n2- Vérifier les logs\n3- Contacter le support", "Quel est le storage ?",
             "Virtualisation", 5, "hyper-v,storage,virtualisation"),
            ("Hyper-V network", "Problème de réseau Hyper-V", "Réseau VM",
             "1- Vérifier le réseau\n2- Vérifier le switch\n3- Vérifier les logs", "Quelle est l'erreur ?",
             "Virtualisation", 4, "hyper-v,reseau,virtualisation"),
            # Monitoring - Nagios
            ("Nagios ne démarre pas", "Nagios ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Monitoring", 4,
             "nagios,demarrage,monitoring"),
            ("Nagios alerte", "Problème d'alerte Nagios", "Alerte non envoyée",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'alerte ?",
             "Monitoring", 4, "nagios,alerte,monitoring"),
            ("Nagios plugin", "Problème de plugin Nagios", "Plugin défectueux",
             "1- Vérifier le plugin\n2- Mettre à jour le plugin\n3- Réinstaller le plugin", "Quel est le plugin ?",
             "Monitoring", 4, "nagios,plugin,monitoring"),
            ("Nagios performance", "Nagios est lent", "Problème de performance",
             "1- Vérifier les logs\n2- Optimiser la configuration\n3- Augmenter les ressources",
             "Quelle est la performance ?", "Monitoring", 4, "nagios,performance,monitoring"),
            ("Nagios configuration", "Problème de configuration Nagios", "Configuration incorrecte",
             "1- Vérifier la configuration\n2- Corriger la configuration\n3- Redémarrer Nagios",
             "Quelle est l'erreur ?", "Monitoring", 4, "nagios,configuration,monitoring"),
            ("Nagios notification", "Problème de notification Nagios", "Notification non reçue",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support",
             "Quelle est la notification ?", "Monitoring", 4, "nagios,notification,monitoring"),

            # Monitoring - Zabbix
            ("Zabbix ne démarre pas", "Zabbix ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Monitoring", 4,
             "zabbix,demarrage,monitoring"),
            ("Zabbix alerte", "Problème d'alerte Zabbix", "Alerte non envoyée",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'alerte ?",
             "Monitoring", 4, "zabbix,alerte,monitoring"),
            ("Zabbix agent", "Problème d'agent Zabbix", "Agent non connecté",
             "1- Vérifier l'agent\n2- Vérifier le réseau\n3- Redémarrer l'agent", "Quel est l'agent ?", "Monitoring", 4,
             "zabbix,agent,monitoring"),
            ("Zabbix proxy", "Problème de proxy Zabbix", "Proxy non connecté",
             "1- Vérifier le proxy\n2- Vérifier le réseau\n3- Redémarrer le proxy", "Quel est le proxy ?", "Monitoring",
             4, "zabbix,proxy,monitoring"),
            ("Zabbix database", "Problème de base Zabbix", "Base corrompue",
             "1- Vérifier la base\n2- Réparer la base\n3- Contacter le support", "Quelle est l'erreur ?", "Monitoring",
             4, "zabbix,database,monitoring"),
            ("Zabbix web", "Problème d'interface Zabbix", "Interface inaccessible",
             "1- Vérifier le service\n2- Vérifier le réseau\n3- Redémarrer", "Quelle est l'erreur ?", "Monitoring", 4,
             "zabbix,web,monitoring"),

            # Monitoring - Prometheus
            ("Prometheus ne démarre pas", "Prometheus ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Monitoring", 4,
             "prometheus,demarrage,monitoring"),
            ("Prometheus alerte", "Problème d'alerte Prometheus", "Alerte non envoyée",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'alerte ?",
             "Monitoring", 4, "prometheus,alerte,monitoring"),
            ("Prometheus metrics", "Problème de métriques Prometheus", "Métriques non collectées",
             "1- Vérifier le target\n2- Vérifier les logs\n3- Redémarrer", "Quel est le target ?", "Monitoring", 4,
             "prometheus,metrics,monitoring"),
            ("Prometheus storage", "Problème de stockage Prometheus", "Stockage plein",
             "1- Vérifier l'espace\n2- Nettoyer le stockage\n3- Augmenter l'espace", "Quelle est la taille ?",
             "Monitoring", 4, "prometheus,storage,monitoring"),
            ("Prometheus configuration", "Problème de configuration Prometheus", "Configuration incorrecte",
             "1- Vérifier la configuration\n2- Corriger la configuration\n3- Redémarrer Prometheus",
             "Quelle est l'erreur ?", "Monitoring", 4, "prometheus,configuration,monitoring"),

            # Monitoring - Grafana
            ("Grafana ne démarre pas", "Grafana ne démarre pas", "Problème de service",
             "1- Vérifier le service\n2- Vérifier les logs\n3- Redémarrer", "Quelle est l'erreur ?", "Monitoring", 4,
             "grafana,demarrage,monitoring"),
            ("Grafana datasource", "Problème de datasource Grafana", "Source non connectée",
             "1- Vérifier la source\n2- Vérifier les identifiants\n3- Redémarrer", "Quelle est la source ?",
             "Monitoring", 4, "grafana,datasource,monitoring"),
            ("Grafana dashboard", "Problème de dashboard Grafana", "Dashboard inaccessible",
             "1- Vérifier le dashboard\n2- Vérifier les logs\n3- Redémarrer", "Quel est le dashboard ?", "Monitoring",
             4, "grafana,dashboard,monitoring"),
            ("Grafana alert", "Problème d'alerte Grafana", "Alerte non envoyée",
             "1- Vérifier la configuration\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'alerte ?",
             "Monitoring", 4, "grafana,alerte,monitoring"),
            ("Grafana plugin", "Problème de plugin Grafana", "Plugin défectueux",
             "1- Vérifier le plugin\n2- Mettre à jour le plugin\n3- Réinstaller le plugin", "Quel est le plugin ?",
             "Monitoring", 4, "grafana,plugin,monitoring"),
            ("Grafana user", "Problème d'utilisateur Grafana", "Utilisateur non authentifié",
             "1- Vérifier les identifiants\n2- Réinitialiser le mot de passe\n3- Contacter le support",
             "Quel est l'utilisateur ?", "Monitoring", 4, "grafana,user,monitoring"),
            # CMS - WordPress
            ("WordPress ne démarre pas", "WordPress ne démarre pas", "Problème de base ou de fichier",
             "1- Vérifier le fichier wp-config.php\n2- Vérifier la base de données\n3- Contacter le support",
             "Quelle est l'erreur ?", "CMS", 3, "wordpress,cms"),
            ("WordPress admin inaccessible", "L'admin WordPress est inaccessible", "Problème de mot de passe",
             "1- Réinitialiser le mot de passe\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "CMS", 3, "wordpress,admin,cms"),
            ("WordPress lent", "WordPress est très lent", "Problème d'hébergement",
             "1- Vérifier le cache\n2- Optimiser les images\n3- Contacter l'hébergeur", "Depuis quand ?", "CMS", 3,
             "wordpress,lent,cms"),
            ("WordPress plugin", "Problème de plugin WordPress", "Plugin défectueux",
             "1- Désactiver le plugin\n2- Mettre à jour le plugin\n3- Supprimer le plugin", "Quel est le plugin ?",
             "CMS", 3, "wordpress,plugin,cms"),
            ("WordPress theme", "Problème de thème WordPress", "Thème défectueux",
             "1- Changer de thème\n2- Mettre à jour le thème\n3- Réinstaller le thème", "Quel est le thème ?", "CMS", 3,
             "wordpress,theme,cms"),
            ("WordPress base corrompue", "La base de données WordPress est corrompue", "Problème de base",
             "1- Réparer la base\n2- Restaurer la base\n3- Contacter le support", "Quelle est l'erreur ?", "CMS", 3,
             "wordpress,database,cms"),
            ("WordPress virus", "Virus détecté sur WordPress", "Site infecté",
             "1- Nettoyer le site\n2- Changer les mots de passe\n3- Contacter le support", "Que détecte-t-il ?", "CMS",
             3, "wordpress,virus,cms"),
            ("WordPress migration", "Problème de migration WordPress", "Migration échoue",
             "1- Vérifier les fichiers\n2- Vérifier la base\n3- Réessayer", "Quelle est l'erreur ?", "CMS", 3,
             "wordpress,migration,cms"),
            ("WordPress erreur 500", "Erreur 500 sur WordPress", "Problème de code",
             "1- Vérifier le .htaccess\n2- Vérifier les fichiers\n3- Contacter le support", "Quelle est l'erreur ?",
             "CMS", 3, "wordpress,500,cms"),

            # CMS - Joomla
            ("Joomla ne démarre pas", "Joomla ne démarre pas", "Problème de base ou de fichier",
             "1- Vérifier le fichier configuration.php\n2- Vérifier la base\n3- Contacter le support",
             "Quelle est l'erreur ?", "CMS", 3, "joomla,cms"),
            ("Joomla admin inaccessible", "L'admin Joomla est inaccessible", "Problème de mot de passe",
             "1- Réinitialiser le mot de passe\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "CMS", 3, "joomla,admin,cms"),
            ("Joomla lent", "Joomla est très lent", "Problème d'hébergement",
             "1- Vérifier le cache\n2- Optimiser les images\n3- Contacter l'hébergeur", "Depuis quand ?", "CMS", 3,
             "joomla,lent,cms"),
            ("Joomla extension", "Problème d'extension Joomla", "Extension défectueuse",
             "1- Désactiver l'extension\n2- Mettre à jour\n3- Supprimer", "Quelle est l'extension ?", "CMS", 3,
             "joomla,extension,cms"),
            ("Joomla template", "Problème de template Joomla", "Template défectueux",
             "1- Changer de template\n2- Mettre à jour\n3- Réinstaller", "Quel est le template ?", "CMS", 3,
             "joomla,template,cms"),
            ("Joomla base corrompue", "La base Joomla est corrompue", "Problème de base",
             "1- Réparer la base\n2- Restaurer\n3- Contacter le support", "Quelle est l'erreur ?", "CMS", 3,
             "joomla,database,cms"),
            ("Joomla virus", "Virus détecté sur Joomla", "Site infecté",
             "1- Nettoyer le site\n2- Changer les mots de passe\n3- Contacter le support", "Que détecte-t-il ?", "CMS",
             3, "joomla,virus,cms"),

            # CMS - Drupal
            ("Drupal ne démarre pas", "Drupal ne démarre pas", "Problème de base ou de fichier",
             "1- Vérifier le settings.php\n2- Vérifier la base\n3- Contacter le support", "Quelle est l'erreur ?",
             "CMS", 3, "drupal,cms"),
            ("Drupal admin inaccessible", "L'admin Drupal est inaccessible", "Problème de mot de passe",
             "1- Réinitialiser le mot de passe\n2- Vérifier les logs\n3- Contacter le support", "Quelle est l'erreur ?",
             "CMS", 3, "drupal,admin,cms"),
            ("Drupal lent", "Drupal est très lent", "Problème d'hébergement",
             "1- Vérifier le cache\n2- Optimiser les images\n3- Contacter l'hébergeur", "Depuis quand ?", "CMS", 3,
             "drupal,lent,cms"),
            ("Drupal module", "Problème de module Drupal", "Module défectueux",
             "1- Désactiver le module\n2- Mettre à jour\n3- Supprimer", "Quel est le module ?", "CMS", 3,
             "drupal,module,cms"),
            ("Drupal theme", "Problème de thème Drupal", "Thème défectueux",
             "1- Changer de thème\n2- Mettre à jour\n3- Réinstaller", "Quel est le thème ?", "CMS", 3,
             "drupal,theme,cms"),
            ("Drupal base corrompue", "La base Drupal est corrompue", "Problème de base",
             "1- Réparer la base\n2- Restaurer\n3- Contacter le support", "Quelle est l'erreur ?", "CMS", 3,
             "drupal,database,cms"),
            ("Drupal update", "Problème de mise à jour Drupal", "Mise à jour échoue",
             "1- Vérifier la version\n2- Télécharger la mise à jour\n3- Réessayer", "Quelle est l'erreur ?", "CMS", 3,
             "drupal,update,cms"),
            # Problèmes divers - Impression
            ("Imprimante hors ligne", "L'imprimante est hors ligne", "Problème de connexion",
             "1- Vérifier le câble\n2- Redémarrer l'imprimante\n3- Réinstaller le pilote",
             "L'imprimante est-elle allumée ?", "Divers", 3, "imprimante,hors-ligne,divers"),
            ("Impression lente", "L'impression est très lente", "Problème de réseau",
             "1- Vérifier le réseau\n2- Vérifier la file d'attente\n3- Redémarrer l'imprimante", "Depuis quand ?",
             "Divers", 3, "impression,lente,divers"),
            ("Impression vide", "L'impression est vide", "Cartouche d'encre vide",
             "1- Vérifier les cartouches\n2- Remplacer les cartouches\n3- Nettoyer les têtes",
             "Les cartouches sont-elles pleines ?", "Divers", 2, "impression,vide,divers"),
            ("Impression rayée", "L'impression est rayée", "Problème de cartouche",
             "1- Nettoyer les têtes\n2- Remplacer les cartouches\n3- Vérifier le papier", "Que montre le test ?",
             "Divers", 2, "impression,rayee,divers"),
            ("Scanner ne fonctionne pas", "Le scanner ne fonctionne pas", "Problème de scanneur",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Contacter le support", "Le scanneur est-il reconnu ?",
             "Divers", 3, "scanner,divers"),

            # Problèmes divers - Périphériques
            ("Clé USB non reconnue", "La clé USB n'est pas reconnue", "Problème de clé USB",
             "1- Tester un autre port\n2- Tester une autre clé\n3- Formater la clé", "La clé est-elle détectée ?",
             "Divers", 2, "usb,cle,divers"),
            ("Disque externe non reconnu", "Le disque externe n'est pas reconnu", "Problème de disque",
             "1- Vérifier le câble\n2- Vérifier le port\n3- Vérifier le pilote", "Le disque est-il détecté ?", "Divers",
             3, "disque,externe,divers"),
            ("Webcam ne fonctionne pas", "La webcam ne fonctionne pas", "Problème de webcam",
             "1- Vérifier le câble\n2- Réinstaller le pilote\n3- Vérifier les permissions",
             "La webcam est-elle reconnue ?", "Divers", 3, "webcam,divers"),
            ("Micro ne fonctionne pas", "Le micro ne fonctionne pas", "Problème de micro",
             "1- Vérifier le câble\n2- Vérifier les permissions\n3- Vérifier les paramètres",
             "Le micro est-il reconnu ?", "Divers", 2, "micro,divers"),
            ("Haut-parleurs ne fonctionnent pas", "Les haut-parleurs ne fonctionnent pas", "Problème audio",
             "1- Vérifier le câble\n2- Vérifier le volume\n3- Vérifier le pilote", "Le son est-il activé ?", "Divers",
             2, "audio,divers"),

            # Problèmes divers - Écrans
            ("Ecran clignote", "L'écran clignote", "Problème de pilote",
             "1- Mettre à jour le pilote\n2- Changer le taux de rafraîchissement\n3- Vérifier le câble",
             "Depuis quand ?", "Divers", 3, "ecran,clignote,divers"),
            ("Ecran noir", "L'écran est noir", "Problème de câble",
             "1- Vérifier le câble\n2- Vérifier l'alimentation\n3- Tester un autre écran", "L'écran s'allume-t-il ?",
             "Divers", 3, "ecran,noir,divers"),
            ("Ecran pixel mort", "Pixel mort sur l'écran", "Problème d'écran",
             "1- Utiliser un outil de réparation\n2- Contacter le support\n3- Remplacer l'écran", "Où est le pixel ?",
             "Divers", 3, "ecran,pixel-mort,divers"),
            ("Ecran décalé", "L'écran est décalé", "Problème de résolution",
             "1- Changer la résolution\n2- Mettre à jour le pilote\n3- Vérifier le câble", "Quelle est la résolution ?",
             "Divers", 3, "ecran,decale,divers"),
            ("Ecran flou", "L'écran est flou", "Problème de câble",
             "1- Vérifier le câble\n2- Changer la résolution\n3- Mettre à jour le pilote",
             "Le câble est-il bien branché ?", "Divers", 3, "ecran,flou,divers"),

            # Problèmes divers - Autres
            ("Problème de sauvegarde", "La sauvegarde échoue", "Problème de sauvegarde",
             "1- Vérifier l'espace\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Divers", 3,
             "sauvegarde,divers"),
            ("Problème de restauration", "La restauration échoue", "Problème de restauration",
             "1- Vérifier les fichiers\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Divers", 3,
             "restauration,divers"),
            ("Problème d'archivage", "L'archivage échoue", "Problème d'archivage",
             "1- Vérifier l'espace\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Divers", 3,
             "archivage,divers"),
            ("Problème de compression", "La compression échoue", "Problème de compression",
             "1- Vérifier l'espace\n2- Vérifier les droits\n3- Réessayer", "Quelle est l'erreur ?", "Divers", 3,
             "compression,divers"),
            ("Problème de décompression", "La décompression échoue", "Problème de décompression",
             "1- Vérifier le fichier\n2- Vérifier les droits\n3- Réessayer", "Quel est le fichier ?", "Divers", 3,
             "decompression,divers"),
            
        ]
        cur.executemany(
            "INSERT INTO pannes (titre, description, diagnostic, procedure, questions, categorie, niveau, tags) VALUES (?,?,?,?,?,?,?,?)",
            donnees
        )
    conn.commit()
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
            self.df = pd.read_sql_query("SELECT * FROM pannes", conn)
            conn.close()

    def rechercher(self, question):
        self.charger()
        question = question.lower()
        mots = re.findall(r"\w+", question)
        resultats = []

        for _, panne in self.df.iterrows():
            score = 0
            champs = f"{panne['titre']} {panne['description']} {panne['tags']} {panne['categorie']}".lower()
            for mot in mots:
                if len(mot) > 1 and mot in champs:
                    score += 5
                if mot in panne['titre'].lower():
                    score += 10
            if score > 0:
                resultats.append((dict(panne), score))

        resultats.sort(key=lambda x: x[1], reverse=True)
        return resultats[:10]

# ===================================================
# FONCTIONS D'EXPORT DES RÉSULTATS
# ==================================================

def generer_pdf_resultats(resultats, question):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import simpleSplit
        from io import BytesIO
    except ImportError:
        st.error("❌ La bibliothèque 'reportlab' n'est pas installée.")
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4
    y = hauteur - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Résultats de recherche - Assistant IT Pro")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Question posée : {question}")
    y -= 20
    c.drawString(50, y, f"{len(resultats)} résultat(s) trouvé(s)")
    y -= 30

    for i, (panne, score) in enumerate(resultats, 1):
        if y < 100:
            c.showPage()
            y = hauteur - 50
            c.setFont("Helvetica", 12)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, f"{i}. {panne['titre']} (Score: {score})")
        y -= 20
        c.setFont("Helvetica", 10)
        texte = f"Catégorie : {panne['categorie']}"
        c.drawString(60, y, texte)
        y -= 15
        texte = f"Diagnostic : {panne['diagnostic']}"
        lignes = simpleSplit(texte, "Helvetica", 10, largeur - 100)
        for ligne in lignes:
            c.drawString(60, y, ligne)
            y -= 15
        texte = f"Procédure : {panne['procedure']}"
        lignes = simpleSplit(texte, "Helvetica", 10, largeur - 100)
        for ligne in lignes:
            c.drawString(60, y, ligne)
            y -= 15
        if panne.get('questions'):
            c.drawString(60, y, f"Questions : {panne['questions']}")
            y -= 15
        y -= 10

    c.save()
    return buffer.getvalue()


def generer_word_resultats(resultats, question):
    try:
        import docx
        from docx.shared import Pt
        from io import BytesIO
    except ImportError:
        st.error("❌ La bibliothèque 'python-docx' n'est pas installée.")
        return None

    doc = docx.Document()
    doc.add_heading("Résultats de recherche - Assistant IT Pro", 0)
    doc.add_paragraph(f"Question posée : {question}")
    doc.add_paragraph(f"{len(resultats)} résultat(s) trouvé(s)")
    doc.add_paragraph()

    for i, (panne, score) in enumerate(resultats, 1):
        doc.add_heading(f"{i}. {panne['titre']} (Score: {score})", level=1)
        p = doc.add_paragraph()
        p.add_run("Catégorie : ").bold = True
        p.add_run(panne['categorie'])
        p = doc.add_paragraph()
        p.add_run("Diagnostic : ").bold = True
        p.add_run(panne['diagnostic'])
        p = doc.add_paragraph()
        p.add_run("Procédure : ").bold = True
        p.add_run(panne['procedure'])
        if panne.get('questions'):
            p = doc.add_paragraph()
            p.add_run("Questions : ").bold = True
            p.add_run(panne['questions'])
        doc.add_paragraph()

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


# ==================================================
# AUTHENTIFICATION
# ==================================================

def inscription(email, password):
    conn = connexion_db()
    cur = conn.cursor()
    try:
        pwd = hashlib.sha256(password.encode()).hexdigest()
        cur.execute(
            "INSERT INTO utilisateurs (email, password, plan, premium, recherches, date_inscription) VALUES (?, ?, 'gratuit', 0, 0, ?)",
            (email, pwd, date.today().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False

def connexion_utilisateur(email, password):
    conn = connexion_db()
    cur = conn.cursor()
    pwd = hashlib.sha256(password.encode()).hexdigest()
    cur.execute("SELECT * FROM utilisateurs WHERE email = ? AND password = ?", (email, pwd))
    user = cur.fetchone()
    conn.close()
    return user

def mise_a_jour_plan(email, plan):
    conn = connexion_db()
    cur = conn.cursor()
    cur.execute("UPDATE utilisateurs SET plan = ?, premium = 1 WHERE email = ?", (plan, email))
    conn.commit()
    conn.close()

# ==================================================
# PAGE VIREMENT BANCAIRE
# ==================================================
def page_virement():
    st.markdown(
        '<p style="color:#FFD700; font-size:36px; font-weight:700; text-align:center;">💳 Paiement par Virement Bancaire</p>',
        unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    <div style='background: linear-gradient(135deg, #1a5276 0%, #2e86c1 100%); padding: 30px; border-radius: 20px; text-align: center; margin-bottom: 30px;'>
        <h2 style='color: white;'>Paiement sécurisé</h2>
        <p style='color: #FFD700;'>Virement bancaire - 0€ de frais</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Choisissez votre offre")

    col1, col2 = st.columns(2)

    with col1:
        with st.container(border=True):
            st.markdown("""
            ### 🚀 PRO
            **9.90€ / mois** | **79€ / an**
            - Recherches illimitées
            - Diagnostics avancés
            - 150+ diagnostics
            - Export PDF
            - Support prioritaire
            - Statistiques avancées
            """)
            if st.button("Choisir Pro - 9.90€", type="primary", use_container_width=True):
                st.session_state.montant_virement = 9.90
                st.session_state.offre_virement = "Pro"
                st.session_state.plan_virement = "pro"
                st.success("✅ Offre Pro sélectionnée !")
                st.balloons()

    with col2:
        with st.container(border=True):
            st.markdown("""
            ### 🏢 BUSINESS
            **29.90€ / mois** | **249€ / an**
            - Tout Pro inclus
            - Diagnostics experts
            - 150+ diagnostics
            - Export PDF/Word
            - Support 24/7
            - Accès API
            - 5 comptes inclus
            """)
            if st.button("Choisir Business - 29.90€", type="primary", use_container_width=True):
                st.session_state.montant_virement = 29.90
                st.session_state.offre_virement = "Business"
                st.session_state.plan_virement = "business"
                st.success("✅ Offre Business sélectionnée !")
                st.balloons()

    if st.session_state.montant_virement > 0:
        st.markdown("---")
        st.markdown("### Effectuez le virement")

        ref = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        st.session_state.ref_virement = ref

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style='background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #2a2a4a;'>
                <h4 style='color: #00d4ff;'>Coordonnées bancaires</h4>
                <p><strong style='color:#aaa;'>Titulaire :</strong> <span style='color:white;'>IT Pro Solutions</span></p>
                <p><strong style='color:#aaa;'>IBAN :</strong> <span style='color:white;'>BE80 9733 8252 3877</span></p>
                <p><strong style='color:#aaa;'>BIC :</strong> <span style='color:white;'>ARSPBE22XXX</span></p>
                <p><strong style='color:#aaa;'>Banque :</strong> <span style='color:white;'>ARGENTA</span></p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style='background: #1a1a2e; padding: 20px; border-radius: 10px; border: 1px solid #2ecc71;'>
                <h4 style='color: #2ecc71;'>Informations importantes</h4>
                <p><strong style='color:#aaa;'>Montant :</strong> <span style='color:#00d4ff;font-weight:700;'>{st.session_state.montant_virement}€</span></p>
                <p><strong style='color:#aaa;'>Offre :</strong> <span style='color:#FFD700;'>{st.session_state.offre_virement}</span></p>
                <p><strong style='color:#aaa;'>Référence :</strong> <code style='background:#0a0a0f;color:#00d4ff;padding:2px 8px;border-radius:4px;'>{ref}</code></p>
                <p><strong style='color:#aaa;'>Email :</strong> <span style='color:white;'>tech.contactinformatique@proton.me</span></p>
                <p style='color: #e74c3c; font-weight:700;'>⚠️ Indiquez la référence dans le libellé</p>
            </div>
            """, unsafe_allow_html=True)

        st.info(f"""
        **📋 Résumé du virement :**
        - Montant : {st.session_state.montant_virement}€
        - Offre : {st.session_state.offre_virement}
        - Référence : {ref}
        - Email : tech.contactinformatique@proton.me
        - Délai : 24-48h ouvrés
        """)
        st.warning(
            "⏳ Après le virement, votre compte sera activé sous 24-48h ouvrés. Un email de confirmation vous sera envoyé.")

# ==================================================
# PAGE OFFRES
# ==================================================
def page_offres():
    st.markdown(
        '<p style="color:#FFD700; font-size:36px; font-weight:700; text-align:center;">📋 Nos Offres</p>',
        unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div style='background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid #2a2a4a; text-align: center;'>
            <h3 style='color: #aaa;'>🆓 Gratuit</h3>
            <p style='font-size: 28px; color: white;'>0€</p>
            <hr>
            <p style='color: #ccc;'>✅ 3 recherches / jour</p>
            <p style='color: #ccc;'>✅ 70+ diagnostics</p>
            <p style='color: #ccc;'>✅ Diagnostics basiques</p>
            <br>
            <span style='background: #2a2a4a; padding: 8px 20px; border-radius: 50px; color: #aaa;'>Actuel</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div style='background: #1a1a2e; padding: 20px; border-radius: 15px; border: 2px solid #FFD700; text-align: center;'>
            <h3 style='color: #FFD700;'>🚀 Pro</h3>
            <p style='font-size: 28px; color: white;'>9.90€<span style='font-size: 16px; color: #aaa;'> /mois</span></p>
            <hr>
            <p style='color: #ccc;'>✅ Recherches illimitées</p>
            <p style='color: #ccc;'>✅ 150+ diagnostics</p>
            <p style='color: #ccc;'>✅ Diagnostics avancés</p>
            <p style='color: #ccc;'>✅ Export PDF</p>
            <p style='color: #ccc;'>✅ Support prioritaire</p>
            <br>
        """, unsafe_allow_html=True)
        if st.button("Choisir Pro", type="primary", key="offre_pro"):
            st.session_state.montant_virement = 9.90
            st.session_state.offre_virement = "Pro"
            st.session_state.plan_virement = "pro"
            st.session_state.page = "💳 Virement"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style='background: #1a1a2e; padding: 20px; border-radius: 15px; border: 2px solid #9B59B6; text-align: center;'>
            <h3 style='color: #9B59B6;'>🏢 Business</h3>
            <p style='font-size: 28px; color: white;'>29.90€<span style='font-size: 16px; color: #aaa;'> /mois</span></p>
            <hr>
            <p style='color: #ccc;'>✅ Tout Pro inclus</p>
            <p style='color: #ccc;'>✅ Diagnostics experts</p>
            <p style='color: #ccc;'>✅ Export PDF/Word</p>
            <p style='color: #ccc;'>✅ Support 24/7</p>
            <p style='color: #ccc;'>✅ Accès API</p>
            <p style='color: #ccc;'>✅ 5 comptes inclus</p>
            <br>
        """, unsafe_allow_html=True)
        if st.button("Choisir Business", type="primary", key="offre_business"):
            st.session_state.montant_virement = 29.90
            st.session_state.offre_virement = "Business"
            st.session_state.plan_virement = "business"
            st.session_state.page = "💳 Virement"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.info("💡 Les offres Pro et Business sont **sans engagement** et peuvent être résiliées à tout moment.")

# ==================================================
# PAGE LICENCE
# ==================================================
def page_licence():
    st.markdown(
        '<p style="color:#FFD700; font-size:36px; font-weight:700; text-align:center;">📄 Licence et Mentions légales</p>',
        unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("""
    ### 📌 Propriété intellectuelle
    - Tous les droits de propriété intellectuelle sur le logiciel **Assistant IT Pro** appartiennent à **IT Pro Solutions**.
    - Toute reproduction, modification ou distribution sans autorisation est interdite.

    ### 🔒 Protection des données
    - Les données utilisateur sont stockées de manière sécurisée et ne sont jamais partagées avec des tiers.
    - Conformément au RGPD, vous pouvez demander la suppression de vos données à tout moment.

    ### 💰 Paiements
    - Les paiements sont traités par virement bancaire. Aucune carte bancaire n'est stockée sur nos serveurs.
    - Les abonnements sont sans engagement et peuvent être résiliés en nous contactant.

    ### 📞 Support
    - Contact : tech.contactinformatique@proton.me
    - Délai de réponse : 24-48h ouvrés

    ---
    *Version 2.0 – 2026*
    """)

# ==================================================
# MAIN
# ==================================================

def main():
    creer_base()
    remplir_base()

    if st.session_state.moteur is None:
        st.session_state.moteur = RechercheIT()

    if st.session_state.date_recherche != date.today():
        st.session_state.date_recherche = date.today()
        st.session_state.recherches_jour = 0

    # ==================================================
    # SIDEBAR
    # ==================================================

    with st.sidebar:
        st.markdown("""
        <style>
            /* Changer le fond de la sidebar */
            section[data-testid="stSidebar"] {
                background-color: #1a1a2e !important;
            }
        </style>
        """, unsafe_allow_html=True)
        st.markdown('<p style="color:#1458; font-size:24px; font-weight:700; text-align:center;">💻 IT Pro</p>',
                    unsafe_allow_html=True)
        st.markdown('<p style="color:#AAAAAA; font-size:12px; text-align:center;">1000 diagnostics</p>',
                    unsafe_allow_html=True)
        st.markdown("---")

        if st.session_state.user:
            st.markdown(f'<p style="color:#FFFFFF;">👤 {st.session_state.user}</p>', unsafe_allow_html=True)

            plan = st.session_state.plan
            if plan == "business":
                st.markdown(
                    '<div style="background:#9B59B6; padding:12px; border-radius:10px; text-align:center;"><p style="color:white; font-weight:700; margin:0;">🏢 BUSINESS</p></div>',
                    unsafe_allow_html=True)
            elif plan == "pro":
                st.markdown(
                    '<div style="background:#FFD700; padding:12px; border-radius:10px; text-align:center;"><p style="color:#0a0a0f; font-weight:700; margin:0;">🚀 PRO</p></div>',
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div style="background:#FF6B6B; padding:12px; border-radius:10px; text-align:center;"><p style="color:white; font-weight:700; margin:0;">🆓 GRATUIT</p></div>',
                    unsafe_allow_html=True)
                restant = max(0, 3 - st.session_state.recherches_jour)
                st.markdown(f'<p style="color:#FFFFFF;">🔍 {restant} recherches restantes</p>', unsafe_allow_html=True)
                st.progress(st.session_state.recherches_jour / 3)

            st.markdown("---")
            menu = ["🏠 Accueil", "📋 Offres", "💳 Virement", "📄 Licence"]
            st.session_state.page = st.radio("Navigation", menu, key="sidebar_menu")

            if st.button("🚪 Déconnexion", use_container_width=True):
                st.session_state.user = None
                st.session_state.premium = False
                st.session_state.plan = "gratuit"
                st.session_state.recherches = 0
                st.session_state.recherches_jour = 0
                st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
            with tab1:
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Mot de passe", type="password", key="login_pass")
                if st.button("Se connecter", use_container_width=True):
                    user = connexion_utilisateur(email, password)
                    if user:
                        st.session_state.user = email
                        st.session_state.plan = user[3] if user[3] else "gratuit"
                        st.session_state.premium = bool(user[4])
                        st.session_state.recherches = user[5] if user[5] else 0
                        st.session_state.recherches_jour = user[5] if user[5] else 0
                        st.success("✅ Connecté !")
                        st.rerun()
                    else:
                        st.error("❌ Identifiants incorrects")
            with tab2:
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Mot de passe", type="password", key="register_pass")
                if st.button("Créer un compte", use_container_width=True):
                    if inscription(email, password):
                        st.success("✅ Compte créé ! Connectez-vous")
                    else:
                        st.error("❌ Email déjà utilisé")

    # ==================================================
    # GESTION DES PAGES
    # ==================================================

    if st.session_state.page == "📋 Offres":
        page_offres()
        return
    if st.session_state.page == "💳 Virement":
        page_virement()
        return
    if st.session_state.page == "📄 Licence":
        page_licence()
        return

    # ==================================================
    # ACCUEIL
    # ==================================================

    st.markdown(
        '<p style="color:#00d4ff; font-size:48px; font-weight:900; text-align:center;">🔧 Assistant Dépannage IT</p>',
        unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#aaa; text-align:center; font-size:18px;">Par IT Pro Solutions - <span style="color:#FFD700;">150+ diagnostics</span></p>',
        unsafe_allow_html=True)
    st.markdown("---")

    question = st.text_area("Décrivez votre problème :", height=100,
                            placeholder="Ex: mon PC est lent, le wifi ne marche pas, erreur Windows...")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Rechercher", type="primary", use_container_width=True):
            if not st.session_state.user:
                st.error("❌ Connectez-vous d'abord")
            elif not st.session_state.premium and st.session_state.recherches_jour >= 3:
                st.error("🔴 LIMITE ATTEINTE ! Passez Premium pour continuer.")
                if st.button("VOIR LES OFFRES"):
                    st.session_state.page = "📋 Offres"
                    st.rerun()
            elif question.strip():
                with st.spinner("Recherche en cours..."):
                    if not st.session_state.premium:
                        st.session_state.recherches_jour += 1
                        st.session_state.recherches += 1
                    results = st.session_state.moteur.rechercher(question)
                    if results:
                        st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                        for panne, score in results:
                            with st.expander(f"🔹 {panne['titre']} (Score: {score})"):
                                st.markdown(f"**Catégorie:** {panne['categorie']}")
                                st.markdown(f"**Diagnostic:** {panne['diagnostic']}")
                                st.markdown(f"**Procédure:**\n{panne['procedure']}")
                                if panne.get('questions'):
                                    st.info(f"❓ {panne['questions']}")


    # ========== BOUTONS D'EXPORT (RÉSERVÉS PRO/BUSINESS) ==========
    if st.session_state.plan in ["pro", "business"]:
        st.markdown("---")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            pdf_data = generer_pdf_resultats(results, question)
            if pdf_data:
                st.download_button(
                    label="📄 Télécharger en PDF",
                    data=pdf_data,
                    file_name=f"resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    key="pdf_download"
                )
            else:
                st.warning("Export PDF indisponible (bibliothèque manquante)")
        with col_btn2:
            word_data = generer_word_resultats(results, question)
            if word_data:
                st.download_button(
                    label="📝 Télécharger en Word",
                    data=word_data,
                    file_name=f"resultats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key="word_download"
                )
            else:
                st.warning("Export Word indisponible (bibliothèque manquante)")
    else:
        st.info("🔒 L'export PDF/Word est disponible uniquement pour les abonnés **Pro** et **Business**.")
else:
    st.warning("😕 Aucun résultat trouvé")
    
#####remplacement de bloc #####
    st.markdown("---")
    st.markdown(
        '<p style="text-align:center; color:#444; font-size:12px;">© 2026 <strong style="color:#FFD700;">IT Pro Solutions</strong> - Tous droits réservés</p>',
        unsafe_allow_html=True)

if __name__ == "__main__":
    main()
