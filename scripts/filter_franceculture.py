#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour supprimer tous les articles de franceculture.fr des données existantes.
"""

import csv
import json
from pathlib import Path
from typing import Set

# Augmenter la limite de taille de champ CSV
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def filter_csv_file(file_path: Path, domain_to_remove: str = "franceculture.fr") -> int:
    """Filtre un fichier CSV pour supprimer les lignes avec le domaine spécifié."""
    if not file_path.exists():
        return 0
    
    # Lire toutes les lignes
    rows = []
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            # Vérifier si le domaine correspond
            domain = row.get('domain', '')
            url = row.get('url', '')
            
            if domain == domain_to_remove or domain_to_remove in url:
                removed_count += 1
                continue
            
            rows.append(row)
    
    # Réécrire le fichier sans les lignes filtrées
    if removed_count > 0:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if rows and fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    
    return removed_count

def filter_json_stats(file_path: Path, domain_to_remove: str = "franceculture.fr") -> int:
    """Filtre le fichier JSON de statistiques pour supprimer les références au domaine."""
    if not file_path.exists():
        return 0
    
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filtrer les médias
    if 'medias' in data:
        original_count = len(data['medias'])
        data['medias'] = [
            media for media in data['medias']
            if media.get('domain', '') != domain_to_remove
        ]
        removed_count += original_count - len(data['medias'])
    
    # Filtrer les articles dans all_articles_by_media
    if 'all_articles_by_media' in data:
        original_count = len(data['all_articles_by_media'])
        data['all_articles_by_media'] = [
            media_group for media_group in data['all_articles_by_media']
            if media_group.get('domain', '') != domain_to_remove
        ]
        removed_count += original_count - len(data['all_articles_by_media'])
    
    # Filtrer les top articles
    if 'top_militant_articles' in data:
        original_count = len(data['top_militant_articles'])
        data['top_militant_articles'] = [
            article for article in data['top_militant_articles']
            if article.get('domain', '') != domain_to_remove
        ]
        removed_count += original_count - len(data['top_militant_articles'])
    
    # Mettre à jour le total d'articles
    if 'total_articles' in data:
        # Recalculer le total en comptant les articles restants
        total = 0
        if 'medias' in data:
            for media in data['medias']:
                total += media.get('n_articles', 0)
        data['total_articles'] = total
    
    # Sauvegarder
    if removed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return removed_count

def get_franceculture_urls() -> Set[str]:
    """Récupère toutes les URLs de franceculture pour les supprimer des fichiers HTML."""
    urls = set()
    
    # Chercher dans urls_clean.csv
    urls_file = DATA_DIR / "urls_clean.csv"
    if urls_file.exists():
        with open(urls_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('domain', '') == 'franceculture.fr' or 'franceculture.fr' in row.get('url', ''):
                    urls.add(row['url'])
    
    # Chercher dans articles_clean.csv
    articles_file = DATA_DIR / "articles_clean.csv"
    if articles_file.exists():
        with open(articles_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('domain', '') == 'franceculture.fr' or 'franceculture.fr' in row.get('url', ''):
                    urls.add(row['url'])
    
    return urls

def main():
    print("🔍 Suppression des articles de franceculture.fr...")
    print("=" * 60)
    
    domain = "franceculture.fr"
    total_removed = 0
    
    # 1. Filtrer urls_raw.csv
    print("\n📄 Filtrage de urls_raw.csv...")
    removed = filter_csv_file(DATA_DIR / "urls_raw.csv", domain)
    total_removed += removed
    print(f"   ✅ {removed} ligne(s) supprimée(s)")
    
    # 2. Filtrer urls_clean.csv
    print("\n📄 Filtrage de urls_clean.csv...")
    removed = filter_csv_file(DATA_DIR / "urls_clean.csv", domain)
    total_removed += removed
    print(f"   ✅ {removed} ligne(s) supprimée(s)")
    
    # 3. Filtrer articles_clean.csv
    print("\n📄 Filtrage de articles_clean.csv...")
    removed = filter_csv_file(DATA_DIR / "articles_clean.csv", domain)
    total_removed += removed
    print(f"   ✅ {removed} ligne(s) supprimée(s)")
    
    # 4. Filtrer scores.csv
    print("\n📄 Filtrage de scores.csv...")
    removed = filter_csv_file(DATA_DIR / "scores.csv", domain)
    total_removed += removed
    print(f"   ✅ {removed} ligne(s) supprimée(s)")
    
    # 5. Filtrer stats_daily.json
    print("\n📄 Filtrage de stats_daily.json...")
    removed = filter_json_stats(DATA_DIR / "stats_daily.json", domain)
    total_removed += removed
    print(f"   ✅ {removed} référence(s) supprimée(s)")
    
    # 6. Note sur les fichiers HTML
    print("\n📁 Fichiers HTML:")
    franceculture_urls = get_franceculture_urls()
    if franceculture_urls:
        print(f"   ⚠️  {len(franceculture_urls)} fichier(s) HTML de franceculture.fr trouvé(s)")
        print(f"   💡 Pour les supprimer complètement, utilisez:")
        print(f"      python scripts/reset_data.py")
        print(f"      (ou supprimez manuellement le dossier data/raw_html/)")
    else:
        print(f"   ✅ Aucun fichier HTML de franceculture.fr trouvé")
    
    print("\n" + "=" * 60)
    print(f"✅ Filtrage terminé: {total_removed} référence(s) supprimée(s)")
    print("\n💡 Pour mettre à jour les statistiques:")
    print("   python scripts/build_stats.py")

if __name__ == "__main__":
    main()

