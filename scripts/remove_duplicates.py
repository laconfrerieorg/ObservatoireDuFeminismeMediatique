#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour détecter et supprimer les doublons dans les fichiers de données.
Vérifie les URLs en double dans tous les fichiers CSV.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

# Augmenter la limite de taille de champ CSV
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

def normalize_url(url: str) -> str:
    """Normalise une URL pour la comparaison."""
    if not url:
        return ""
    # Supprimer les fragments et paramètres de tracking
    url = url.split('#')[0].split('?')[0]
    # Supprimer le trailing slash
    if url.endswith('/'):
        url = url[:-1]
    return url.lower().strip()

def remove_duplicates_from_csv(file_path: Path, key_field: str = 'url') -> Dict:
    """Supprime les doublons d'un fichier CSV en gardant la première occurrence."""
    if not file_path.exists():
        return {'removed': 0, 'total': 0, 'kept': 0}
    
    seen_urls: Set[str] = set()
    seen_normalized: Set[str] = set()
    unique_rows: List[Dict] = []
    duplicates: List[Dict] = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        if not fieldnames or key_field not in fieldnames:
            return {'removed': 0, 'total': 0, 'kept': 0, 'error': f'Champ {key_field} non trouvé'}
        
        for row in reader:
            url = row.get(key_field, '')
            normalized = normalize_url(url)
            
            # Vérifier si on a déjà vu cette URL (originale ou normalisée)
            if url in seen_urls or normalized in seen_normalized:
                duplicates.append(row)
                continue
            
            # Ajouter aux sets de tracking
            seen_urls.add(url)
            if normalized:
                seen_normalized.add(normalized)
            
            unique_rows.append(row)
    
    total = len(unique_rows) + len(duplicates)
    removed = len(duplicates)
    
    # Réécrire le fichier si des doublons ont été trouvés
    if removed > 0:
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_rows)
    
    return {
        'removed': removed,
        'total': total,
        'kept': len(unique_rows),
        'duplicates': duplicates[:10]  # Garder les 10 premiers pour affichage
    }

def analyze_duplicates_in_csv(file_path: Path, key_field: str = 'url') -> Dict:
    """Analyse les doublons sans les supprimer."""
    if not file_path.exists():
        return {'duplicates': [], 'count': 0}
    
    url_counts = defaultdict(list)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for idx, row in enumerate(reader):
            url = row.get(key_field, '')
            normalized = normalize_url(url)
            
            if url:
                url_counts[normalized].append({
                    'index': idx + 1,
                    'url': url,
                    'row': row
                })
    
    # Trouver les doublons
    duplicates = []
    for normalized_url, occurrences in url_counts.items():
        if len(occurrences) > 1:
            duplicates.append({
                'url': occurrences[0]['url'],
                'normalized': normalized_url,
                'count': len(occurrences),
                'occurrences': occurrences
            })
    
    return {
        'duplicates': duplicates,
        'count': len(duplicates),
        'total_duplicate_rows': sum(len(d['occurrences']) - 1 for d in duplicates)
    }

def remove_duplicates_from_json(file_path: Path) -> Dict:
    """Supprime les doublons dans le fichier JSON de statistiques."""
    if not file_path.exists():
        return {'removed': 0}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    removed = 0
    
    # Filtrer les doublons dans all_articles_by_media
    if 'all_articles_by_media' in data:
        for media_group in data['all_articles_by_media']:
            articles = media_group.get('articles', [])
            seen_urls = set()
            unique_articles = []
            
            for article in articles:
                url = article.get('url', '')
                normalized = normalize_url(url)
                
                if normalized and normalized not in seen_urls:
                    seen_urls.add(normalized)
                    unique_articles.append(article)
                else:
                    removed += 1
            
            media_group['articles'] = unique_articles
            media_group['n_articles'] = len(unique_articles)
    
    # Filtrer les doublons dans top_militant_articles
    if 'top_militant_articles' in data:
        seen_urls = set()
        unique_top = []
        
        for article in data['top_militant_articles']:
            url = article.get('url', '')
            normalized = normalize_url(url)
            
            if normalized and normalized not in seen_urls:
                seen_urls.add(normalized)
                unique_top.append(article)
            else:
                removed += 1
        
        data['top_militant_articles'] = unique_top
    
    # Sauvegarder si des doublons ont été supprimés
    if removed > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return {'removed': removed}

