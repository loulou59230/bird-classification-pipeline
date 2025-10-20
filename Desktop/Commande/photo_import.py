import pandas as pd
import requests
import os
from pathlib import Path
import time

# nom du fichier 
nom_csv = "observations-Bihoreau_gris.csv"
#nom_excel = "observations-aigrette.xlsx"
dossier_destination = "photos_Bihoreau_gris"


try:
    # Créer le dossier de destination s'il n'existe pas
    Path(dossier_destination).mkdir(exist_ok=True)
    
    # Lire le CSV
    df = pd.read_csv(nom_csv, encoding="utf-8-sig")
    
    # Afficher les colonnes disponibles
    print("Colonnes disponibles :")
    print(df.columns.tolist())
    print(f"Nombre de lignes : {len(df)}\n")
    
    # Extraire les URLs
    compteur = 0
    erreurs = 0
    
    for index, row in df.iterrows():
        url = row.get("image_url", "")
        
        if pd.isna(url) or url == "":
            continue
        
        try:
            # Télécharger l'image
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Créer un nom de fichier unique
                nom_fichier = f"{compteur + 1:03d}.jpg"
                chemin_fichier = os.path.join(dossier_destination, nom_fichier)
                
                # Sauvegarder l'image
                with open(chemin_fichier, "wb") as f:
                    f.write(response.content)
                
                compteur += 1
                print(f"✓ {compteur} - Téléchargé : {nom_fichier}")
                
                # Petit délai pour ne pas surcharger le serveur
                time.sleep(0.5)
            else:
                erreurs += 1
                print(f"✗ Erreur {response.status_code} : {url}")
                
        except Exception as e:
            erreurs += 1
            print(f"✗ Erreur téléchargement : {url} - {e}")
    
    print(f"\nRésumé:")
    print(f"Photos téléchargées : {compteur}")
    print(f"Erreurs : {erreurs}")
    print(f"Dossier : {os.path.abspath(dossier_destination)}")
    
except FileNotFoundError:
    print(f"Erreur : Le fichier '{nom_csv}' n'a pas été trouvé.")
except Exception as e:
    print(f"Erreur : {e}")