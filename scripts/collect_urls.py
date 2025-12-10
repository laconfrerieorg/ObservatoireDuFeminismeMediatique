#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de collecte d'URLs via moteurs de recherche.
Recherche les articles des médias configurés avec les mots-clés définis.
"""

import os
import sys
import csv
import yaml
import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Set
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Augmenter la limite de taille de champ CSV (défaut: 131072)
# Utiliser 50MB au lieu de sys.maxsize pour éviter l'erreur sur Windows
csv.field_size_limit(50 * 1024 * 1024)  # 50MB

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()


class URLCollector:
    """Collecte d'URLs via moteurs de recherche."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        self.medias = self._load_config("medias.yml")
        self.keywords = self._load_config("keywords.yml")
        self.search_config = self._load_config("search_providers.yml")
        
        self.urls_raw_file = self.data_dir / "urls_raw.csv"
        self.urls_clean_file = self.data_dir / "urls_clean.csv"
        
        self.collected_urls: Set[str] = set()
        self.new_urls: List[Dict] = []
        self.skipped_urls: int = 0
        # Verrous pour l'écriture thread-safe
        self.csv_lock = threading.Lock()
        self.urls_lock = threading.Lock()
        self.stats_lock = threading.Lock()
    
    def _load_config(self, filename: str) -> Dict:
        """Charge un fichier de configuration YAML."""
        config_path = self.config_dir / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Fichier de config introuvable: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _normalize_url(self, url: str) -> str:
        """Normalise une URL pour éviter les doublons (supprime fragments, paramètres de tracking, etc.)."""
        try:
            parsed = urlparse(url)
            # Garder seulement scheme, netloc et path (supprimer query et fragment)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # Supprimer le trailing slash pour uniformiser
            if normalized.endswith('/'):
                normalized = normalized[:-1]
            return normalized
        except:
            return url
    
    def _load_existing_urls(self) -> Set[str]:
        """Charge les URLs déjà collectées/traitées pour éviter les doublons."""
        urls = set()
        
        # 1. URLs déjà collectées (urls_raw.csv)
        if self.urls_raw_file.exists():
            with open(self.urls_raw_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row['url']
                    # Normaliser et ajouter les deux versions (originale et normalisée)
                    urls.add(url)
                    urls.add(self._normalize_url(url))
        
        # 2. URLs déjà nettoyées (urls_clean.csv)
        if self.urls_clean_file.exists():
            with open(self.urls_clean_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row['url']
                    urls.add(url)
                    urls.add(self._normalize_url(url))
        
        # 3. Articles déjà parsés (articles_clean.csv)
        articles_file = self.data_dir / "articles_clean.csv"
        if articles_file.exists():
            with open(articles_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url', '')
                    if url:
                        urls.add(url)
                        urls.add(self._normalize_url(url))
        
        # 4. Articles déjà analysés (scores.csv)
        scores_file = self.data_dir / "scores.csv"
        if scores_file.exists():
            with open(scores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url', '')
                    if url:
                        urls.add(url)
                        urls.add(self._normalize_url(url))
        
        return urls
    
    def _search_duckduckgo(self, query: str, max_results: int = 50) -> List[Dict]:
        """
        Recherche via DuckDuckGo (gratuit, pas besoin d'API).
        Note: Cette implémentation est basique. Pour une production,
        utilisez la bibliothèque duckduckgo-search ou SerpAPI.
        """
        results = []
        try:
            # Utilisation de ddgs (nouveau nom du package)
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    try:
                        search_results = ddgs.text(query, max_results=max_results, region='fr-fr')
                        if search_results:
                            for result in search_results:
                                # Vérifier que result est un dictionnaire
                                if isinstance(result, dict):
                                    url = result.get('href', '') or result.get('url', '')
                                    if url:  # Ne garder que les résultats avec une URL valide
                                        results.append({
                                            'url': url,
                                            'title': result.get('title', ''),
                                            'snippet': result.get('body', '') or result.get('snippet', ''),
                                            'date': result.get('date', '')
                                        })
                    except (IndexError, KeyError, AttributeError, TypeError) as e:
                        # Erreur silencieuse pour les recherches qui échouent
                        # (certaines requêtes peuvent ne pas retourner de résultats)
                        pass
                    except Exception as e:
                        # Autres erreurs (timeout, etc.) - on continue quand même
                        pass
            except ImportError:
                print("⚠️  Bibliothèque ddgs non installée.")
                print("   Installez-la avec: pip install ddgs")
                print("   Ou utilisez SerpAPI/Bing API (voir config/search_providers.yml)")
                # Fallback: recherche manuelle via requests (basique)
                pass
        
        except Exception as e:
            # Erreur silencieuse - certaines recherches peuvent échouer
            # sans bloquer tout le processus
            pass
        
        return results
    
    def _search_bing(self, query: str, max_results: int = 50) -> List[Dict]:
        """Recherche via Bing Web Search API."""
        api_key = os.getenv("BING_API_KEY")
        if not api_key:
            print("⚠️  BING_API_KEY non définie dans .env")
            return []
        
        results = []
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": api_key}
        params = {
            "q": query,
            "count": min(max_results, 50),
            "offset": 0,
            "mkt": "fr-FR",
            "safeSearch": "Moderate"
        }
        
        try:
            response = requests.get(endpoint, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("webPages", {}).get("value", []):
                results.append({
                    'url': item.get('url', ''),
                    'title': item.get('name', ''),
                    'snippet': item.get('snippet', ''),
                    'date': item.get('dateLastCrawled', '')
                })
        
        except Exception as e:
            print(f"❌ Erreur lors de la recherche Bing: {e}")
        
        return results
    
    def _search_serpapi(self, query: str, max_results: int = 50) -> List[Dict]:
        """Recherche via SerpAPI."""
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            print("⚠️  SERPAPI_KEY non définie dans .env")
            return []
        
        results = []
        endpoint = "https://serpapi.com/search"
        params = {
            "api_key": api_key,
            "engine": "google",
            "q": query,
            "num": min(max_results, 100),
            "hl": "fr",
            "gl": "fr"
        }
        
        try:
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get("organic_results", []):
                results.append({
                    'url': item.get('link', ''),
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'date': item.get('date', '')
                })
        
        except Exception as e:
            print(f"❌ Erreur lors de la recherche SerpAPI: {e}")
        
        return results
    
    def _search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Lance une recherche selon le provider configuré."""
        provider_config = self.search_config.get("providers", {})
        
        # Essayer dans l'ordre: DuckDuckGo, Bing, SerpAPI
        if provider_config.get("duckduckgo", {}).get("enabled", True):
            results = self._search_duckduckgo(query, max_results)
            if results:
                return results
        
        if provider_config.get("bing", {}).get("enabled", False):
            results = self._search_bing(query, max_results)
            if results:
                return results
        
        if provider_config.get("serpapi", {}).get("enabled", False):
            results = self._search_serpapi(query, max_results)
            if results:
                return results
        
        return []
    
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            return domain
        except:
            return ""
    
    def _is_media_url(self, url: str) -> bool:
        """Vérifie si l'URL appartient à un média configuré."""
        domain = self._extract_domain(url)
        media_domains = {media['domain'] for media in self.medias['medias']}
        return domain in media_domains
    
    def _extract_all_keywords(self, keywords_config):
        """Extrait tous les mots-clés d'une configuration (structure avec catégories)."""
        all_keywords = []
        if isinstance(keywords_config, dict):
            # Nouvelle structure avec catégories et pondérations
            for category_name, category_data in keywords_config.items():
                if isinstance(category_data, dict) and 'keywords' in category_data:
                    all_keywords.extend(category_data['keywords'])
                elif isinstance(category_data, list):
                    # Ancienne structure (liste simple)
                    all_keywords.extend(category_data)
        elif isinstance(keywords_config, list):
            # Structure simple (liste de mots-clés)
            all_keywords.extend(keywords_config)
        return all_keywords
    
    def _process_search_query(self, media: Dict, keyword: str, existing_urls: Set[str], query_num: int, total_queries: int) -> Dict:
        """Traite une requête de recherche de manière thread-safe."""
        domain = media['domain']
        query = f'site:{domain} {keyword}'
        
        result_info = {
            'query': query,
            'query_num': query_num,
            'total_queries': total_queries,
            'new_count': 0,
            'skipped_count': 0,
            'new_urls': []
        }
        
        try:
            results = self._search(query, max_results=50)
            
            for result in results:
                url = result.get('url', '')
                if not url:
                    continue
                
                # Normaliser l'URL pour la comparaison
                normalized_url = self._normalize_url(url)
                
                # Vérifier si l'URL existe déjà (thread-safe)
                with self.urls_lock:
                    if url in existing_urls or normalized_url in existing_urls:
                        result_info['skipped_count'] += 1
                        continue
                    
                    # Vérifier que c'est bien un URL du média
                    if self._is_media_url(url):
                        # Ajouter les deux versions pour éviter les doublons futurs
                        existing_urls.add(url)
                        existing_urls.add(normalized_url)
                
                # Créer la ligne pour le CSV
                row = {
                    'url': url,
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'domain': domain,
                    'keyword': keyword,
                    'date_found': result.get('date', ''),
                    'search_date': datetime.now().isoformat()
                }
                
                # Écrire dans le CSV de manière thread-safe
                with self.csv_lock:
                    # Vérifier si le fichier existe et a un header
                    file_exists = self.urls_raw_file.exists()
                    file_has_header = False
                    if file_exists:
                        try:
                            with open(self.urls_raw_file, 'r', encoding='utf-8') as f:
                                reader = csv.reader(f)
                                first_line = next(reader, None)
                                file_has_header = first_line is not None
                        except:
                            file_has_header = False
                    
                    with open(self.urls_raw_file, 'a', newline='', encoding='utf-8') as f:
                        fieldnames = ['url', 'title', 'snippet', 'domain', 'keyword', 'date_found', 'search_date']
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if not file_exists or not file_has_header:
                            writer.writeheader()
                        writer.writerow(row)
                
                result_info['new_urls'].append(row)
                result_info['new_count'] += 1
            
            # Mettre à jour les statistiques (thread-safe)
            with self.stats_lock:
                self.new_urls.extend(result_info['new_urls'])
                self.skipped_urls += result_info['skipped_count']
        
        except Exception as e:
            result_info['error'] = str(e)
        
        return result_info
    
    def collect_urls(self, max_workers: int = 5):
        """Collecte les URLs pour tous les médias et mots-clés en parallèle."""
        print("🔍 Début de la collecte d'URLs (mode parallèle)...")
        
        # Charger les URLs existantes
        existing_urls = self._load_existing_urls()
        print(f"📊 {len(existing_urls)} URLs déjà collectées")
        
        # Extraire tous les mots-clés féministes uniquement
        feminist_keywords_list = self._extract_all_keywords(
            self.keywords.get("feminist_keywords", {})
        )
        
        # Utiliser uniquement les mots-clés féministes
        all_keywords = feminist_keywords_list
        
        # Initialiser le fichier CSV si nécessaire
        if not self.urls_raw_file.exists():
            with open(self.urls_raw_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['url', 'title', 'snippet', 'domain', 'keyword', 'date_found', 'search_date']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        
        # Créer toutes les tâches de recherche
        tasks = []
        query_num = 0
        
        for media in self.medias['medias']:
            domain = media['domain']
            print(f"\n📰 Média: {media['name']} ({domain})")
            
            for keyword in all_keywords:
                query_num += 1
                tasks.append((media, keyword, query_num))
        
        total_queries = len(tasks)
        print(f"🚀 Lancement de {total_queries} recherches en parallèle (max {max_workers} workers)...\n")
        
        # Exécuter les recherches en parallèle
        completed = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre toutes les tâches
            future_to_task = {
                executor.submit(self._process_search_query, media, keyword, existing_urls, query_num, total_queries): (media, keyword, query_num)
                for media, keyword, query_num in tasks
            }
            
            # Traiter les résultats au fur et à mesure
            for future in as_completed(future_to_task):
                media, keyword, query_num = future_to_task[future]
                completed += 1
                
                try:
                    result_info = future.result()
                    query = result_info['query']
                    new_count = result_info['new_count']
                    skipped_count = result_info['skipped_count']
                    
                    if 'error' in result_info:
                        print(f"  [{completed}/{total_queries}] {query} → Erreur: {result_info['error']}")
                    elif new_count > 0:
                        print(f"  [{completed}/{total_queries}] {query} → {new_count} nouvelle(s) URL(s)")
                    elif skipped_count > 0:
                        print(f"  [{completed}/{total_queries}] {query} → {skipped_count} déjà collectée(s), 0 nouvelle")
                    else:
                        print(f"  [{completed}/{total_queries}] {query} → 0 résultat")
                
                except Exception as e:
                    print(f"  [{completed}/{total_queries}] Erreur lors du traitement: {e}")
                
                # Petite pause pour éviter de surcharger les APIs
                time.sleep(0.5)
        
        print(f"\n✅ Collecte terminée:")
        print(f"   📊 {len(self.new_urls)} nouvelles URLs trouvées")
        print(f"   ⏭️  {self.skipped_urls} URLs ignorées (déjà collectées/traitées)")
        self._deduplicate_urls()
    
    def _deduplicate_urls(self):
        """Crée le fichier urls_clean.csv avec les URLs uniques."""
        if not self.urls_raw_file.exists():
            return
        
        seen_urls = set()
        clean_urls = []
        
        with open(self.urls_raw_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row['url']
                if url not in seen_urls:
                    seen_urls.add(url)
                    clean_urls.append(row)
        
        with open(self.urls_clean_file, 'w', newline='', encoding='utf-8') as f:
            if clean_urls:
                fieldnames = clean_urls[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(clean_urls)
        
        print(f"📝 {len(clean_urls)} URLs uniques dans {self.urls_clean_file}")


def main():
    collector = URLCollector()
    collector.collect_urls()


if __name__ == "__main__":
    main()