def main():
    print("🔍 Détection et suppression des doublons")
    print("=" * 60)
    
    total_removed = 0
    
    # 1. Analyser urls_raw.csv
    print("\n📄 Analyse de urls_raw.csv...")
    file_path = DATA_DIR / "urls_raw.csv"
    if file_path.exists():
        analysis = analyze_duplicates_in_csv(file_path, 'url')
        if analysis['count'] > 0:
            print(f"   ⚠️  {analysis['count']} URL(s) en double détectée(s)")
            print(f"   📊 {analysis['total_duplicate_rows']} ligne(s) dupliquée(s) au total")
            
            # Afficher quelques exemples
            for dup in analysis['duplicates'][:5]:
                print(f"      - {dup['url'][:60]}... ({dup['count']} occurrences)")
            
            result = remove_duplicates_from_csv(file_path, 'url')
            total_removed += result['removed']
            print(f"   ✅ {result['removed']} doublon(s) supprimé(s), {result['kept']} ligne(s) conservée(s)")
        else:
            print(f"   ✅ Aucun doublon trouvé")
    else:
        print(f"   ⏭️  Fichier non trouvé")
    
    # 2. Analyser urls_clean.csv
    print("\n📄 Analyse de urls_clean.csv...")
    file_path = DATA_DIR / "urls_clean.csv"
    if file_path.exists():
        analysis = analyze_duplicates_in_csv(file_path, 'url')
        if analysis['count'] > 0:
            print(f"   ⚠️  {analysis['count']} URL(s) en double détectée(s)")
            print(f"   📊 {analysis['total_duplicate_rows']} ligne(s) dupliquée(s) au total")
            
            result = remove_duplicates_from_csv(file_path, 'url')
            total_removed += result['removed']
            print(f"   ✅ {result['removed']} doublon(s) supprimé(s), {result['kept']} ligne(s) conservée(s)")
        else:
            print(f"   ✅ Aucun doublon trouvé")
    else:
        print(f"   ⏭️  Fichier non trouvé")
    
    # 3. Analyser articles_clean.csv
    print("\n📄 Analyse de articles_clean.csv...")
    file_path = DATA_DIR / "articles_clean.csv"
    if file_path.exists():
        analysis = analyze_duplicates_in_csv(file_path, 'url')
        if analysis['count'] > 0:
            print(f"   ⚠️  {analysis['count']} article(s) en double détecté(s)")
            print(f"   📊 {analysis['total_duplicate_rows']} ligne(s) dupliquée(s) au total")
            
            result = remove_duplicates_from_csv(file_path, 'url')
            total_removed += result['removed']
            print(f"   ✅ {result['removed']} doublon(s) supprimé(s), {result['kept']} article(s) conservé(s)")
        else:
            print(f"   ✅ Aucun doublon trouvé")
    else:
        print(f"   ⏭️  Fichier non trouvé")
    
    # 4. Analyser scores.csv
    print("\n📄 Analyse de scores.csv...")
    file_path = DATA_DIR / "scores.csv"
    if file_path.exists():
        analysis = analyze_duplicates_in_csv(file_path, 'url')
        if analysis['count'] > 0:
            print(f"   ⚠️  {analysis['count']} score(s) en double détecté(s)")
            print(f"   📊 {analysis['total_duplicate_rows']} ligne(s) dupliquée(s) au total")
            
            result = remove_duplicates_from_csv(file_path, 'url')
            total_removed += result['removed']
            print(f"   ✅ {result['removed']} doublon(s) supprimé(s), {result['kept']} score(s) conservé(s)")
        else:
            print(f"   ✅ Aucun doublon trouvé")
    else:
        print(f"   ⏭️  Fichier non trouvé")
    
    # 5. Analyser stats_daily.json
    print("\n📄 Analyse de stats_daily.json...")
    file_path = DATA_DIR / "stats_daily.json"
    if file_path.exists():
        result = remove_duplicates_from_json(file_path)
        if result['removed'] > 0:
            total_removed += result['removed']
            print(f"   ✅ {result['removed']} doublon(s) supprimé(s) dans les statistiques")
        else:
            print(f"   ✅ Aucun doublon trouvé")
    else:
        print(f"   ⏭️  Fichier non trouvé")
    
    print("\n" + "=" * 60)
    print(f"✅ Analyse terminée: {total_removed} doublon(s) supprimé(s) au total")
    
    if total_removed > 0:
        print("\n💡 Pour mettre à jour les statistiques après suppression:")
        print("   python scripts/build_stats.py")

if __name__ == "__main__":
    main()

