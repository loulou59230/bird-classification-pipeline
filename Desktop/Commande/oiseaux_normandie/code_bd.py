import pandas as pd
import sqlite3
import os
from pathlib import Path

# ==================== CONFIGURATION ====================
DB_NAME = "oiseaux_normandie.db"
IMAGES_FOLDER = "images"

# Données des oiseaux
OISEAUX_DATA = [
    ('Aigrette garzette', 'Egretta garzetta'),
    ('Avocette élégante', 'Recurvirostra avosetta'),
    ('Bergeronnette de Yarrell', 'Motacilla yarrellii'),
    ('Bergeronnette flavéole', 'Motacilla flava'),
    ('Bergeronnette grise', 'Motacilla cinerea'),
    ('Bihoreau gris', 'Nycticorax nycticorax'),
    ('Cormoran huppé', 'Phalacrocorax aristotelis'),
    ('Courlis cendré', 'Numenius arquata'),
    ('Eider à duvet', 'Somateria mollissima'),
    ('Faucon crécerelle', 'Falco tinnunculus'),
    ('Faucon pèlerin', 'Falco peregrinus'),
    ('Fou de Bassan', 'Morus bassanus'),
    ('Fulmar boréal', 'Fulmarus glacialis'),
    ('Goéland argenté', 'Larus argentatus'),
    ('Goéland brun', 'Larus fuscus'),
    ('Goéland leucophée', 'Larus michahellis'),
    ('Goéland marin', 'Larus marinus'),
    ('Grand Cormoran', 'Phalacrocorax carbo'),
    ('Grand Gravelot', 'Charadrius hiaticula'),
    ('Gravelot à collier', 'Charadrius alexandrinus'),
    ('Grèbe à cou noir', 'Podiceps nigricollis'),
    ('Grèbe huppé', 'Podiceps cristatus'),
    ('Guifette moustac', 'Chlidonias hybrida'),
    ('Héron cendré', 'Ardea cinerea'),
    ('Pie bavarde' , 'Pica Pica')
]

# ==================== FONCTIONS ====================

def creer_base_donnees():
    """Crée la base de données et la table oiseaux"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS oiseaux (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_fr TEXT NOT NULL,
        nom_latin TEXT NOT NULL UNIQUE,
        image_path TEXT,
        date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    c.executemany('''
    INSERT OR IGNORE INTO oiseaux (nom_fr, nom_latin)
    VALUES (?, ?)
    ''', OISEAUX_DATA)
    
    conn.commit()
    nb_oiseaux = c.execute("SELECT COUNT(*) FROM oiseaux").fetchone()[0]
    conn.close()
    
    print(f"Base de données créée : {nb_oiseaux} oiseaux")
    return nb_oiseaux


def lister_photos(dossier='.'):
    """Liste toutes les photos JPG disponibles"""
    photos = [f for f in os.listdir(dossier) if f.lower().endswith(('.jpg', '.jpeg'))]
    print(f"\n {len(photos)} photo(s) trouvée(s) dans '{dossier}' :")
    for photo in sorted(photos):
        print(f"   - {photo}")
    return photos


def ajouter_image(nom_latin, nom_fichier):
    """Associe une photo à un oiseau par son nom latin"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Vérifier que le fichier existe
    if not os.path.exists(nom_fichier):
        print(f"Fichier introuvable : {nom_fichier}")
        conn.close()
        return False
    
    # Mettre à jour le chemin de l'image
    c.execute('''
    UPDATE oiseaux 
    SET image_path = ? 
    WHERE nom_latin = ?
    ''', (nom_fichier, nom_latin))
    
    conn.commit()
    success = c.rowcount > 0
    
    if success:
        print(f"Image '{nom_fichier}' associée à {nom_latin}")
    else:
        print(f"Oiseau non trouvé : {nom_latin}")
    
    conn.close()
    return success


def associer_images_auto(dossier='.'):
    """Associe automatiquement les images aux oiseaux selon leur nom"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Récupérer tous les oiseaux
    c.execute("SELECT id, nom_fr, nom_latin FROM oiseaux")
    oiseaux = c.fetchall()
    
    # Lister les photos disponibles
    photos = [f for f in os.listdir(dossier) if f.lower().endswith(('.jpg', '.jpeg'))]
    
    associes = 0
    print("\nAssociation automatique des images :")
    
    for oiseau_id, nom_fr, nom_latin in oiseaux:
        # Créer des variantes du nom pour la recherche
        nom_normalise = nom_fr.lower().replace(' ', '_').replace('é', 'e').replace('è', 'e').replace('ê', 'e')
        nom_espece = nom_latin.split()[1].lower()  # Genre de l'espèce
        
        for photo in photos:
            photo_lower = photo.lower()
            # Chercher correspondance
            if nom_normalise in photo_lower or nom_espece in photo_lower:
                chemin_photo = os.path.join(dossier, photo) if dossier != '.' else photo
                c.execute("UPDATE oiseaux SET image_path = ? WHERE id = ?", (chemin_photo, oiseau_id))
                print(f"   ✓ {nom_fr} ← {photo}")
                associes += 1
                break
    
    conn.commit()
    conn.close()
    print(f"\n✓ {associes} image(s) associée(s) automatiquement")
    return associes


def afficher_etat():
    """Affiche l'état actuel de la base de données"""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT id, nom_fr, nom_latin, image_path FROM oiseaux", conn)
    conn.close()
    
    nb_avec_image = df['image_path'].notna().sum()
    nb_total = len(df)
    
    print(f"\nÉtat de la base de données :")
    print(f"   Total oiseaux : {nb_total}")
    print(f"   Avec image : {nb_avec_image}")
    print(f"   Sans image : {nb_total - nb_avec_image}")
    print("\n" + "="*60)
    print(df.to_string(index=False))
    return df


def supprimer_image(nom_latin):
    """Supprime l'association d'image pour un oiseau"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("UPDATE oiseaux SET image_path = NULL WHERE nom_latin = ?", (nom_latin,))
    conn.commit()
    
    if c.rowcount > 0:
        print(f"Image supprimée pour {nom_latin}")
        success = True
    else:
        print(f"Oiseau non trouvé : {nom_latin}")
        success = False
    
    conn.close()
    return success


# ==================== MENU PRINCIPAL ====================

def menu():
    """Menu interactif pour gérer la base de données"""
    print("\n" + "="*60)
    print(" GESTIONNAIRE BASE DE DONNÉES OISEAUX DE NORMANDIE")
    print("="*60)
    print("1. Créer/initialiser la base de données")
    print("2. Lister les photos disponibles")
    print("3. Associer une image manuellement")
    print("4. Associer les images automatiquement")
    print("5. Afficher l'état de la base")
    print("6. Supprimer une association d'image")
    print("0. Quitter")
    print("="*60)


# ==================== EXÉCUTION ====================

if __name__ == "__main__":
    # Initialisation
    print("Initialisation de la base de données...")
    creer_base_donnees()
    associer_images_auto()
    afficher_etat()