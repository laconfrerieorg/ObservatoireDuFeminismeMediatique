#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de réinitialisation des données.
Supprime tous les fichiers de données pour repartir de zéro.
"""

import os
import sys
from pathlib import Path
import shutil

sys.path.insert(0, str(Path(__file__).parent.parent))


def reset_data():
    """Réinitialise toutes les données du projet."""
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    # Fichiers CSV à supprimer
    csv_files = [
        "urls_raw.csv",
        "urls_clean.csv",
        "articles_clean.csv",
        "scores.csv",
        "stats_daily.csv",
        "fetch_log.csv"
    ]
    
    # Dossiers à supprimer
    directories = [
        "raw_html"
    ]
    
    print("🔄 Réinitialisation des données...")
    print("=" * 60)
    
    # Supprimer les fichiers CSV
    print("\n📄 Suppression des fichiers CSV...")
    for csv_file in csv_files:
        file_path = data_dir / csv_file
        if file_path.exists():
            file_path.unlink()
            print(f"   ✅ Supprimé: {csv_file}")
        else:
            print(f"   ⏭️  Non trouvé: {csv_file}")
    
    # Supprimer les dossiers
    print("\n📁 Suppression des dossiers...")
    for dir_name in directories:
        dir_path = data_dir / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   ✅ Supprimé: {dir_name}/")
        else:
            print(f"   ⏭️  Non trouvé: {dir_name}/")
    
    # Recréer les dossiers nécessaires
    print("\n📁 Recréation des dossiers...")
    (data_dir / "raw_html").mkdir(exist_ok=True)
    print("   ✅ Dossier raw_html/ créé")
    
    print("\n" + "=" * 60)
    print("✅ Réinitialisation terminée !")
    print("\nVous pouvez maintenant relancer le pipeline complet :")
    print("   1. python scripts/collect_urls.py")
    print("   2. python scripts/fetch_articles.py")
    print("   3. python scripts/parse_articles.py")
    print("   4. python scripts/analyze_articles.py")
    print("   5. python scripts/build_stats.py")


if __name__ == "__main__":
    # Demander confirmation
    print("⚠️  ATTENTION: Cette opération va supprimer TOUTES les données collectées.")
    print("   - URLs collectées")
    print("   - Articles téléchargés")
    print("   - Scores calculés")
    print("   - Statistiques générées")
    print()
    response = input("Êtes-vous sûr de vouloir continuer ? (oui/non): ")
    
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        reset_data()
    else:
        print("❌ Opération annulée.")

