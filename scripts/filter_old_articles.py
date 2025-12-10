#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour supprimer les articles publiés avant 2000 ou après 2025 des données existantes.
"""

import csv
import json
from pathlib import Path
from datetime import datetime
from dateutil import parser as date_parser

# Augmenter la limite de taille de champ CSV
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

MIN_YEAR = 2000
MAX_YEAR = 2025

def is_date_invalid(date_str: str, min_year: int = MIN_YEAR, max_year: int = MAX_YEAR) -> bool:
    """Vérifie si une date est invalide (trop ancienne ou future)."""
    if not date_str:
        return False  # Si pas de date, on garde l'article
    
    try:
        parsed_date = date_parser.parse(date_str, fuzzy=True)
        year = parsed_date.year
        return year < min_year or year > max_year
    except:
        return False  # Si erreur de parsing, on garde l'article

def filter_csv_file(file_path: Path) -> int:
    """Filtre un fichier CSV pour supprimer les articles avant 2000 ou après 2025."""
    if not file_path.exists():
        return 0
    
    rows = []
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            date_pub = row.get('date_pub', '')
            
            if is_date_invalid(date_pub):
                removed_count += 1
                continue
            
            rows.append(row)
    
    # Réécrire le fichier si des articles ont été supprimés
    if removed_count > 0:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            if rows and fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
    
    return removed_count

def filter_json_stats(file_path: Path) -> int:
    """Filtre le fichier JSON de statistiques pour supprimer les articles avant 2000 ou après 2025."""
    if not file_path.exists():
        return 0
    
    removed_count = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filtrer les articles dans all_articles_by_media
    if 'all_articles_by_media' in data:
        for media_group in data['all_articles_by_media']:
            articles = media_group.get('articles', [])
            filtered_articles = []
            
            for article in articles:
                date_pub = article.get('date_pub', '')
                if is_date_invalid(date_pub):
                    removed_count += 1
                    continue
                filtered_articles.append(article)
            
            media_group['articles'] = filtered_articles
            media_group['n_articles'] = len(filtered_articles)
    
    # Filtrer les top articles
    if 'top_militant_articles' in data:
        original_count = len(data['top_militant_articles'])
        data['top_militant_articles'] = [
            article for article in data['top_militant_articles']
            if not is_date_invalid(article.get('date_pub', ''))
        ]
        removed_count += original_count - len(data['top_militant_articles'])
    
    # Sauvegarder si des articles ont été supprimés
    if removed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return removed_count

def main():
    print(f"🔍 Suppression des articles publiés avant {MIN_YEAR} ou après {MAX_YEAR}...")
    print("=" * 60)
    
    total_removed = 0
    
    # 1. Filtrer articles_clean.csv
    print("\n📄 Filtrage de articles_clean.csv...")
    removed = filter_csv_file(DATA_DIR / "articles_clean.csv")
    total_removed += removed
    print(f"   ✅ {removed} article(s) supprimé(s)")
    
    # 2. Filtrer scores.csv
    print("\n📄 Filtrage de scores.csv...")
    removed = filter_csv_file(DATA_DIR / "scores.csv")
    total_removed += removed
    print(f"   ✅ {removed} score(s) supprimé(s)")
    
    # 3. Filtrer stats_daily.json
    print("\n📄 Filtrage de stats_daily.json...")
    removed = filter_json_stats(DATA_DIR / "stats_daily.json")
    total_removed += removed
    print(f"   ✅ {removed} référence(s) supprimée(s)")
    
    print("\n" + "=" * 60)
    print(f"✅ Filtrage terminé: {total_removed} référence(s) supprimée(s)")
    
    if total_removed > 0:
        print("\n💡 Pour mettre à jour les statistiques:")
        print("   python scripts/build_stats.py")

if __name__ == "__main__":
    main()
